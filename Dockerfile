FROM python:3.11-slim

WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start with gunicorn
CMD gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} backend.app:app
