# ── Dockerfile for the Vektra Python backend ──────────────────────────
# Each line here is a "build step". Docker runs them top to bottom.

# 1) Start FROM a base image that already has Python on it.
#    python:3.12-slim = a small Linux image with Python 3.12 preinstalled.
FROM python:3.12-slim

# 2) ENV sets environment variables inside the container.
#    This one stops Python from buffering its output, so logs appear instantly.
ENV PYTHONUNBUFFERED=1

# 3) WORKDIR makes /app the working directory and creates it.
WORKDIR /app

# 4) COPY the dependency file first and install deps BEFORE copying code.
#    Why? Docker caches each build step. Copying requirements first means the
#    expensive `pip install` step is cached — it only re-runs when the file
#    changes, not on every code change.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5) Now copy the source code in.
COPY server/ /app/server/

# 6) EXPOSE documents which port the app listens on (informational only).
EXPOSE 8000

# 7) CMD runs when the container STARTS (not during build).
#    `server.main:app` = module server.main, object app (we fixed main.py so
#    the app is a module-level object uvicorn can import).
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]