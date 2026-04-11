#!/bin/bash
# NexHost V5 - Startup Script for ClawCloud Run

echo "================================================"
echo "  NexHost V5 - Starting..."
echo "================================================"

# Set working directory
cd /app

# Create necessary directories
mkdir -p /app/data /app/data/uploads /app/logs

# Install dependencies
echo "📦 Installing dependencies..."
pip install flask flask-cors PyJWT bcrypt psutil werkzeug python-dotenv gunicorn --quiet

echo "🚀 Starting gunicorn..."
exec gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  backend.app:app
