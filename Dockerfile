FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Upgrade pip and helpers (non-fatal)
RUN pip install --upgrade pip setuptools wheel || true

# Copy project into container (no install by default)
COPY . /app

# Start an interactive shell by default
CMD ["/bin/bash"]
