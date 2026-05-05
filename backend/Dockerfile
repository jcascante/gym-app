FROM python:3.13.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install OS dependencies (build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy backend source
COPY . /app/

# Remove any accidentally baked SQLite DB from the source tree
RUN rm -f /app/gym_app.db || true

# Configure container for development SQLite DB (default)
ENV ENVIRONMENT=development
ENV DATABASE_URL="sqlite+aiosqlite:///./gym_app.db"
ENV RESET_DB_ON_START=true

# Create a non-root 'app' user to run the Python process
RUN groupadd -r app || true && useradd -r -g app -s /usr/sbin/nologin -d /app app || true

# Copy entrypoint which will handle runtime DB seeding
COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Ensure app directory permissions
RUN chown -R app:app /app || true

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
