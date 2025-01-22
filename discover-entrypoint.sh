#!/bin/sh
ROOT_DIR=/hydroshare/hs_discover
# Replace env vars in static files
for file in $ROOT_DIR/static/js/*.js $ROOT_DIR/static/js/*.js.map $ROOT_DIR/templates/hs_discover/js/*.js $ROOT_DIR/templates/hs_discover/index.html;
do
    echo "Processing $file ...";
    # LC_ALL=C sed -i "" 's|VUE_APP_BUCKET_URL_PUBLIC_PATH_PLACEHOLDER|'${VUE_APP_BUCKET_URL_PUBLIC_PATH}'|g' $file
    sed -i 's|VUE_APP_BUCKET_URL_PUBLIC_PATH_PLACEHOLDER|'${VUE_APP_BUCKET_URL_PUBLIC_PATH}'|g' $file
done

exec "$@"
