FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/usr/local/openjdk-17

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/lib/jvm/java-17-openjdk-amd64 /usr/local/openjdk-17

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY docs ./docs

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir ".[gnn]"

COPY . .

CMD ["uvicorn", "neo_ange.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
