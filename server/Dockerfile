FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    make \
    python3-dev \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin:${PATH}"
ENV UV_PYTHON_PREFERENCE=only-system

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

RUN groupadd --system app && useradd --system --create-home --gid app app \
    && mkdir -p uploads /home/app/.cache/huggingface \
    && chown -R app:app /app /home/app

ENV HOME=/home/app
USER app

EXPOSE 8000

# generous start-period: on a cold container (empty hf-cache volume) the
# embedding + cross-encoder models must fully download before uvicorn even
# binds the port; failures during this window don't count against retries.
# warm restarts (models already cached) become healthy within seconds regardless.
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]