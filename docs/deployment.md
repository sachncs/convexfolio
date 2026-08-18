# Deployment

## Production Deployment

### Prerequisites

- Python 3.10+
- Virtual environment (recommended)
- Sufficient memory for portfolio computations

### Installation

```bash
# Create virtual environment
python -m venv /opt/options/venv
source /opt/options/venv/bin/activate

# Install package (without dev dependencies)
pip install -e .
```

### Configuration

Create a production configuration file:

```json
{
  "runtime": {
    "seed": 7,
    "log_level": "WARNING",
    "output_dir": "/var/options/artifacts"
  },
  "optimization": {
    "alpha": 0.05,
    "method": "all",
    "enforce_nu_greater_than_six": true
  }
}
```

### Running as a Service

#### Using systemd (Linux)

Create `/etc/systemd/system/options.service`:

```ini
[Unit]
Description=Optimal Option Portfolios Service
After=network.target

[Service]
Type=oneshot
User=oop
Group=oop
WorkingDirectory=/opt/oop
ExecStart=/opt/options/venv/bin/oop --config /etc/options/config.json --command reproduce-report
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable oop
sudo systemctl start oop
```

#### Using cron for Scheduled Runs

```bash
# Run daily at 2 AM
0 2 * * * /opt/options/venv/bin/oop --config /etc/options/config.json --command reproduce-report >> /var/log/oop.log 2>&1
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY config.json .

CMD ["oop", "--config", "config.json", "--command", "reproduce-report"]
```

### Build and Run

```bash
docker build -t oop .
docker run -v $(pwd)/artifacts:/app/artifacts oop
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OOP_SEED` | `7` | Random seed |
| `OOP_LOG_LEVEL` | `INFO` | Logging level |
| `OOP_OUTPUT_DIR` | `artifacts` | Output directory |

## Monitoring

### Logging

Configure logging level via config or environment:

```bash
export OOP_LOG_LEVEL=DEBUG
options --command reproduce-report
```

### Output Monitoring

Monitor the output directory for new reports:

```bash
watch -n 5 ls -la /var/options/artifacts/
```

## Backup

### Output Directory

```bash
# Backup artifacts
tar -czf options-artifacts-$(date +%Y%m%d).tar.gz /var/options/artifacts/
```

### Configuration

```bash
# Backup config
cp /etc/options/config.json /etc/options/config.json.bak.$(date +%Y%m%d)
```

## Scaling

### Horizontal Scaling

- Run multiple instances with different seeds
- Use job queues for parallel processing
- Distribute across multiple machines

### Vertical Scaling

- Increase memory for large portfolios
- Use faster CPUs for numerical optimization
- Consider GPU acceleration for matrix operations

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Memory error | Reduce portfolio size or increase swap |
| Slow optimization | Check matrix conditioning |
| Permission denied | Verify output directory permissions |
| Module not found | Ensure virtual environment is activated |
