#!/bin/bash

command_output=$(mc ls prod-minio)

buckets=()

while IFS= read -r bucket; do
    buckets+=("$bucket")
done <<< "$command_output"

for bucket in "${buckets[@]}"; do
    bucket_name=${bucket##* }
    bucket_name=${bucket_name%/}
    echo "Bucket: $bucket_name"
    resource_listing=$(mc ls prod-minio/$bucket_name)
    if [[ -z "$resource_listing" ]]; then
        #echo "No resources found in bucket: $bucket_name. Continuing to next bucket."
        continue
    fi
    resources=()

    while IFS= read -r resource; do
        resources+=("$resource")
    done <<< "$resource_listing"

    for resource in "${resources[@]}"; do
        resource_id=${resource##* }
        resource_id=${resource_id%/}
        echo "Resource ID: $resource_id"
        if file_listing=$(mc find "prod-minio/$bucket_name/$resource_id/data/contents/" --print {} 2>/dev/null); then
            files=()
            while IFS= read -r file; do
                files+=("$file")
            done <<< "$file_listing"

            for file_name in "${files[@]}"; do
                if [[ -n "$file_name" ]]; then
                    if ! file_head=$(mc head -n 1 "$file_name" 2>/dev/null); then
                        file_size=$(mc find "$file_name" --print {size})
                        #echo "$file_size - $file_name"
                        if [[ "$file_size" != "0 B" ]]; then
                            echo "Unreadable file detected: $file_name"
                        fi
                    fi
                fi
            done
        fi
    done
done
