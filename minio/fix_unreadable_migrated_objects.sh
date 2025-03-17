#!/bin/bash

#command_output=$(mc ls prod-minio)

buckets=('limaos90')

#while IFS= read -r bucket; do
#    buckets+=("$bucket")
#done <<< "$command_output"

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

        file_listing=$(mc ls --recursive prod-minio/$bucket_name/$resource_id/data/contents/)
        files=()
        while IFS= read -r file; do
            files+=("$file")
        done <<< "$file_listing"

        for file in "${files[@]}"; do
            file_name=$(echo "$file" | awk '{for (i=6; i<=NF; i++) printf $i (i<NF ? OFS : "");}')
            #file_name=${file##* }
            #file_name=${file_name%/}

            if [[ -n "$file_name" ]]; then
                #echo "File: [$file_name]"
                #file_head=$(mc head -n 1 prod-minio/$bucket_name/$resource_id/data/contents/$file_name)
                file_size=$(echo "$file" | awk '{print $4}')
                #echo "Parsed file size: $file_size - $file_name"
                if [[ "$file_size" != "0B" ]]; then
                    if ! file_head=$(mc head -n 1 "prod-minio/$bucket_name/$resource_id/data/contents/$file_name" 2>/dev/null); then
                        echo "Unreadable file detected: $file_name"
                    fi
                fi
            fi
        done
    done
done
