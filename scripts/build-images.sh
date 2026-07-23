#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <image-tag>"
    exit 1
fi

IMAGE_TAG="$1"
BASE_REPOSITORY="us-central1-docker.pkg.dev/hydroshare-403701/hydroshare"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"
build_image() {
    case "$1" in
        hydroshare)
            docker build --no-cache --platform linux/amd64 -t "${BASE_REPOSITORY}/hydroshare:${IMAGE_TAG}" -f Dockerfile-multistage-node . && \
            docker push "${BASE_REPOSITORY}/hydroshare:${IMAGE_TAG}" &
            ;;
        discover-frontend)
            docker build --no-cache --platform linux/amd64 -t "${BASE_REPOSITORY}/discover-frontend:${IMAGE_TAG}" -f discovery-atlas/frontend/Dockerfile discovery-atlas/frontend/ && \
            docker push "${BASE_REPOSITORY}/discover-frontend:${IMAGE_TAG}" &
            ;;
        hsextract)
            docker build --no-cache --platform linux/amd64 -t "${BASE_REPOSITORY}/hsextract:${IMAGE_TAG}" -f hs_extract/Dockerfile . && \
            docker push "${BASE_REPOSITORY}/hsextract:${IMAGE_TAG}" &
            ;;
        hs-s3-proxy)
            docker build --no-cache --platform linux/amd64 -t "${BASE_REPOSITORY}/hs-s3-proxy:${IMAGE_TAG}" -f hs_s3_proxy/Dockerfile hs_s3_proxy/ && \
            docker push "${BASE_REPOSITORY}/hs-s3-proxy:${IMAGE_TAG}" &
            ;;
        hs-s3-auth)
            docker build --no-cache --platform linux/amd64 -t "${BASE_REPOSITORY}/hs-s3-auth:${IMAGE_TAG}" -f hs_s3_auth/Dockerfile hs_s3_auth/ && \
            docker push "${BASE_REPOSITORY}/hs-s3-auth:${IMAGE_TAG}" &
            ;;
        all)
            build_image hydroshare
            build_image discover-frontend
            build_image hsextract
            build_image hs-s3-proxy
            build_image hs-s3-auth
            ;;
        *)
            echo "Unknown image: $1"
            echo "Valid images: hydroshare discover-frontend hsextract hs-s3-proxy hs-s3-auth all"
            exit 1
            ;;
    esac
}

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <image-tag> <image-name> [image-name ...]"
    echo "Valid images: hydroshare discover-frontend hsextract hs-s3-proxy hs-s3-auth all"
    exit 1
fi

for image in "${@:2}"; do
    build_image "$image"
done
wait
