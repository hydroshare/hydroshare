# hs-s3-auth

S3 authorization and service account management service for HydroShare.

## Standing up the service

From the `hs_s3_auth/` directory:

```bash
docker compose up -d
```

This starts four containers:

| Container | Purpose |
|-----------|---------|
| `micro-auth` | FastAPI authorization service (port 80) |
| `postgres` | PostgreSQL database seeded from `tests/init-scripts/` (port 5432) |
| `redis` | Redis cache (port 6379) |
| `minio` | MinIO object storage with the auth plugin pointed at `micro-auth` (ports 9000, 9001) |

To tail logs:

```bash
docker compose logs -f micro-auth
```

To stop and remove containers:

```bash
docker compose down
```

To also remove persistent volumes (database, MinIO data):

```bash
docker compose down -v
```

## Running the tests

With the stack running, exec into the `micro-auth` container and run pytest:

```bash
docker compose exec micro-auth python -m pytest tests/ -v
```

To run a specific test file:

```bash
docker compose exec micro-auth python -m pytest tests/test_events_router.py -v
```

To run a specific test:

```bash
docker compose exec micro-auth python -m pytest tests/test_minio_service_accounts.py::test_create_service_account -v
```

> **Note:** The `tests/` directory and `api/` source are bind-mounted into the container (see `docker-compose.yml`), so edits on the host are reflected immediately without rebuilding.
