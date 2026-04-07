# — Stage 1: Builder ————————————————————————————————————————————
# Install Python deps in a separate layer so they are cached independently
# from the application source code.
FROM python:3.10-slim AS builder

# System deps needed to *compile* some wheels (e.g. numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# — Stage 2: Runtime ————————————————————————————————————————————
FROM python:3.10-slim AS runtime

# Runtime system libraries required by OpenCV (even headless) and psutil:
#   libglib2.0-0  → glib (gobject, gio)
#   libgl1        → libGL.so.1  ← THE FIX: missing in the old Dockerfile,
#                                 causes "ImportError: libGL.so.1" at startup
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source
COPY . .

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["python", "server/main.py"]