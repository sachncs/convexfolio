FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system convexfolio \
    && useradd --system --gid convexfolio --home /app --shell /bin/bash convexfolio

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY convexfolio ./convexfolio

RUN pip install --no-cache-dir .

RUN mkdir -p /app/artifacts \
    && chown -R convexfolio:convexfolio /app

USER convexfolio

WORKDIR /app

ENTRYPOINT ["convexfolio"]
CMD ["--command", "print-report"]
