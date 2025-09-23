#!/bin/bash

command_output=$(mc ls cuahsi)

lines=()

# Read the command output line by line
while IFS= read -r line; do
    lines+=("$line")
done <<< "$command_output"

# Loop over each line
for line in "${lines[@]}"; do
    bucket_name=${line##* }
    bucket_name=${bucket_name%/}
    # Check if a rule already exists for the bucket
    existing_rule=$(mc ilm rule ls cuahsi/$bucket_name)
    # echo "$existing_rule"

    if [[ -n "$existing_rule" ]]; then
        command=""
        # echo "Rule already exists for $bucket_name, skipping..."
    else
        echo "Adding rule for $bucket_name"
        command="mc ilm rule add --transition-days \"0\" --transition-tier \"GCP-STORAGE\" cuahsi/$bucket_name"
        eval $command
    fi
done
