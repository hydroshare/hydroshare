# Preservation-Only Mode: Options and Feasibility

Status: exploration only. No code has been changed.

## Goal

Move HydroShare into a "preservation-only" state in which data is retained and can be seen, but nothing
can be created, changed or downloaded by users, and the deployment is as cheap as practical.

Requirements shared by every option:

- Resource metadata can be viewed (metadata-only: no file contents are served to users).
- No resource creation, editing, sharing, publishing, copying or deletion.
- No file downloads for users. Admins retrieve data only through direct S3/GCS access.
- Published resources keep their DOI linkage (the landing page keeps resolving at `/resource/<id>/`).
  No DataCite POST or PUT happens in this mode, and DataCite target hostnames do not change.
- Components made unnecessary are not deployed.

The change is applied to the existing deployment (not a fresh deploy).

Sizes are relative (S, M, L), not time estimates.

## Options at a glance

| | Option 1: Flag in the existing app | Option 2: Static catalog | Option 3: Atlas-backed slim app |
|---|---|---|---|
| Idea | `PRESERVATION_ONLY` flag restricts the full app | Replace the app with a static SPA over a compiled catalog | Replace the app with a small API and the existing Discover SPA over the Atlas index |
| Private resources visible to owners | Yes | Yes, but visible to everyone (all resources listed) | Yes, only to their owners (server-enforced filter) |
| Login | Existing | None | Slim OIDC login |
| Search UX | Existing | Rebuilt client-side | Existing Discover SPA |
| Runs | Django, DB, Redis, S3 services | Static hosting only | Small API, Atlas, static SPA |
| Relative cost | Highest | Lowest | Medium |
| Relative effort | M to L (many enforcement points) | M | M to L (visibility model, auth, frontend) |

Options 2 and 3 are independent alternatives. Option 3 is heavier and costs more than Option 2 but keeps
private resources visible only to their owners. Option 2 lists every resource publicly.

---

## Option 1: Flag in the existing deployment

Add a deployment mode (`PRESERVATION_ONLY=true`) to the existing app. Enforce it in the Django, REST and
S3 layers, and stop deploying components that are no longer needed.

### Decisions

| Question | Decision |
|---|---|
| View vs download | Metadata-only. File contents are not served. |
| File listing | Kept. Served from the database, not S3. |
| Auth | Kept (OIDC login, view permissions, "my resources"). |
| Admin data access | Direct S3 protocol only. No download through the Django UI or REST API. |
| DataCite | No POST or PUT in this mode. Existing DOIs are unaffected as long as landing pages are served. |
| Deployment | Modify the existing Cloud Run / Cloud SQL deployment in place. |

### Current-state findings

#### Existing building blocks

- `ENABLE_EDIT_ACTIONS` already exists in
  [hs_s3_auth/api/routers/minio.py](../../hs_s3_auth/api/routers/minio.py).
  It denies all S3 write and delete actions for non-admin users unless set to `true`.
  Default is `false`. The platform-recipes Terraform sets it to `true` on the `hs_s3_auth` service.
- `DISABLE_PERIODIC_TASKS` exists in [hs_core/tasks.py](../../hs_core/tasks.py)
  (`setup_periodic_tasks`). When true, no Celery beat schedule is registered.
- S3 admin access exists. In `hs_s3_auth`, superusers and the `cuahsi` account are allowed every action.
  `/verify-signature/` authenticates S3 clients by per-user access key.
- `ResourceFile` rows in the DB hold path, size, checksum and modified time for every file.

#### Gaps

- No global read-only or maintenance flag anywhere.
- No global DRF permission class (see Glossary). `REST_FRAMEWORK` in
  [hydroshare/settings.py](../../hydroshare/settings.py#L719) sets no `DEFAULT_PERMISSION_CLASSES`,
  so each REST view does its own checks.
- Middleware ([hydroshare/settings.py](../../hydroshare/settings.py#L591)) does no mode-wide enforcement.
- Superusers bypass `ENABLE_EDIT_ACTIONS` in `hs_s3_auth`, so an admin can write through S3.
- File browser listing (`data_store_structure` in
  [hs_core/views/resource_folder_hierarchy.py](../../hs_core/views/resource_folder_hierarchy.py#L38))
  lists files from S3 (`istorage.listdir`) and not from the DB.

### Enforcement design

Layers, from the cheapest global control to defense in depth.

1. **Setting.** `PRESERVATION_ONLY` env var read in `hydroshare/settings.py`. Exposed to templates through a
   context processor and to the Vue discover app (API field or build var). Size: S.
2. **Middleware.** A new middleware that rejects non-safe methods (POST, PUT, PATCH, DELETE) with 403 or 503.
   Small allowlist for login, logout and OIDC callbacks. It also denies all download routes outright
   (not "admin only"), because admins use S3:
   - `rest_download` and `download` in [django_s3/views.py](../../django_s3/views.py)
   - bag and zip endpoints, `zip_by_aggregation_file`, `file_download_url_mapper`
   - `data_store_folder_zip` and `data_store_folder_zip_public`
   - `GET /hsapi/resource/<id>/` (redirects to the bag)
   
   GET endpoints that mutate state need to be found and listed. Size: M.
3. **Permission layer.** Gate `can_change_resource`, `can_delete_resource`, `can_change_resource_flags`,
   `can_share_resource` and similar in [hs_access_control/models/user.py](../../hs_access_control/models/user.py),
   and `authorize()` in [hs_core/views/utils.py](../../hs_core/views/utils.py#L323).
   Page processors render edit controls from these, so edit UI disappears with no per-template work.
   Decision needed: whether management commands and Django admin are also blocked. Size: M.
4. **REST views.** Add a `PreservationOnly` permission class, either per view or as a global default in
   `REST_FRAMEWORK` with safe methods allowed. The global default is cleaner but changes behaviour for every
   view and needs testing. This is the largest uncertainty. Size: M to L.
5. **S3 path.** Set `ENABLE_EDIT_ACTIONS=false`. For stricter control, deny the data-object read actions for
   non-admins in `_check_user_authorization`. Size: S.
6. **IAM backstop.** Give the app's GCS HMAC service account `storage.objectViewer` on the resource and
   published buckets instead of `objectAdmin`. This enforces read-only at the infrastructure level,
   independent of app code, and also covers the superuser write bypass.
   Admins who need to write would use a separate privileged identity. Size: S, but needs coordination.
7. **Celery guards (optional).** Check the flag inside mutation tasks (`copy_resource_task`,
   `delete_resource_task`, `create_new_version_resource_task`, `add_zip_file_contents_to_resource`,
   `create_temp_zip`, `process_s3_event`). Largely moot once the workers are not deployed. Size: S.
8. **Direct writers (optional).** Guard `hs_core.hydroshare.resource` functions
   (`create_resource`, `add_resource_files`, `delete_resource_file`) as a backstop. Size: S.
9. **Other mutating surfaces to audit.** Django admin, user profile and registration edits,
   `hs_collection_resource`, `hs_tools_resource`, `hs_labels`, `hs_communities` views.

### File listing

Preserve what the landing page shows. Under the flag, `data_store_structure` reads from `ResourceFile` rows
instead of S3. Aggregation and folder metadata are already in the DB.

- Backfill `_size`, `_checksum` and `_modified_time` before cutover. They are normally filled lazily by
  `nightly_cache_file_system_metadata`.
- Empty folders exist only in S3 and will not appear. Probably acceptable.
- File browser and landing-page templates must render names and sizes without download links or previews.
- Check for other landing-page code that touches S3 at render time. A practical test is to run the app without
  S3 credentials and click through representative resources.
- Size: S to M, plus the UI work in the next section.

### UI changes

Hide edit and download controls in templates and in the Vue discover app (`discovery-atlas/frontend`).
The permission-layer change handles most edit controls automatically. Download links and preview
components need explicit handling. Size: M.

### DataCite and DOIs

- Publishing registers a DOI whose target URL is the resource landing page. Resolution
  (`doi.org` to DataCite to landing page) requires only that `/resource/<id>/` keeps being served on the
  registered hostname. No application code needs to run.
- Publish, metadata update and deposit calls to DataCite
  ([hs_core/hydroshare/resource.py](../../hs_core/hydroshare/resource.py#L1000), `requests.post` / `requests.put`)
  are reached only through the publish and metadata-edit paths, which are blocked. Existing resources cannot be
  published in this mode.
- `DATACITE_USERNAME` / `DATACITE_PASSWORD` are not needed at runtime in this mode.
- Hostname changes are out of scope.

Pre-cutover check: find resources whose DOI is not yet activated
(`pending`, `update_pending`, `failure`, `update_failure` markers, see
`DataciteSubmissionStatus` in [hs_core/enums.py](../../hs_core/enums.py)) and resources in the
"under review for publication" state. These cannot complete after cutover, so resolve or accept them first.

### Admin access via S3

- Admins already have full access through `hs_s3_proxy` and `hs_s3_auth` (superuser bypass and
  service-account signature verification). Keep those two services deployed. They can scale to zero.
- Confirm how admins obtain S3 access keys (`get_user_service_account_secrets_and_id`) and that the flow
  still works.
- Decide whether superusers should be able to write via S3. If not, rely on the IAM backstop (layer 6).

### Deployment changes (existing environment)

Terraform in `platform-recipes/hydroshare/infrastructure/cloud-native/module`.
Add a `preservation_only` variable and use `count` / `for_each` on the following. Size: M.

| Component | Action | Notes |
|---|---|---|
| `companion` Cloud Run service | Remove | Also remove the `/companion/*` LB route and companion secrets. |
| `hs-extract` worker pool | Remove | Extraction only happens on new uploads. |
| `hs-event-s3` worker pool | Remove | Only reacts to bucket writes. |
| `beat` worker pool | Remove | Also set `DISABLE_PERIODIC_TASKS`. |
| `defaultworker` pool | Remove | Only needed for bag and zip and other write-side tasks. |
| `hs_s3_auth`, `hs_s3_proxy` | Keep | `ENABLE_EDIT_ACTIONS` from the variable. Min instances 0. |
| `hydroshare` web | Keep | Lower min instances (prod 2 to 1) and CPU/memory. Add `PRESERVATION_ONLY`. |
| `discover` SPA | Keep | Hide edit and download controls. |
| Cloud SQL | Keep, downsize | Prod is `db-custom-8-30720` REGIONAL. |
| Redis | Optional | Cache and S3 auth cache remain. Could move to DB or in-memory cache later. |
| Scheduled jobs | Keep `pg_backup` | `stats` and `tracking_csv_export` only if still wanted. |
| Resource and published buckets | Keep | Consider IAM read-only binding and cheaper storage class. |
| Secrets | Remove unused | companion secrets, datacite password. |

#### Rollout in an existing environment

- **Drain first.** Let in-flight Celery work and the `s3_events`, `extract` and `default` queues empty
  before removing workers. Run `ensure_published_resources_have_bags` so published resources have bags in the
  bucket.
- **Backfill.** Run the `ResourceFile` system-metadata backfill before switching the file listing.
- **Order.** Ship the application changes (flag defaults to off), verify with the flag on in dev, then flip in prod,
  then apply the Terraform removals.
- **Downsizing.** Cloud SQL tier or HA changes in place cause a restart. Plan a window.
  Redis scaling may also disrupt.
- **Reversibility.** Setting the variable back to false recreates the removed services. Data is untouched.
  Anything written between modes needs to be reconciled by the normal S3 event flow.
- **Deletion protection.** Prod Cloud SQL has deletion protection. Downsizing does not need it lifted, but
  confirm with a plan.

### Cost levers (rough ordering)

1. Cloud SQL tier and HA downsizing.
2. Removing worker pools (4 pools; prod runs 3 instances each plus beat).
3. Lower web min instances and per-instance resources.
4. Redis removal or downsizing (optional).
5. Cheaper storage class on the resource buckets.

### Relative level of effort

| Area | Size |
|---|---|
| Setting and template context | S |
| Middleware (non-GET and download denylist) | M |
| Permission-layer gating | M |
| DRF views | M to L |
| File listing from DB | S to M |
| UI changes (templates, Vue app) | M |
| `hs_s3_auth` flag plus IAM backstop | S |
| Celery and direct-writer guards | S |
| Terraform | M |
| Pre-cutover checks (DOI states, backfills, bag generation) | S to M |

### Risks

- DRF: without a global permission class, every REST view needs auditing, and a global default affects
  every view.
- GET endpoints that mutate, or new endpoints added later, may bypass the middleware list.
  A test that walks the URL conf and asserts all non-GET routes are rejected under the flag would catch this
  (deferred for now).
- Superuser S3 write bypass. Mitigated by IAM.
- File listing may silently differ from the S3 view (empty folders, rows with missing size or checksum).
- Landing-page code that reads S3 at render time must be found and guarded.

### Open questions

- Should management commands and Django admin be blocked or exempt?
- Should superusers be able to write through S3, or is the IAM read-only binding enforced?
- How do admins obtain S3 access keys, and does that flow need to be preserved?
- Do any usage-tracking tables (`hs_tracking`) need to keep recording views?
- Which resources are in pending or under-review states at cutover?

---

## Option 2: Static catalog

Take the whole application down and deploy a static single-page app that shows a notice and a searchable
list of resources, so users can confirm their data still exists. Nothing runs server-side.

### Findings

- Each resource has a `dataset_metadata.json` (schema.org JSON-LD) at `<resource id>/.hsjsonld/dataset_metadata.json`.
  The same file already feeds the Atlas discovery index
  ([hs_core/hydroshare_atlas_discovery_collection.py](../../hs_core/hydroshare_atlas_discovery_collection.py)).
- There are about 20k resources, and every resource has a `dataset_metadata.json`.
- Data is frozen in this mode, so the index is built once. No event-driven sync is needed.
- The existing Atlas catalog only contains discoverable resources. The sync in
  [hs_event_s3/tasks.py](../../hs_event_s3/tasks.py#L100-L108) deletes private ones. Option 2 does not use
  the Atlas catalog, so it can include all resources.
- The Vue landing page already fetches `dataset_metadata.json` through the S3 proxy
  ([discovery-atlas/frontend/src/components/landing-page/shared.ts](../../discovery-atlas/frontend/src/components/landing-page/shared.ts#L195)).

### Design

A one-time job reads `dataset_metadata.json` for every resource, regardless of sharing status, and writes a
slim catalog (id, title, creators, dates, type, keywords, DOI, short description). It can be a local script or a
Cloud Run job. The UI is deliberately minimal: a table of title, authors and a few other fields, with search and
sort. A visibility column can be included if the UI should show a "private" badge.

| Variant | Search and sort | Notes |
|---|---|---|
| B: JSON catalog | MiniSearch, Fuse or Orama in the browser, or Pagefind for chunked static search | At 20k records the catalog is a few MB gzipped. Best text search (fuzzy, prefix). Likely sufficient. |
| C: Parquet | DuckDB-WASM reading Parquet from GCS with HTTP range requests (needs bucket CORS) | One-time conversion: DuckDB `read_json_auto` over the files, then `COPY ... TO 'catalog.parquet'`. SQL sorting and filtering. Text search limited to `ILIKE` or a basic FTS extension. No real benefit at 20k records beyond SQL ergonomics. |

Other server-based layers (BigQuery over GCS, Typesense or Meilisearch) were considered. They add a service or
per-query cost and do not fit the "as slim as possible" goal.

### Private resources

By default, all resources are listed regardless of sharing status. This is the accepted trade-off of this
option: metadata of private resources becomes visible to the public. Only the compiled catalog is public;
the buckets stay private.

This needs sign-off from whoever owns the privacy policy, since private resources can hold unpublished work
or sensitive locations. The catalog contents are a deliberate choice for non-public resources:

1. Full catalog fields (the default and simplest).
2. Redacted: for example only the ID, title, creator names and dates. No abstract, keywords or coverage.
3. Excluded entirely.

Redaction is cheap in the catalog builder, since the minimal UI only needs a few fields. Option 3 is the
alternative if private resources must be visible only to their owners.

### Landing pages and DOIs

- `/resource/<id>/` can be rendered by the SPA from `dataset_metadata.json`.
- Some landing-page data currently comes from Django and Postgres (creator profile links, view and download
  counts, alerts, owners, from [hs_discover/views.py](../../hs_discover/views.py)). These would be dropped or
  baked into the catalog.
- Hosting needs SPA fallback routing so deep links return `index.html`. A GCS website bucket with a not-found
  page returns a 404 status, so use the load balancer or a small nginx.

### Deployment

- Replace everything with a GCS bucket, CDN and the existing load balancer (change the default backend to a
  backend bucket).
- Remove Django web, `hs_s3_auth`, `hs_s3_proxy`, Cloud SQL, Redis, all worker pools and Companion.
- Admin data access is direct GCS access with IAM, so the S3 proxy is not needed.
- Keep a final Cloud SQL export in cold storage and write a restore runbook. Deleting Cloud SQL is the main
  irreversible step and needs sign-off.
- Keep the resource and published buckets (read-only, ideally cheaper storage class).

Lost: login, "my resources", view and download counts, and tracking. Private resources are listed for
everyone, not just their owners.

### Level of effort

| Area | Size |
|---|---|
| Catalog builder | M |
| Frontend: search table and landing page from static data | M to L |
| Static hosting and load balancer routing | S to M |
| Final DB export and restore runbook | S |

The frontend is the largest item. Replicating a subset of the Atlas filters in the browser is the part to scope.

### Open questions

- Is it acceptable to expose non-public resource metadata, and if so, in full or redacted form?
- Is a restore path (not an immediate one) enough for retention of the database and Mongo data?

---

## Option 3: Atlas-backed slim app

Keep the existing Discover SPA and its Atlas search index, but replace the Django application with a small
API. Index all resources (including private), mark visibility, and show private resources only to their owners
when they search with a "private to me" filter. Remove the link to the resource landing page from search
results.

### Findings

- Existing pipeline: `dataset_metadata.json` is copied into the MongoDB Atlas `discovery` collection by
  `collect_file_to_catalog` ([hs_core/hydroshare_atlas_discovery_collection.py](../../hs_core/hydroshare_atlas_discovery_collection.py)).
  The Django endpoints `/hsapi/discovery-atlas/search` and `/typeahead`
  ([hs_rest_api/discovery_atlas.py](../../hs_rest_api/discovery_atlas.py)) build an Atlas Search `$search`
  pipeline (fuzzy search, autocomplete, sorting, filters).
- Only discoverable resources are in the index today
  ([hs_event_s3/tasks.py](../../hs_event_s3/tasks.py#L100-L108)).
- The search view returns the full stored document via `$lookup`.
- The Discover SPA search has no auth awareness. Its `User` model
  ([discovery-atlas/frontend/src/models/user.model.ts](../../discovery-atlas/frontend/src/models/user.model.ts))
  is a leftover ORCID-style login that search does not use. Login and the navigation bar come from the Django
  theme shell (`pages/search.html`, which embeds the SPA in an iframe, see
  [hs_discover/views.py](../../hs_discover/views.py)).
- `dataset_metadata.json` carries creators but, as far as seen, no owner or sharing information (verify).
  That lives in Postgres.

### Visibility model

1. **Index everything.** Remove the `discoverable` gate in the event sync. Backfill private resources by
   reading their `dataset_metadata.json` from S3 (they are not in Mongo today).
2. **Add access fields** to each document, written at ingest from Postgres:
   - `visibility`: public, discoverable or private.
   - `access_users`: user identifiers (username, lowercased, or stable user id). Not emails.
   
   Decide whether shared-with-me (edit or view) counts, not only owners. Group-based access is flattened to
   members at export time, which is easy since the data is frozen.
3. **Update the Atlas Search index definition** (`fuzzy_search`) to map the new fields (token types). Rebuild
   the index.
4. **Enforce server-side.** The filter must come from the authenticated identity, never from a client
   `owner=` parameter. Add `visibility in (public, discoverable) OR access_users contains <caller>` to the
   compound filter in `SearchQuery._filters`. "Private to me" then only narrows within that.
5. Apply the same filter to `typeahead` and to any other read of the collection.
6. **Strip `access_users` from responses** (the `$lookup` returns the full document).
7. Anonymous callers see public/discoverable only.

### Authentication

OIDC (OpenID Connect) is a standard way to let users log in through a separate identity service. HydroShare
uses a Keycloak server (CUAHSI realm at `auth.cuahsi.io`) with client ID `hydroshare` and a client secret
(see [hydroshare/settings.py](../../hydroshare/settings.py#L186-L225)). The app redirects to Keycloak, receives a
code, exchanges it for a signed token and reads claims such as `preferred_username`.

- Current implementation: `mozilla_django_oidc` inside Django
  ([hs_core/authentication.py](../../hs_core/authentication.py)). It creates or matches a Django `User` row,
  calls HydroShare's `create_account` and stores a Django session in Postgres.
- It is not extractable as a unit. It needs Django's auth user model and a database for users and sessions.
  A throwaway SQLite file does not work on Cloud Run because instances and restarts would lose user rows.
- The slim app only needs the username. HydroShare already treats the `preferred_username` claim as the
  username (`filter_users_by_claims` in `hs_core/authentication.py`), so it maps directly to `access_users`
  with no database lookup.

Replacement:

1. `/login` redirects to Keycloak's authorization endpoint (state and nonce).
2. `/oidc/callback/` exchanges the code, verifies the ID token (signature via JWKS, audience, expiry, nonce)
   and sets a signed, `HttpOnly`, `Secure`, `SameSite=Lax` cookie containing the username and an expiry.
3. `/logout` clears the cookie and optionally calls the Keycloak end-session endpoint.
4. `/me` returns the current user to the SPA.

Use a framework-neutral OIDC library such as Authlib (it has FastAPI/Starlette and Django integrations).
The session is stateless, so no Redis or Cloud SQL is needed. The API is GET-only, so CSRF is not a concern.
When served on the same hostname, the slim app can reuse the existing client and its registered
`/oidc/callback/` redirect URI (confirm in Keycloak, including that the client is confidential).

Framework choice for the slim API: FastAPI (matches the repo's `hs_s3_auth` and `hs_s3_proxy` services) or a
minimal Django project without a database. FastAPI is the lean choice.

Alternative considered: an `oauth2-proxy` sidecar on Cloud Run. It avoids writing login code, but search
must work anonymously while still passing identity when logged in, and optional-auth behaviour needs a
prototype to confirm. Cloud IAP or Identity Platform federation is heavier than needed.

### Slim API

A new service, but mostly extraction of existing code, not a from-scratch search API.

**Where it lives.** In this repo, as a new top-level directory (for example `hs_discover_api/`), built as its
own image. `hs_s3_auth` is the template: its own `Dockerfile`, `requirements.txt`, `api/` and `tests/`,
FastAPI on `python:3.11` (`fastapi run api/main.py`), built from its own context in `local-dev.yml` and deployed
as a separate Cloud Run service.

The new package contains:

- `Dockerfile` and `requirements.txt` with only `fastapi`, `pymongo`, `pydantic`, an OIDC library (Authlib) and
  a cookie-signing library (`itsdangerous` or Starlette sessions). No Django, boto3, Celery, Redis or
  SQLAlchemy.
- `api/` with the search, typeahead, `/login`, `/oidc/callback/`, `/logout` and `/me` routes.
- Optionally, the built SPA served as static files from the same container (one image, one Cloud Run service).
  Otherwise the SPA stays in a bucket behind the load balancer.

**What gets ported.** `hs_rest_api/discovery_atlas.py` is mostly framework-neutral. `SearchQuery` is already a
plain pydantic model that builds the `$search` pipeline. The Django-specific parts are:

- `request.GET`, `JsonResponse`, `@api_view` and the swagger decorators
- `settings.SEARCH_BOOST_*` and the relevance score threshold (move to env-based config)
- `MongoDBClient`: do not import `hs_core.hydroshare_atlas_discovery_collection`. It creates a boto3 S3
  client at import time and reads Django settings. Write a small `pymongo` client in the new package.

**Copy, not import.** The query builder is copied into the new package, since importing from `hs_rest_api`
would pull Django into the image. The Django app is gone in this mode, so the duplication is acceptable.
Note in the repo that the two copies can drift if the full app is ever restored.

**Size.**

| Piece | Size |
|---|---|
| Port search and typeahead | S to M |
| Mongo client and config | S |
| Auth routes (see Authentication) | S to M |
| Visibility filter and response stripping (see Visibility model) | M |

Most of the effort is verifying that the ported search behaves like the existing one (test it against the same
Atlas index) and getting the visibility filter and auth right.

### Frontend

The Django theme shell goes away. The SPA is served directly with a minimal header. Required changes:

- login and logout controls and a `/me` call
- a "private to me" filter in the existing filter system (`filter.ts`)
- a private badge (an icon is already referenced in `constants.ts`)
- remove the landing-page link from search result cards

### Landing pages and DOIs

Removing the link from search results is a UI change only. The DOI target `/resource/<id>/` for published
resources must still resolve. The Vue landing page currently fetches `dataset_metadata.json` through the S3
proxy, so either keep the read-only proxy up for published resources or serve a metadata-only landing page
from the Mongo document. This is an open item.

### Deployment

- Remove Django web, workers, Companion, Redis and (with stateless auth) Cloud SQL. Keep a final DB export.
- Keep Atlas (managed) and one small Cloud Run service for the API. Keep the SPA static.
- Add secrets: OIDC client secret and the cookie signing key. Update LB routes.
- Admin data access via direct GCS IAM, or the read-only proxy if it is kept for landing pages.
- Keycloak remains an external dependency outside the Terraform.

### Level of effort

| Area | Size |
|---|---|
| OIDC login, logout, session cookie, `/me` | S to M |
| Port search and typeahead API from Django | S to M |
| Ingest enrichment, backfill, Atlas index change, server-side filter, response stripping | M |
| Frontend (header, login, private filter, remove landing links) | M |
| Terraform and routing | S to M |

Roughly half the effort is the visibility model. The auth swap is a modest add-on.

### Risks

- Private metadata is copied into Atlas, so Atlas network access and credentials need a security review.
- A filter bug is a data leak. Tests that a non-owner never sees a private document through search,
  typeahead and any detail path are a must-have even if other tests are deferred.
- Hand-rolled OIDC is easy to get subtly wrong. Use a vetted library and test state, nonce, audience and
  expiry checks. Keep the signing key in Secret Manager.
- Normalise usernames to lowercase in both the index and the claim comparison.
- Inactive or suspended accounts are unknown to the slim app (probably acceptable).
- Keycloak stays a dependency outside the Terraform.

### Open questions

- Confirm the Keycloak client configuration (confidential, redirect URIs, scopes include the claims needed).
- Should shared-with-me resources, not only owned ones, appear under "private to me"?
- Keep the read-only proxy for DOI landing pages, or render them from the Mongo document?
- Does `dataset_metadata.json` include any owner information, or must it all come from Postgres?

---

## Comparison

| | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| Owners can verify private resources | Yes | Yes, but listed for everyone | Yes, only for owners |
| Keeps current search UX | Yes | No (rebuilt) | Yes |
| Auth needed | Existing | None | Slim OIDC |
| Runs after cutover | Django web, DB, Redis, S3 services | Static hosting | API service, Atlas, static SPA |
| Cost | Highest | Lowest | Medium |
| Main risk | Many enforcement points (DRF, GET mutations) | Frontend rebuild | Visibility filter correctness |
| Reversibility | Flip a variable | Restore from DB export | Restore from DB export |

## Glossary

- **DRF**: Django REST Framework, the library used for the REST API (`rest_framework` in
  `INSTALLED_APPS`). It provides views, serializers and per-view permission classes.
- **OIDC**: OpenID Connect. A standard for logging in through a separate identity service. HydroShare uses
  Keycloak as the identity provider.
- **Keycloak**: the open-source identity server CUAHSI runs for HydroShare logins (`auth.cuahsi.io`).
- **Atlas / Atlas Search**: MongoDB Atlas, the managed MongoDB service, and its built-in text search used by
  the Discover app.
- **Parquet**: a columnar file format that tools such as DuckDB can query efficiently, including from the
  browser with HTTP range requests.
