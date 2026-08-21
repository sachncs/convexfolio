# Deployment

How to run Convexfolio on a server so it works automatically — once a
day, on a schedule, or behind a Docker container.

> 📖 **New to servers?** See the
> [Glossary](glossary.md) for terms like `systemd`, `cron`, `Docker`.

---

## What is deployment?

"Deployment" means running Convexfolio on a machine that isn't your
laptop — a server that runs 24/7, runs the package on a schedule,
and saves the reports somewhere you can fetch them.

There are three common ways:

| Style | Best for |
|---|---|
| **systemd service** | Linux servers. Runs once at boot or on demand. |
| **cron job** | Linux servers. Runs on a recurring schedule (e.g., daily). |
| **Docker container** | Any OS. Bundles the package + dependencies into one image. |

If you don't know which to pick, start with **cron** — it's the
simplest.

---

## Before you start

You'll need:

- A Linux server (a VM, a Raspberry Pi, an AWS EC2 instance, etc.).
- Python 3.12 or newer installed.
- Root or sudo access (so you can install packages and write to
  system folders).

A non-root user to run the package as — **don't run things as root**
unless you have a specific reason. Create a dedicated user:

```bash
sudo useradd --system --shell /bin/bash --home /opt/convexfolio convexfolio
```

---

## Option 1 — cron (simplest)

`cron` is Linux's built-in scheduler. You give it a line that says
"run this command at this time, every day/week/etc."

### Step 1 — install the package

```bash
sudo -u convexfolio -H bash -c '
  cd /opt/convexfolio
  git clone https://github.com/sachncs/convexfolio.git .
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
'
```

(`-H` makes sure the user's home directory is used as `~`; `-u`
switches to the `convexfolio` user.)

### Step 2 — write the config

```bash
sudo -u convexfolio mkdir -p /opt/convexfolio/config
sudo tee /opt/convexfolio/config/config.json > /dev/null <<'EOF'
{
  "runtime": {
    "seed": 7,
    "log_level": "INFO",
    "output_directory": "/var/lib/convexfolio/artifacts"
  },
  "optimization": {
    "alpha": 0.05,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
EOF
sudo chown convexfolio:convexfolio /opt/convexfolio/config/config.json
```

### Step 3 — schedule it

Open the crontab for the `convexfolio` user:

```bash
sudo -u convexfolio crontab -e
```

Add a line:

```cron
# Run every day at 2:00 AM
0 2 * * * cd /opt/convexfolio && .venv/bin/convexfolio --config config/config.json --command reproduce-report >> /var/log/convexfolio.log 2>&1
```

Format: `minute hour day-of-month month day-of-week command`. The
above runs daily at 2 AM. Save and exit.

### Step 4 — verify

Check the log:

```bash
tail -n 50 /var/log/convexfolio.log
ls /var/lib/convexfolio/artifacts/
```

You should see `report.json` written after the first run.

---

## Option 2 — systemd (for one-off or boot-time runs)

`systemd` is Linux's built-in service manager. It's how every Linux
daemon runs. ([Glossary: systemd](glossary.md))

### Step 1 — install the package

Same as cron, above.

### Step 2 — write the service file

Create `/etc/systemd/system/convexfolio.service`:

```ini
[Unit]
Description=Convexfolio service
After=network.target

[Service]
Type=oneshot
User=convexfolio
Group=convexfolio
WorkingDirectory=/opt/convexfolio
ExecStart=/opt/convexfolio/.venv/bin/convexfolio \
    --config /opt/convexfolio/config/config.json \
    --command reproduce-report
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Format: standard systemd unit file. ([Glossary: systemd](glossary.md))

### Step 3 — enable and run

```bash
sudo systemctl daemon-reload              # pick up the new file
sudo systemctl start convexfolio          # run it now
sudo systemctl status convexfolio         # check it worked
sudo systemctl enable convexfolio         # (optional) run at boot
```

Logs go to the journal:

```bash
sudo journalctl -u convexfolio -n 50
```

---

## Option 3 — Docker (for portability)

Docker packages Convexfolio + its dependencies into one image that
runs the same on every machine. ([Glossary: Docker](glossary.md))

### Step 1 — write the Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install the package.
COPY pyproject.toml ./
COPY convexfolio ./convexfolio
RUN pip install --no-cache-dir .

# Copy config.
COPY config.json /app/config.json

# Default command.
CMD ["convexfolio", "--config", "/app/config.json", "--command", "reproduce-report"]
```

### Step 2 — build the image

```bash
docker build -t convexfolio:latest .
```

### Step 3 — run the container

```bash
# One-off run, with reports saved to ./artifacts on the host
docker run --rm \
    -v "$(pwd)/artifacts:/app/artifacts" \
    convexfolio:latest
```

For a scheduled Docker run, you'd typically combine this with cron on
the host (yes, you can have cron run `docker run ...`) or use a
container orchestrator like Kubernetes. ([Glossary: Docker](glossary.md))

---

## Output management

Whichever option you pick, the package writes to
`runtime.output_directory`. Default is `artifacts/`. Pick a path
that's:

- On a persistent volume (not in `/tmp` or container scratch space).
- Backed up, if you care about historical reports.
- Writable by the user the package runs as.

A common pattern: timestamp the output directory:

```cron
0 2 * * * cd /opt/convexfolio && \
    mkdir -p "artifacts/$(date +\%Y-\%m-\%d)" && \
    sed -i "s|output_directory.*|output_directory: \"artifacts/$(date +\%Y-\%m-\%d)\"|" config/config.json && \
    .venv/bin/convexfolio --config config/config.json --command reproduce-report
```

(That snippet overwrites the config each day so reports are split
into daily folders. Adapt to your needs.)

---

## Environment variables

The package doesn't read many environment variables directly, but a
few are useful:

| Variable | Effect |
|---|---|
| `OPTIONS_PARALLEL_THRESHOLD` | In `check()`, switch to a process pool when repetitions exceed this. Default `4`. |
| `PYTHONPATH` | Where Python looks for modules. The systemd / cron examples already set this via the venv. |

To set them in systemd, add `Environment=KEY=value` lines under
`[Service]`. To set them in cron, prefix the command:

```cron
0 2 * * * OPTIONS_PARALLEL_THRESHOLD=8 /opt/convexfolio/.venv/bin/convexfolio ...
```

---

## Monitoring

A few questions to ask yourself once it's running:

- **Did the run succeed?** Check the exit code (`0` = success,
  non-zero = failure). Cron logs the exit code in some setups;
  systemd makes it available via `systemctl status`.
- **Where are the reports?** `ls $runtime.output_directory`. They
  should appear after each scheduled run.
- **Is the log file growing?** `ls -la /var/log/convexfolio.log`. If
  it stops growing, the job isn't running.

For serious monitoring, pipe the output to a log-collector (Loki,
Datadog, etc.) — but that's out of scope for this guide.

---

## Troubleshooting

### The cron job runs but produces no output

Check that:

- The cron job's `cd` matches where you actually installed the
  package.
- The user `cron` runs as can read the config and write to the
  output directory.
- The path to the `convexfolio` binary is absolute (cron has a tiny
  `PATH`; don't rely on relative paths).

### The systemd service fails immediately

Check `journalctl -u convexfolio -xe` for the error. Common causes:

- Missing Python module — re-run `pip install -e .` inside the
  venv.
- Wrong working directory in the unit file.
- Permissions on the config or output directory.

### Docker container can't write artifacts

The `-v "$(pwd)/artifacts:/app/artifacts"` mount makes the host
folder available inside the container. If the host folder doesn't
exist, Docker creates it as root, and the container (running as a
non-root user) can't write to it. Fix:

```bash
mkdir -p ./artifacts
chmod 777 ./artifacts    # or chown to match the container's user
```

---

## Where to look next

- **[Glossary](glossary.md)** — Every term used here.
- **[Release process](release.md)** — How to publish a new version
  after fixing things in production.
- **[Architecture](architecture.md)** — How the package is put
  together.
