FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_HOST=0.0.0.0

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/build

COPY pyproject.toml README.md main.py ./
COPY app ./app
RUN python -m pip install --no-cache-dir .

WORKDIR /app
COPY app/ .
RUN npm install --prefix /app

CMD ["python", "app.py"]
