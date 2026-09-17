# Minimal working placeholder so `docker build` succeeds in CI.
# TODO(gabriel): convert to a multi-stage build with a non-root user and
# only runtime dependencies in the final layer.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

CMD ["python", "-m", "app.main"]
