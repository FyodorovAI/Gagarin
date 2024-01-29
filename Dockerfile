FROM python:3.11-slim

WORKDIR /app

COPY ./src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
