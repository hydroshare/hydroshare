# Configuring a Developer Environment

## Standard Configuration

### Database-backed S3 zones in local Docker

The local Compose deployment stores zone settings in the database. The web app
encrypts each S3 secret with a local Fernet key; the extraction worker and S3
proxy fetch their configuration from a token-protected internal web endpoint.
Only S3 access/secret credentials are supported, including GCS HMAC keys;
Google service-account JSON keys are not supported.
Configure each zone's internal endpoint for service-to-storage traffic and its
public endpoint for browser downloads. Download URLs are signed for the public
endpoint, which must be reachable by the user's browser.

The first-start script generates a random local encryption key and service token
if they do not already exist. Existing files are preserved. For other workflows,
create or validate them using:

```sh
python3 scripts/create_local_zone_secrets.py config
```

Keep both files private and outside database snapshots and version control.
Do not overwrite existing files: doing so makes existing encrypted credentials
unreadable or invalidates the service token.
Never use a production encryption key locally. A snapshot encrypted with a
different key cannot be decrypted; database-zone loading fails rather than
falling back to the settings file. Encryption alone is not an access boundary:
use separate local-only IAM credentials and, where possible, block network
access to production buckets. Anyone with database access and the encryption
key can recover the credentials. The token grants access to decrypted zone
credentials and the internal HTTP endpoint is intended only for the trusted
local Compose network, not an untrusted network.

The first-start script imports and migrates the database, then seeds the zones
from `RESOURCE_S3_ZONES_CONFIG` before starting the extraction worker and
proxy. The seed command accepts only the local `http://minio:9000` endpoint;
public endpoints must also use HTTP and a local hostname (`localhost`,
`127.0.0.1`, `::1`, or `host.docker.internal`). It fails if the settings
contain a different endpoint. Ensure the configured credentials match the local
MinIO service. Before importing a snapshot
separately, stop all five zone consumers so that no
running process can retain old credentials. After the import, initialize the
database *before* starting them:

```sh
docker compose -f local-dev.yml stop hydroshare defaultworker hs_event_s3 hs_extract hs-s3-proxy
# Import the snapshot using your existing local procedure.
docker compose -f local-dev.yml build hydroshare hs_extract hs-s3-proxy
docker compose -f local-dev.yml up -d postgis pgbouncer redis minio mongodb
docker compose -f local-dev.yml run --rm --no-deps hydroshare python manage.py migrate --noinput
docker compose -f local-dev.yml run --rm --no-deps hydroshare python manage.py seed_local_s3_zones --confirm
docker compose -f local-dev.yml up -d hydroshare defaultworker hs_event_s3 hs_extract hs-s3-proxy
```

The seed command **disables all imported zones**, then replaces or creates
the zones from the local settings (by default, `hydroshare`, `published`, and
`ciroh`). It does not move bucket data or alter user quota
assignments. Other imported zones remain disabled; review affected user quotas
before using those resources. Conflicting bucket names cause the transaction to
fail rather than silently deleting zones. Create the MinIO buckets using the
existing local setup if they do not already exist. The services can fail until
the database is migrated and seeded.

Staff with the appropriate Django admin permissions can manage Storage zones
under `/admin/`. Leave the secret field blank to retain its current value.
The default zone must remain enabled; an assigned zone cannot be disabled.
Zone names and bucket names cannot be changed after creation, and deleting
zones through the admin is disabled. A configuration change does not move
objects. Zone settings are process-cached and do not automatically refresh.
Restart all five services listed above after edits or credential rotations;
until then, different processes can use different versions. The existing
settings and environment-based configuration remain available for deployments
that do not set `S3_ZONES_DATABASE_ENABLED=true`.

To apply an edit after the stack is initialized:

```sh
docker compose -f local-dev.yml restart hydroshare defaultworker hs_event_s3 hs_extract hs-s3-proxy
```

### Docker, docker-machine, and Vagrant

#### Linux

#### OSX

### hscl

### PyCharm

### Running the tests

## Advanced Topics
