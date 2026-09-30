#!/usr/bin/env bash
set -euo pipefail

# Mirrors each top-level prefix under every source bucket into a single target bucket under GCS_ALIAS.
# This preserves the object layout under each source bucket root instead of copying the entire bucket tree.
# Example behavior:
#   prod-minio/<user_bucket>/<prefix>/<resource_path> -> gcs/<target_bucket>/<prefix>/<resource_path>
#
# Required environment variables:
#   PROD_ALIAS        Example: prod-minio
#   GCS_ALIAS         Example: gcs
#
# Optional environment variables:
#   SYNC_CONFIG       main|published|ciroh (default: main); selects the default
#                      GCS_BUCKET/INCLUDE_REGEX/EXCLUDE_REGEX preset below. Any of the
#                      three can still be overridden explicitly.
#   GCS_BUCKET        Example: hydroshare-beta-resources
#   DRY_RUN           true|false (default: true)
#   OVERWRITE         true|false (default: true)
#   REMOVE            true|false (default: false)
#   INCLUDE_REGEX     Regex bucket allowlist
#   EXCLUDE_REGEX     Regex bucket denylist
#
# SYNC_CONFIG presets:
#   main       - all buckets except published/ciroh-data/bags/tmp/zips -> hydroshare-403701-prod-cloud-native-resource
#   published  - published bucket only                                -> hydroshare-published-resources
#   ciroh      - ciroh-data bucket only                                -> ciroh-hydroshare-data
#
# Notes:
# - Buckets are discovered via `mc ls <PROD_ALIAS>`.
# - Bucket names ending with '/' are normalized.
#
# Targeted sync mode:
# - If lines of the form '<bucket_name>/<resource_short_id>' are piped in on stdin,
#   only those resource prefixes are mirrored (bucket discovery is skipped entirely).
#   This is how hs_core's list_recently_updated_resource_buckets management command
#   is meant to be consumed:
#     python manage.py list_recently_updated_resource_buckets --hours 24 \
#       | PROD_ALIAS=prod-minio GCS_ALIAS=gcs ./mirror-prod-minio-users-to-gcs.sh

# 3 runs for running the data sync (remove dry-run to actually perform the migration). Note you
# must have the aliases set up in your mc config for prod-minio, gcs and gcs-ciroh, and the target
# bucket must already exist in GCS.:

# all non-published and non-ciroh-data buckets, dry-run:
# DRY_RUN=true SYNC_CONFIG=main PROD_ALIAS=prod-minio GCS_ALIAS=gcs ./mirror-prod-minio-users-to-gcs.sh

# published bucket only, dry-run:
# DRY_RUN=true SYNC_CONFIG=published PROD_ALIAS=prod-minio GCS_ALIAS=gcs ./mirror-prod-minio-users-to-gcs.sh

# ciroh-data bucket only, dry-run:
# DRY_RUN=true SYNC_CONFIG=ciroh PROD_ALIAS=prod-minio GCS_ALIAS=gcs-ciroh ./mirror-prod-minio-users-to-gcs.sh


SYNC_CONFIG="${SYNC_CONFIG:-main}"

case "$SYNC_CONFIG" in
  main)
    default_gcs_bucket="hydroshare-403701-prod-cloud-native-resource"
    default_include_regex=".*"
    default_exclude_regex="^(published|ciroh-data|bags|tmp|zips)"
    ;;
  published)
    default_gcs_bucket="hydroshare-403701-prod-cloud-native-published"
    default_include_regex="^published$"
    default_exclude_regex="^$"
    ;;
  ciroh)
    default_gcs_bucket="hydroshare-403701-prod-cloud-native-ciroh"
    default_include_regex="^ciroh-data$"
    default_exclude_regex="^$"
    ;;
  *)
    echo "ERROR: Unknown SYNC_CONFIG '${SYNC_CONFIG}'. Expected one of: main, published, ciroh." >&2
    exit 1
    ;;
esac

PROD_ALIAS="${PROD_ALIAS:-hydroshare}"
GCS_ALIAS="${GCS_ALIAS:-gcs}"
GCS_BUCKET="${GCS_BUCKET:-$default_gcs_bucket}"
DRY_RUN="${DRY_RUN:-false}"
OVERWRITE="${OVERWRITE:-true}"
REMOVE="${REMOVE:-false}"
INCLUDE_REGEX="${INCLUDE_REGEX:-$default_include_regex}"
EXCLUDE_REGEX="${EXCLUDE_REGEX:-$default_exclude_regex}"

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

  echo "Discovering root prefixes under ${src}"

  root_prefixes=()
  if ! ls_output=$(mc ls "${src}" 2>/dev/null); then
    echo "ERROR: Unable to list source bucket ${src}; skipping bucket." >&2
    continue
  fi

  while IFS= read -r prefix; do
    [[ -n "$prefix" ]] && root_prefixes+=("$prefix")
  done < <(printf '%s\n' "$ls_output" | awk '{print $NF}' | sed 's:/$::' | sort -u)

  if [[ ${#root_prefixes[@]} -eq 0 ]]; then
    echo "No root prefixes found under ${src}"
    continue
  fi

  for prefix in "${root_prefixes[@]}"; do
    src_prefix="${src}/${prefix}"
    dst_prefix="${dst}/${prefix}"

    echo "Mirroring ${src_prefix} -> ${dst_prefix}"
    if ! mc mirror "${mirror_flags[@]}" "${src_prefix}" "${dst_prefix}"; then
      echo "ERROR: Failed to mirror ${src_prefix} -> ${dst_prefix}; continuing to next prefix." >&2
      continue
    fi
  done
done

echo "Mirror pass complete."
