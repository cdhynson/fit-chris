FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app
COPY ./Server ./Server

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "80"] 