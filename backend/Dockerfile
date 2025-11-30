## Multi-stage image: build frontend, install backend, run nginx+uvicorn via supervisord

######## Frontend builder ########
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
# Copy package.json and pnpm lock for reproducible installs
COPY frontend/package.json ./
COPY frontend/pnpm-lock.yaml ./
COPY frontend/ ./

## Use npm to install & build frontend (more deterministic in CI without corepack config)
RUN npm ci --silent || npm install --silent

RUN npx vite build

######## Final image ########
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install OS dependencies (nginx + supervisor + build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    nginx \
    supervisor \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated nginx user/group (workers will drop privileges to this user)
RUN groupadd -r nginx || true && useradd -r -g nginx -s /sbin/nologin -d /var/www nginx || true

# Copy nginx and supervisor configs (added below in the repo)
COPY backend/deploy/nginx.conf /etc/nginx/nginx.conf
COPY backend/deploy/supervisord.conf /etc/supervisor/supervisord.conf

# Install Python deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy backend source
COPY backend/ /app/

# Remove any accidentally baked SQLite DB from the source tree so the image
# does not contain a pre-populated DB layer. The entrypoint will create/seed
# the DB at container start if needed.
RUN rm -f /app/gym_app.db || true

# Configure container for development SQLite DB (default)
ENV ENVIRONMENT=development
ENV DATABASE_URL="sqlite+aiosqlite:///./gym_app.db"
ENV RESET_DB_ON_START=true

# Create a non-root 'app' user to run the Python process
RUN groupadd -r app || true && useradd -r -g app -s /usr/sbin/nologin -d /app app || true

# Copy entrypoint which will handle runtime DB seeding and permission fixes
COPY backend/deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy frontend build output into nginx www root
COPY --from=frontend-builder /app/frontend/dist /var/www/frontend


# Ensure frontend dir exists and is owned by the nginx user
RUN mkdir -p /var/www/frontend \
    && chown -R nginx:nginx /var/www/frontend || true

# Ensure app directory permissions
RUN chown -R app:app /app || true

# Ensure logs directory exists for supervisor
RUN mkdir -p /var/log/supervisor

EXPOSE 80

# Entrypoint will perform runtime checks (seed DB if necessary) and exec supervisord
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
