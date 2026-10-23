#!/bin/bash

set -e

usage() {
    echo "Usage: $0 <env> <image-tag> <image-name> [image-name ...]"
    echo "Valid envs: prod beta"
    echo "Valid images: hydroshare discover-frontend hsextract hs-s3-proxy hs-s3-auth all"
}

if [ "$#" -lt 3 ]; then
    usage
    exit 1
fi

ENV="$1"
IMAGE_TAG="$2"

case "${ENV}" in
    prod)
        BASE_REPOSITORY="us-central1-docker.pkg.dev/hydroshare-403701/hydroshare"
        ;;
    beta)
        BASE_REPOSITORY="us-central1-docker.pkg.dev/hydroshare-sandbox/hydroshare"
        ;;
    *)
        echo "Unknown env: ${ENV}"
        usage
        exit 1
        ;;
esac
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"
build_image() {
    case "$1" in
        hydroshare)
            docker build --platform linux/amd64 -t "${BASE_REPOSITORY}/hydroshare:${IMAGE_TAG}" -f Dockerfile . && \
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

for image in "${@:3}"; do
    build_image "$image"
done
wait
