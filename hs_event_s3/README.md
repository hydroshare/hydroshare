# hs_event_s3

Sets up a Kafka consumer listening to S3 event writes and updates the django db based on the change.

The first pass looks for inconsistencies in the resource. This could be optimized to update the db based on the file write.
