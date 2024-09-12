#!/bin/bash

command_output=$(mc ls cuahsi)

lines=()

# Read the command output line by line
while IFS= read -r line; do
    lines+=("$line")
done <<< "$command_output"

# Loop over each line
for line in "${lines[@]}"; do
    parsed_string=${line##* }
    parsed_string=${parsed_string%/}

    # Print the parsed string
    echo "$parsed_string"
    command="mc ilm rule add --transition-days \"0\" --transition-tier \"GCP-STORAGE\" cuahsi/$parsed_string"
    eval $command
done
