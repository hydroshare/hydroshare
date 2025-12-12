#!/bin/sh
ROOT_DIR=/srv/discover-frontend

echo "VITE_APP_BASE is '${VITE_APP_BASE}'"

# 2. Replace placeholders in built files
echo "Replacing environment variable placeholders in built files..."

# Get only environment variables that start with VITE_APP_
for var_name in $(env | grep -E '^VITE_APP_' | cut -d '=' -f 1); do
    value=$(eval "echo \$$var_name")
    
    # Skip if value is empty
    if [ -z "$value" ]; then
        echo "Warning: $var_name is empty, skipping"
        continue
    fi
    
    # Escape special characters for sed
    escaped_value=$(echo "$value" | sed 's/[\/&]/\\&/g')
    
    echo "Processing $var_name with value '$value'"
    
    # Replace in files
    find "$ROOT_DIR" -type f \( -name '*.js' -o -name '*.css' -o -name '*.html' -o -name '*.woff' \) \
        -exec sed -i "s|${var_name}|${escaped_value}|g" {} + 2>/dev/null || true
done

echo "Entrypoint completed. Starting Caddy..."
exec "$@"