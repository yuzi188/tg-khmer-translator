FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Force rebuild v2
ENV BUILD_VERSION=2
CMD ["python", "main.py"]
