FROM python:3.11-slim

WORKDIR /app

COPY ./src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --retries 3 --timeout 60 fyodorov_utils==0.3.17

RUN pip install --retries 3 --timeout 60 fyodorov_llm_agents==0.4.37

COPY ./src .

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
