#!/usr/bin/env bash
set -euo pipefail

# Mirrors every source bucket under PROD_ALIAS into a single target bucket under GCS_ALIAS.
# This reproduces the behavior seen in scripts/nohup.out where:
#   prod-minio/<user_bucket>/<resource_path> -> gcs/<target_bucket>/<resource_path>
#
# Required environment variables:
#   PROD_ALIAS        Example: prod-minio
#   GCS_ALIAS         Example: gcs
#   GCS_BUCKET        Example: hydroshare-beta-resources
#
# Optional environment variables:
#   DRY_RUN           true|false (default: true)
#   OVERWRITE         true|false (default: true)
#   REMOVE            true|false (default: false)
#   INCLUDE_REGEX     Regex bucket allowlist (default: .*)
#   EXCLUDE_REGEX     Regex bucket denylist (default: ^$)
#
# Notes:
# - Buckets are discovered via `mc ls <PROD_ALIAS>`.
# - Bucket names ending with '/' are normalized.

# 3 runs with parameters for running the data sync (remove dry-run to actually perform the migration). Note you must have the aliases set up in your mc config for prod-minio, gcs and gcs-ciroh, and the target bucket must already exist in GCS.:

# all non-published and non-ciroh-data buckets, dry-run:
# DRY_RUN=true EXCLUDE_REGEX='^(published|ciroh-data)$' PROD_ALIAS=prod-minio GCS_ALIAS=gcs GCS_BUCKET=hydroshare-resources ./mirror-prod-minio-users-to-gcs.sh

# published bucket only, dry-run:
# DRY_RUN=true INCLUDE_REGEX='^published$' PROD_ALIAS=prod-minio GCS_ALIAS=gcs GCS_BUCKET=hydroshare-published-resources ./mirror-prod-minio-users-to-gcs.sh

# ciroh-data bucket only, dry-run:
# DRY_RUN=true INCLUDE_REGEX='^ciroh-data$' PROD_ALIAS=prod-minio GCS_ALIAS=gcs-ciroh GCS_BUCKET=ciroh-hydroshare-data ./mirror-prod-minio-users-to-gcs.sh


PROD_ALIAS="${PROD_ALIAS:-}"
GCS_ALIAS="${GCS_ALIAS:-}"
GCS_BUCKET="${GCS_BUCKET:-}"
DRY_RUN="${DRY_RUN:-true}"
OVERWRITE="${OVERWRITE:-true}"
REMOVE="${REMOVE:-false}"
INCLUDE_REGEX="${INCLUDE_REGEX:-.*}"
EXCLUDE_REGEX="${EXCLUDE_REGEX:-^$}"

if [[ -z "$PROD_ALIAS" || -z "$GCS_ALIAS" || -z "$GCS_BUCKET" ]]; then
  echo "ERROR: PROD_ALIAS, GCS_ALIAS, and GCS_BUCKET are required."
  exit 1
fi

if ! command -v mc >/dev/null 2>&1; then
  echo "ERROR: mc (MinIO client) is not installed or not on PATH."
  exit 1
fi

# Ensure destination bucket exists.
if ! mc ls "${GCS_ALIAS}/${GCS_BUCKET}" >/dev/null 2>&1; then
  echo "ERROR: Destination bucket ${GCS_ALIAS}/${GCS_BUCKET} does not exist."
  echo "Create it first, then rerun this script."
  exit 1
fi

# Build mirror flags.
mirror_flags=()
if [[ "$DRY_RUN" == "true" ]]; then
  mirror_flags+=(--dry-run)
fi
if [[ "$OVERWRITE" == "true" ]]; then
  mirror_flags+=(--overwrite)
fi
if [[ "$REMOVE" == "true" ]]; then
  mirror_flags+=(--remove)
fi

# Discover source buckets.
source_buckets=()
while IFS= read -r bucket_name; do
  [[ -n "$bucket_name" ]] && source_buckets+=("$bucket_name")
done < <(mc ls "${PROD_ALIAS}" | awk '{print $NF}' | sed 's:/$::' | sort -u)

if [[ ${#source_buckets[@]} -eq 0 ]]; then
  echo "No buckets found under alias ${PROD_ALIAS}."
  exit 0
fi

for bucket in "${source_buckets[@]}"; do
  if [[ ! "$bucket" =~ $INCLUDE_REGEX ]]; then
    continue
  fi
  if [[ "$bucket" =~ $EXCLUDE_REGEX ]]; then
    continue
  fi

  src="${PROD_ALIAS}/${bucket}"
  dst="${GCS_ALIAS}/${GCS_BUCKET}"

  echo "Mirroring ${src} -> ${dst}"
  mc mirror "${mirror_flags[@]}" "${src}" "${dst}"
done

echo "Mirror pass complete."
