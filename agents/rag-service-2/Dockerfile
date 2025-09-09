# ---- Builder Stage ----
# Use a full python image that has build tools available for compiling dependencies.
FROM python:3.10 AS builder

# Set environment variables for Poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Copy only the dependency files to leverage Docker's layer caching.
COPY pyproject.toml poetry.lock ./

# Install poetry
RUN pip install poetry

# Install only production dependencies into the virtual environment.
RUN poetry install --no-root --without dev

# ---- Final Stage ----
# Use a slim, production-ready image for the final container.
FROM python:3.10-slim AS final

# Set environment variables to use the virtual environment.
ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create a non-root user for security best practices.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Create a writable directory for caching and temporary files to prevent permission errors.
# Set standard environment variables to direct libraries to use this directory.
RUN mkdir -p /data/huggingface_cache /data/tmp && \
    chown -R appuser:appgroup /data

ENV HF_HOME=/data/huggingface_cache \
    TMPDIR=/data/tmp

# Copy the virtual environment from the builder stage.
COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv

# Copy the application source code and change ownership.
COPY --chown=appuser:appgroup ./app ./app

# Switch to the non-root user for runtime.
USER appuser


# Expose the port your FastAPI application runs on
EXPOSE 8000

# Command to run your application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]