FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY ./src/requirements.txt .

RUN uv pip install --no-cache-dir --system -r requirements.txt

RUN uv pip install --retries 3 --timeout 60 --system fyodorov_utils==0.3.17

RUN uv pip install --retries 3 --timeout 60 --system fyodorov_llm_agents==0.4.38

COPY ./src .

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
