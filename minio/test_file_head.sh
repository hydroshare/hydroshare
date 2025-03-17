bucket_name="limaos90"
resource_id="977c24b20a1a4c3caf71bf7e47ff802a"
file_name="maps/etp/etp00000.219"


if ! file_head=$(mc head -n 1 prod-minio/$bucket_name/$resource_id/data/contents/$file_name 2>/dev/null); then
    echo "Error: Unable to read file: $file_name"
else
    echo "File head: $file_head"
fi
