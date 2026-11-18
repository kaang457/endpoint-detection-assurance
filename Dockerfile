# --- stage 1: build the web UI ---------------------------------------------
# The React console is built here so the image is self-contained; no host npm
# and no checked-in bundle are needed to run it.
FROM node:22-alpine AS webui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Override the dev outDir (which points outside this stage) to a local folder.
RUN npx vite build --outDir dist --emptyOutDir

# --- stage 2: the control plane --------------------------------------------
# Day 14/15 hardening: pinned base, non-root least-privilege user. The digest
# pin (`python@sha256:...`) is the stronger form; the exact tag is pinned here.
FROM python:3.12.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN useradd --create-home --uid 10001 eda
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY --from=webui /ui/dist ./src/eda/webui

USER eda
EXPOSE 8000
CMD ["uvicorn", "eda.controlplane:app", "--host", "0.0.0.0", "--port", "8000"]
