"""Integration checks for the multi-step workflows in the Astro tutorials."""

import numpy as np

from convexfolio import CFVaR3Numerical, CFVaR3Objective, Minimize, Variance
from convexfolio.backtest import (
    BacktestConfig,
    load_price_history_csv,
    run_backtest,
)
from convexfolio.constraints import (
    long_only_inequalities,
    position_limits_inequalities,
    sector_caps_inequalities,
)
from convexfolio.data import LoadCSV, SyntheticPortfolio


def test_from_csv_tutorial_workflow(tmp_path) -> None:
    portfolio_path = tmp_path / "portfolio.csv"
    portfolio_path.write_text(
        "expected_payoff,cost,precision_diag\n"
        "0.05,0.60,2.0\n"
        "0.10,0.40,1.5\n"
        "-0.02,0.30,1.2\n"
        "0.08,0.80,2.5\n"
        "0.03,0.50,1.8\n",
        encoding="utf-8",
    )

    inputs = LoadCSV(portfolio_path)()
    weights = Minimize(Variance(inputs.precision_matrix), inputs.cost_vector).value

    assert inputs.n_instruments == 5
    assert np.isclose(float(weights @ inputs.cost_vector), 1.0, atol=1e-8)


def test_constraints_tutorial_workflow(tmp_path) -> None:
    portfolio_path = tmp_path / "portfolio.csv"
    portfolio_path.write_text(
        "expected_payoff,cost,precision_diag\n"
        + "\n".join(
            f"{payoff},{cost},{diagonal}"
            for payoff, cost, diagonal in (
                (0.05, 0.60, 2.0),
                (0.10, 0.40, 1.5),
                (-0.02, 0.30, 1.2),
                (0.08, 0.80, 2.5),
                (0.03, 0.50, 1.8),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    inputs = LoadCSV(portfolio_path)()
    sector_map = [0, 0, 1, 1, 2]
    constraints = (
        *long_only_inequalities(inputs.n_instruments),
        *position_limits_inequalities(inputs.n_instruments, max_abs_weight=0.50),
        *sector_caps_inequalities(sector_map, max_per_sector=0.75),
    )
    objective = CFVaR3Objective(
        alpha=0.05,
        expected_payoff=inputs.expected_payoff,
        precision_matrix=inputs.precision_matrix,
        kappa3_callback=lambda weights: 0.0,
    )
    weights = CFVaR3Numerical(
        cost_vector=inputs.cost_vector,
        initial_weights=np.array([0.50, 0.25, 0.50, 0.25, 0.50]),
        objective_callable=objective,
        extra_constraints=constraints,
    ).value

    assert np.all(weights >= -1e-8)
    assert np.all(np.abs(weights) <= 0.50 + 1e-8)
    assert np.isclose(float(weights @ inputs.cost_vector), 1.0, atol=1e-8)


def test_backtesting_tutorial_workflow(tmp_path) -> None:
    prices_path = tmp_path / "prices.csv"
    prices_path.write_text(
        "timestamp,A,B,C,D,E\n"
        "2026-01-01,1.00,1.00,1.00,1.00,1.00\n"
        "2026-01-02,1.05,0.98,1.02,0.95,1.03\n"
        "2026-01-03,1.08,0.96,1.05,0.92,1.06\n"
        "2026-01-04,1.04,1.02,1.08,0.98,1.10\n"
        "2026-01-05,1.10,0.99,1.12,0.95,1.07\n"
        "2026-01-06,1.12,1.01,1.15,0.93,1.09\n"
        "2026-01-07,1.15,1.04,1.18,0.96,1.12\n",
        encoding="utf-8",
    )

    history = load_price_history_csv(prices_path)
    inputs = SyntheticPortfolio(
        n_instruments=history.n_instruments,
        degrees_of_freedom=8.0,
        seed=7,
    )()
    result = run_backtest(
        history,
        BacktestConfig(
            portfolio_inputs=inputs,
            rebalance_frequency=2,
            transaction_cost_bps=5.0,
            alpha=0.05,
        ),
    )

    assert result.portfolio_value.shape == (7,)
    assert np.all(np.isfinite(result.portfolio_value))
    assert result.summary["n_instruments"] == 5
