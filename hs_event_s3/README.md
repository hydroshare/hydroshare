# S3 event processing

The S3 proxy sends completed resource-file mutations and successful object
downloads to the S3 auth service. The auth service dispatches the events to
Celery workers, which perform Django-side processing.

## S3 download activity

The initial reporting scope is successful `s3:GetObject` requests for resource
content files under `{resource_id}/data/contents/`. Bucket listings, object
metadata requests (`HEAD`), failed reads, and non-resource objects are excluded.
Each qualifying request is recorded as one `hs_tracking.Variable` named `s3`,
with the S3 operation in its value. This counts successful read requests, not
unique files or confirmed full transfers; ranged reads count as requests too.

S3 requests identify a HydroShare user but do not carry the browser's Django
tracking-session cookie. The download tracking task therefore creates a
tracking session for each event and associates it with that user's existing
tracking visitor. Reports should count `s3` activity records rather than these
per-event sessions.

Download events use a dedicated Celery task. They must not be sent through the
resource mutation task, which updates file metadata for writes and deletes.
They must also not trigger metadata extraction.

## Proxy HTTP tests

The proxy download tests use Python's built-in `unittest` and dependencies
already in the proxy image; they do not require pytest or a rebuilt image.
From the repository root, with the local `hydroshare/hs-s3-proxy:latest` image
available, run:

```sh
docker run --rm \
  -v "$PWD/hs_s3_proxy/api:/app/api:ro" \
  -v "$PWD/hs_s3_proxy/tests:/tests:ro" \
  --entrypoint python hydroshare/hs-s3-proxy:latest \
  -m unittest discover -s /tests -p test_download_tracking_unittest.py -v
```

The mounts supply the current source and tests without changing the image or
the running proxy. These tests simulate the auth, storage, and event-service
boundaries; they do not verify Celery processing or database persistence.
