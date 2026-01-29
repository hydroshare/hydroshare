#!/bin/bash

# Constants for image repository
DOCKER_REPO="us-central1-docker.pkg.dev/hydroshare-403701/hydroshare/discover-frontend"

# Get the latest commit hash
COMMIT_HASH=$(git rev-parse --short HEAD)

# If the git tree is dirty, append a checksum of the changes
if [[ -n $(git status --porcelain) ]]; then
    DIRTY_HASH=$(git diff | shasum | cut -c1-7)
    COMMIT_HASH="${COMMIT_HASH}-dirty-${DIRTY_HASH}"
fi

echo "Building Docker image with tag: $DOCKER_REPO:$COMMIT_HASH"

# Build Docker image with Caddy
docker build -t $DOCKER_REPO:$COMMIT_HASH ../

# Push to your registry
docker push $DOCKER_REPO:$COMMIT_HASH

echo "Docker image pushed! Tag: $DOCKER_REPO:$COMMIT_HASH"