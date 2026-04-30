#!/usr/bin/env bash

set -euo pipefail

SRC_ALIAS="hydroshare"
DST_ALIAS="gcs"
DST_BUCKET="hydroshare-resources"
DST_PUBLISHED_BUCKET="hydroshare-published-resources"

command -v mc >/dev/null 2>&1 || {
    echo "mc is required but not installed."
    exit 1
}

mirror_bucket() {
    local src="$1"
    local dst="$2"

    echo "Mirroring ${src} -> ${dst}"
    if ! mc mirror "${src}" "${dst}"; then
        echo "ERROR: Failed to mirror ${src} -> ${dst}" >&2
    fi
}

mc ls "${SRC_ALIAS}" | awk '{print $5}' | sed 's:/$::' | while IFS= read -r bucket; do
    [[ -n "${bucket}" ]] || continue
    case "${bucket}" in
        zips|tmp|bags)
            echo "Skipping ${SRC_ALIAS}/${bucket}"
            ;;
        published)
            mirror_bucket "${SRC_ALIAS}/${bucket}" "${DST_ALIAS}/${DST_PUBLISHED_BUCKET}"
            ;;
        *)
            mirror_bucket "${SRC_ALIAS}/${bucket}" "${DST_ALIAS}/${DST_BUCKET}"
            ;;
    esac
done