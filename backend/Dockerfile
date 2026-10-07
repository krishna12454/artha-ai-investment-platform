FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; slim image is enough for pure-Python stack
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
