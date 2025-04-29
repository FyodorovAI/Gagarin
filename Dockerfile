FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY ./src/requirements.txt .

RUN uv venv

RUN uv pip install uvicorn

RUN uv pip install --no-cache-dir -r requirements.txt

RUN uv pip install fyodorov_utils==0.3.17

RUN uv pip install fyodorov_llm_agents==0.4.38

COPY ./src .

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
