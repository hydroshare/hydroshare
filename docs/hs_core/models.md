:::hs_core.models

## Resource size cache

Resource file sizes are cached in Django; an unknown file size is counted as zero
for quota until it is refreshed. Quota sums the cached sizes of resources for
which the user is the quota holder, excluding published resources by default.
Creating a resource file (including bulk creation) or replacing its contents
refreshes its size from storage. An S3 event refreshes the size when linking an
already registered file; metadata-only saves do not re-read it.
Resource `size` still resolves unknown file sizes from S3. Resource totals are
populated lazily, including for existing resources, and invalidated transactionally
by Django file mutations. Direct SQL, older
application versions, and bulk conflict updates bypass or cannot maintain this
cache and must not be used to change resource files.

For a rolling deployment, apply the migration first, then deploy with
`RESOURCE_SIZE_CACHE_ENABLED = False` to all application and worker processes.
Once all file writers are upgraded, pause file writes, clear
`ResourceSizeCache` rows with the command below, enable the setting and restart
all processes before resuming writes. Use the same procedure after any
out-of-band database changes. The cache warms on demand; no S3 calls are needed
for quota calculation.

```shell
python manage.py shell -c "from hs_core.models import ResourceSizeCache; ResourceSizeCache.objects.all().delete()"
```