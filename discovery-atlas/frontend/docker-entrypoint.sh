#!/bin/sh
ROOT_DIR=/srv/discover-frontend

echo "VITE_APP_BASE is '${VITE_APP_BASE}'"

# 1. Generate Caddyfile with the correct base path
echo "Generating Caddyfile from template..."
if [ -f /etc/caddy/Caddyfile.template ]; then
    sed "s|{{ .VITE_APP_BASE }}|${VITE_APP_BASE}|g" /etc/caddy/Caddyfile.template > /etc/caddy/Caddyfile
    echo "Caddyfile generated:"
    cat /etc/caddy/Caddyfile
else
    echo "Warning: Caddyfile template not found at /etc/caddy/Caddyfile.template"
fi

# 2. Normalize VITE_APP_BASE to remove leading and trailing slashes unless it's just "/" or "./"
# We do this beause at build time, Vite already added a leading and trailing slashes
if [ "$VITE_APP_BASE" = "/" ] || [ "$VITE_APP_BASE" = "./" ]; then
    VITE_APP_BASE="$VITE_APP_BASE"
else
    VITE_APP_BASE=$(echo "$VITE_APP_BASE" | sed 's|^/*||; s|/*$||')
fi
echo "Normalized VITE_APP_BASE is '${VITE_APP_BASE}'"

# Export the normalized value so it's available in the environment
export VITE_APP_BASE="$VITE_APP_BASE"

# 3. Replace placeholders in built files
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