# S3 event processing

The S3 proxy sends resource-file mutation and download events to the S3 auth
service. The auth service publishes them to Celery, and workers perform
Django-side processing.

## S3 download activity

The initial reporting scope is successful `s3:GetObject` requests for resource
content files under `{resource_id}/data/contents/`. Bucket listings, object
metadata requests (`HEAD`), failed reads, and non-resource objects are excluded.
Each qualifying request is recorded as one `hs_tracking.Variable` named `s3`,
with the S3 operation in its value. This counts successful read requests, not
unique files or confirmed full transfers; ranged reads count as requests too.

After sending the response body, the proxy posts to the auth service's
`/s3/event/` endpoint in an async background task. The auth service queues
`record_s3_download` on `s3_events`. The proxy's HTTP call has a 300 ms total
deadline and no retry; neither the call nor its deadline delays the file
response. A timeout does not prove the event was lost: it may already be queued.
Tracking is best-effort. On Cloud Run, use instance-based billing for the
proxy to keep CPU available after the response ends. Write and delete
notifications are unchanged.

For download notifications, the proxy logs a warning if the auth service
returns anything other than HTTP `204`, including the status code, bucket,
and object path. Timeouts and request errors are logged separately with the
bucket and object path; request errors also include the exception type.

S3 requests identify a HydroShare user but do not carry the browser's Django
tracking-session cookie. The download tracking task therefore creates a
tracking session for each event and associates it with that user's existing
tracking visitor. Reports should count `s3` activity records rather than these
per-event sessions.

Download events use a dedicated Celery task. They must not be sent through the
resource mutation task, which updates file metadata for writes and deletes.
They must also not trigger metadata extraction.

### Decision: reuse the auth service's event endpoint

For [#6503](https://github.com/hydroshare/hydroshare/issues/6503), we chose to
send the event through the existing auth endpoint after the file response.
Direct publishing would remove an HTTP hop but require each proxy, including
separately deployed proxies such as CIROH's, to have broker access and Celery
configuration. The relay keeps Redis access in the auth service and follows
the existing mutation-event pattern without making downloads wait for tracking.
Roll out the worker and auth service before the proxy so they recognize
download events when the proxy starts sending them.

#### Why start with a 300 ms deadline and no retry?

In the seven-day production Cloud Run log review on November 19, 2026,
151 of 61,223 requests (0.25%) to the auth service's `POST /s3/event/`
endpoint took longer than 300 ms. One request returned HTTP `500`, and the
proxy logged no event-notification timeout warnings.

These are auth-side timings for existing event calls, not full proxy-to-auth
round trips or a measure of missed download events. They support 300 ms as
a starting deadline. We do not retry the notification because a timeout can
occur after the event was queued, and retrying could count the download twice.

The tracking and mutation tasks still share `s3_events` and its workers.
On beta, compare completed test downloads with persisted `s3` records after
the queue drains, and verify those records appear in the normal export.
Check whether a small concurrent download burst delays file-change
processing. If it does, isolate tracking with a separate queue and dedicated
worker capacity.

## Proxy HTTP tests

The proxy download tests use Python's built-in `unittest`. From the repository
root, build the proxy image, then run:

```sh
docker build -t hydroshare/hs-s3-proxy:latest hs_s3_proxy
docker run --rm \
  -v "$PWD/hs_s3_proxy/api:/app/api:ro" \
  -v "$PWD/hs_s3_proxy/tests:/tests:ro" \
  --entrypoint python hydroshare/hs-s3-proxy:latest \
  -m unittest discover -s /tests -p test_download_tracking_unittest.py -v
```

The mounts supply the current source and tests without modifying the running
proxy. These tests simulate the auth, storage, and HTTP notification boundaries;
they do not verify worker processing or database persistence.
