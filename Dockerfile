FROM node:22-slim AS assets

WORKDIR /app
COPY app/package.json ./
COPY app/scripts ./scripts
RUN npm install --omit=dev --no-audit --no-fund

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_HOST=0.0.0.0

WORKDIR /tmp/build

COPY pyproject.toml README.md main.py ./
COPY app ./app
RUN python -m pip install --no-cache-dir .

WORKDIR /app
COPY app/ .

CMD ["python", "app.py"]

FROM base AS dev

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

FROM base AS runtime

COPY --from=assets /app/static/vendor ./static/vendor
