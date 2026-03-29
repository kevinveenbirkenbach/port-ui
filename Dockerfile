FROM python:3.12-slim

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
