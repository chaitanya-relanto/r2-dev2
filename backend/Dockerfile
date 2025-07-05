# Use the official Python image as a parent image.
# Using -slim to keep the image size down.
FROM python:3.13-slim

# Set environment variables for Python and Pipenv.
# PYTHONUNBUFFERED: Ensures that Python output is sent straight to the terminal.
# PIPENV_VENV_IN_PROJECT: Creates the virtual environment in a .venv folder in the project root.
# PORT: Sets the default port for the application. This can be overridden by --env-file.
ENV PYTHONUNBUFFERED=1 \
    PIPENV_VENV_IN_PROJECT=1 \
    PORT=8000

# Install system-level dependencies required for building Python packages like psycopg.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container.
WORKDIR /app

# Install Pipenv, used for managing project dependencies.
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock to install dependencies before copying the rest of the code.
# This leverages Docker's layer caching for faster subsequent builds.
COPY Pipfile Pipfile.lock ./

# Install project dependencies using pipenv sync. This creates a .venv directory inside /app.
RUN pipenv sync

# Copy the rest of the application's source code.
# The .dockerignore file will prevent copying unnecessary files and directories.
COPY . .

# Expose the port the app runs on.
EXPOSE ${PORT}

# The command to run the application.
# Uses pipenv to run uvicorn within the virtual environment.
# Note: --reload is included for local development. For production, it should be removed.
# The entrypoint is 'main:app' because main.py is in the project root.
# We use sh -c to allow the shell to expand the ${PORT} variable at runtime.
CMD ["/bin/sh", "-c", "pipenv run uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload"] 