# Multi-stage build: keeps the runtime image small and runs as a non-root user.
#
# Stage 1 ("builder") installs Python dependencies into a user-local prefix
# so only the resulting site-packages -- not pip's build cache or dev tools --
# are copied into the final image.
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: minimal runtime image.
FROM python:3.11-slim

# Dedicated, unprivileged user -- the container never runs as root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY app/ app/

# SQLite database file lives on a mounted volume (see docker-compose.yml),
# owned by the non-root user so it can write to it.
RUN mkdir -p /data && chown -R appuser:appuser /data /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/alerts.db

CMD ["python", "-m", "app.main"]