# syntax=docker/dockerfile:1.7

############################
# Builder: compilers + rust
############################
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

# Tools needed to build Rust/Python extensions
RUN apk add --no-cache \
    build-base \
    rust \
    cargo \
    python3-dev \
    libffi-dev \
    openssl-dev \
    musl-dev \
    git

WORKDIR /app

# Keep uv/pip caches small
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy only requirements first for layer caching
COPY ./src/requirements.txt ./requirements.txt

# Build wheels for all deps (musllinux/aarch64) into /wheels
RUN python -m pip wheel --no-cache-dir -r requirements.txt -w /wheels

############################
# Runtime: tiny, wheels only
############################
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS runtime

# Runtime libs some wheels depend on
RUN apk add --no-cache \
    libstdc++ \
    libgcc \
    libffi \
    openssl \
    ca-certificates \
    tzdata
WORKDIR /app

COPY ./src/requirements.txt .

# Install from local wheelhouse only (no compilers in this stage)
COPY --from=builder /wheels /wheels
COPY ./src/requirements.txt ./requirements.txt
RUN uv pip install --system --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
 && rm -rf /wheels
# Install dependencies globally using --system
RUN uv pip install --system fyodorov_utils==0.4.18
RUN uv pip install --system fyodorov_llm_agents==0.5.20

COPY ./src .

EXPOSE 8002

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
