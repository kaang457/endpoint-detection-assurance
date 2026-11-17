# Day 14 hardening: pin the base image. A SHA-256 digest pin is the stronger
# form (`python@sha256:...`); the exact tag is pinned here and the digest is the
# next step once a trusted one is chosen.
FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Day 15 hardening: run as a non-root, least-privilege user.
RUN useradd --create-home --uid 10001 eda
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

USER eda
EXPOSE 8000
CMD ["uvicorn", "eda.controlplane:app", "--host", "0.0.0.0", "--port", "8000"]
