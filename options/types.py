"""Typed data containers for the paper equations."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PortfolioState:
    """State variables in Setting 2.1."""

    option_prices_v: FloatArray
    theta: FloatArray
    delta_matrix_d: FloatArray
    gamma_tensor: FloatArray


@dataclass(frozen=True)
class DistributionParameters:
    """Distributional objects appearing in Section 2 and 4."""

    mu: FloatArray
    sigma: FloatArray
    nu: float
    omega: FloatArray


@dataclass(frozen=True)
class IntermediateMoments:
    """Intermediate vectors/matrices from Eq. (3) expansion.

    Notes:
      This container is retained for compatibility; quantities are now computed
      by modules `moments.py` and `reproduction_math.py`.
    """

    c_scalar: float
    h_vector: FloatArray
    q_vector: FloatArray
    h_matrix: FloatArray
    e_matrix: FloatArray
