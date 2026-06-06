# Stage 1: builder
FROM python:3.13.1-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir poetry poetry-plugin-export

COPY pyproject.toml poetry.lock ./

# create the venv and force-install packaging/requests as a safety net
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install --no-cache-dir packaging requests  # safety net

# stage 2: final
FROM python:3.13.1-slim
WORKDIR /app

# setup user and directories before copying code
RUN useradd -m glitch && \
    mkdir -p /app/logs && \
    chown -R glitch:glitch /app/logs && \
    chown -R glitch:glitch /app/

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 tini && \
    rm -rf /var/lib/apt/lists/*  && \
    apt autoremove -y && \
    apt clean

# copy the virtualenv and the source code
COPY --from=builder /opt/venv /opt/venv
COPY --chown=glitch:glitch ./src ./src

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER glitch

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "src"]
