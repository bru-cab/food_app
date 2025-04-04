FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
flask db upgrade\n\
python -c "from app import db; db.create_all()"\n\
gunicorn --bind 0.0.0.0:8080 app:app' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

# Expose the port the app runs on
EXPOSE 8080

# Run the application with migrations
CMD ["/app/entrypoint.sh"] 