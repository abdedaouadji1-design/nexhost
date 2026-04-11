FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directories
RUN mkdir -p /app/data /app/data/uploads /app/logs

EXPOSE 5000

# gunicorn مع keepalive وإعدادات محسّنة
CMD ["gunicorn", \
     "-w", "1", \
     "-b", "0.0.0.0:5000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "backend.app:app"]
