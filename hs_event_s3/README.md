# hs_event_s3

Sets up a Kafka consumer listening to S3 event writes and updates the django db based on the change.

The first pass looks for inconsistencies in the resource. This could be optimized to update the db based on the file write.

## Error handling & observability

- The `notify_hs_django` pipeline is wrapped in a `try`/`catch` block (`notify_hs_django_pipeline.yaml`) so Redpanda Connect logs any processor errors with context. Errors are emitted as `ERROR` log lines from the `log` processor.
- The processor code (`hsevent/main.py`) now raises decoding and processing errors after logging them; stack traces and the resource/key involved are printed to container logs.
- To inspect issues locally: `docker compose logs -f hs_event_s3` (or `docker-compose` depending on your CLI). Look for `ERROR [hs_event_s3]` or `notify_hs_django_processor failed` entries.
- Typical failures you should see surfaced:
  - invalid JSON from the event (`Failed to decode payload from Redpanda`)
  - missing required fields (`Incomplete event payload - key or resource id missing`)
  - missing Django objects (e.g., resource not found) or unexpected processing errors, which bubble up and are logged with the resource id and key.
