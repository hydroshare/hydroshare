# S3 event processing

The S3 proxy sends completed resource-file mutations to the S3 auth service,
which dispatches them to Celery. For download tracking, the proxy publishes
directly to Celery. Workers perform Django-side processing for both paths.

## S3 download activity

The initial reporting scope is successful `s3:GetObject` requests for resource
content files under `{resource_id}/data/contents/`. Bucket listings, object
metadata requests (`HEAD`), failed reads, and non-resource objects are excluded.
Each qualifying request is recorded as one `hs_tracking.Variable` named `s3`,
with the S3 operation in its value. This counts successful read requests, not
unique files or confirmed full transfers; ranged reads count as requests too.

After sending the response body, the proxy publishes `record_s3_download` to
the `s3_events` queue in a background thread. Set `CELERY_BROKER_URL` on the
proxy to the same Redis broker and database as the S3 event worker in that
environment. Store any credentials in the deployment's secret manager. If
the URL is not set, the proxy logs that tracking was skipped.

Publishing does not delay the file response. Redis connect and socket
operations use 300 ms timeouts (not a total publish deadline), with no Celery
publish retry. Tracking is best-effort: interrupted streams, broker failures,
or instance shutdown can leave requests uncounted. On Cloud Run, use
instance-based billing for the proxy to keep CPU available after the response
ends. Write and delete notifications are unchanged.

S3 requests identify a HydroShare user but do not carry the browser's Django
tracking-session cookie. The download tracking task therefore creates a
tracking session for each event and associates it with that user's existing
tracking visitor. Reports should count `s3` activity records rather than these
per-event sessions.

Download events use a dedicated Celery task. They must not be sent through the
resource mutation task, which updates file metadata for writes and deletes.
They must also not trigger metadata extraction.

### Decision: publish download tracking directly to Celery

For [#6503](https://github.com/hydroshare/hydroshare/issues/6503), we chose
direct publishing after the response. Waiting for an HTTP acknowledgment
before streaming would delay the download, even with an async client.
Sending HTTP after streaming would avoid the wait but still depend on the
auth service to relay the message. Direct publishing removes that extra hop
at the cost of giving the proxy access to the Redis broker. Occasional
missed tracking events are acceptable; file delivery does not wait on
tracking.

The tracking and mutation tasks still share `s3_events` and its workers.
On beta, verify an isolated download produces an `s3` record and appears in
the normal export. Then check whether a small concurrent download burst
delays file-change processing. If it does, isolate tracking with a separate
queue and dedicated worker capacity.

## Proxy HTTP tests

The proxy download tests use Python's built-in `unittest`. From the repository
root, build the proxy image with its Celery dependency, then run:

```sh
docker build -t hydroshare/hs-s3-proxy:latest hs_s3_proxy
docker run --rm \
  -v "$PWD/hs_s3_proxy/api:/app/api:ro" \
  -v "$PWD/hs_s3_proxy/tests:/tests:ro" \
  --entrypoint python hydroshare/hs-s3-proxy:latest \
  -m unittest discover -s /tests -p test_download_tracking_unittest.py -v
```

The mounts supply the current source and tests without modifying the running
proxy. These tests simulate the auth, storage, and broker boundaries; they do
not verify worker processing or database persistence.
