#!/usr/bin/env bash

set -euo pipefail

SRC_ALIAS="hydroshare"
DST_ALIAS="gcs"
DST_BUCKET="hydroshare-beta-resources"

command -v mc >/dev/null 2>&1 || {
    echo "mc is required but not installed."
    exit 1
}

mc ls "${SRC_ALIAS}" >/dev/null
mc mb --ignore-existing "${DST_ALIAS}/${DST_BUCKET}" >/dev/null 2>&1 || true

mc ls "${SRC_ALIAS}" | awk '{print $5}' | sed 's:/$::' | while IFS= read -r bucket; do
    [[ -n "${bucket}" ]] || continue
    case "${bucket}" in
        zips|tmp|bags) continue ;;
    esac

    echo "Mirroring ${SRC_ALIAS}/${bucket} -> ${DST_ALIAS}/${DST_BUCKET}"
    mc mirror "${SRC_ALIAS}/${bucket}" "${DST_ALIAS}/${DST_BUCKET}"
done