#!/bin/bash

# This script builds and runs the FastAPI backend Docker container.
# It sets default values, stops any existing container with the same name,
# and passes the environment configuration files to the running container.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
IMAGE_NAME="r2dev2-backend"
CONTAINER_NAME="r2dev2-backend-container"

# Use the PORT from the environment, or default to 8015
# This allows overriding from the command line, e.g., PORT=8016 ./docker-shell.sh
HOST_PORT=${PORT:-8015}

echo "--- Using Configuration ---"
echo "Image Name:      $IMAGE_NAME"
echo "Container Name:  $CONTAINER_NAME"
echo "Host Port:       $HOST_PORT"
echo "--------------------------"

# --- Build Step ---
echo ""
echo "Building the Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .
echo "Build successful."


# --- Run Step ---

# Stop and remove any existing container with the same name to avoid conflicts.
echo ""
echo "Checking for and removing existing container named '$CONTAINER_NAME'..."
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    docker stop $CONTAINER_NAME
    echo "Stopped existing container."
fi
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    docker rm $CONTAINER_NAME
    echo "Removed existing container."
fi

echo ""
echo "Running the new Docker container '$CONTAINER_NAME'..."
echo "Mapping host port $HOST_PORT to the container's port."
echo "Using environment files: configs/.env and configs/secrets/.env"

docker run -d \
    -p "${HOST_PORT}:8000" \
    --env-file configs/.env \
    --env-file configs/secrets/.env \
    --network r2dev2-network \
    --name $CONTAINER_NAME \
    $IMAGE_NAME

echo ""
echo "Container '$CONTAINER_NAME' started successfully in detached mode."
echo "To view logs, run: docker logs -f $CONTAINER_NAME"
echo "To stop the container, run: docker stop $CONTAINER_NAME" 