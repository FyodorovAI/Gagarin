FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY ./src/requirements.txt .

# Install dependencies globally using --system
RUN uv pip install --system uvicorn \
    && uv pip install --system --no-cache-dir -r requirements.txt
RUN uv pip install --system fyodorov_utils==0.3.29
RUN uv pip install --system fyodorov_llm_agents==0.4.81

COPY ./src .

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
