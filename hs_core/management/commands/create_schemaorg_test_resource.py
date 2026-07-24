"""Create a metadata-rich resource for validating schema.org JSON-LD output.

Usage:
    python manage.py create_schemaorg_test_resource --username asdf
    python manage.py create_schemaorg_test_resource --username asdf --short-id abcdef1234567890abcdef1234567890
    python manage.py create_schemaorg_test_resource --username asdf --unpublished
    python manage.py create_schemaorg_test_resource --username asdf --force
"""

import io
import uuid
import datetime
import getpass
from urllib.parse import urlparse

from dateutil import tz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile

from mezzanine.pages.models import Page
from rest_framework import status
from rest_framework.test import APIClient

from hs_access_control.models import UserAccess, UserResourcePrivilege, PrivilegeCodes
from hs_core.hydroshare import create_resource
from hs_core.hydroshare.resource import get_resource_doi
from hs_core.models import BaseResource, CoreMetaData, Identifier
from hs_core.tasks import create_bag_by_s3
from theme.models import UserQuota


def _ensure_published_user(stdout):
    publisher_username = getattr(settings, "PUBLISHER_USER_NAME", "published")

    pub_user, created = User.objects.get_or_create(
        username=publisher_username,
        defaults={"email": "published@hydroshare.org", "is_active": True},
    )
    if created:
        pub_user.set_unusable_password()
        pub_user.save()
        stdout.write(f"Created '{publisher_username}' user")

    UserAccess.objects.get_or_create(user=pub_user)

    profile = pub_user.userprofile
    if not profile.bucket_name:
        profile._assign_bucket_name()
        profile.save()

    UserQuota.objects.get_or_create(user=pub_user, zone="hydroshare")
    return pub_user


def _build_test_metadata(owner, short_id):
    return [
        {
            "creator": {
                "name": "Schema Test Creator",
                "email": owner.email or "schema.creator@example.org",
                "organization": "HydroShare QA",
                "phone": "+1-435-555-0101",
                "homepage": "https://example.org/schema-creator",
                "identifiers": {"ORCID": "https://orcid.org/0000-0002-1825-0097"},
                "hydroshare_user_id": owner.id,
            }
        },
        {
            "contributor": {
                "name": "Schema Test Contributor",
                "email": "schema.contributor@example.org",
                "organization": "HydroShare QA",
                "phone": "+1-435-555-0102",
                "homepage": "https://example.org/schema-contributor",
            }
        },
        {
            "description": {
                "abstract": (
                    "Synthetic resource used to validate schema.org JSON-LD output in HydroShare. "
                    "Includes coverage, relations, funding, rights, identifiers, and file formats."
                )
            }
        },
        {
            "coverage": {
                "type": "box",
                "value": {
                    "name": "Test Bounding Box",
                    "northlimit": 42.1234,
                    "southlimit": 40.1234,
                    "eastlimit": -110.1234,
                    "westlimit": -112.1234,
                    "units": "Decimal degrees",
                    "projection": "WGS 84 EPSG:4326",
                },
            }
        },
        {
            "coverage": {
                "type": "period",
                "value": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-12-31T00:00:00Z",
                },
            }
        },
        {
            "rights": {
                "statement": "This resource is shared under the Creative Commons Attribution CC BY.",
                "url": "http://creativecommons.org/licenses/by/4.0/",
            }
        },
        {
            "fundingagency": {
                "agency_name": "National Science Foundation",
                "award_title": "Schema.org Metadata Validation",
                "award_number": "NSF-TEST-2026-0001",
                "agency_url": "https://www.nsf.gov",
            }
        },
        {
            "identifier": {
                "name": "Project URL",
                "url": f"https://example.org/projects/hydroshare-schema-validation/{short_id}",
            }
        },
        {"relation": {"type": "isPartOf", "value": "https://example.org/collections/schema-tests"}},
        {"relation": {"type": "hasPart", "value": "https://example.org/resources/schema-tests/part-1"}},
        {"relation": {"type": "source", "value": "https://example.org/data/source-dataset"}},
        {"relation": {"type": "isVersionOf", "value": "https://example.org/resources/schema-tests/v1"}},
        {"relation": {"type": "replaces", "value": "https://example.org/resources/schema-tests/v3"}},
        {"relation": {"type": "isDescribedBy", "value": "https://example.org/docs/schema-tests/description"}},
        {"relation": {"type": "isReferencedBy", "value": "https://example.org/papers/schema-tests-citation"}},
        {"relation": {"type": "references", "value": "https://example.org/standards/schema-org-dataset"}},
    ]


def _publish_without_datacite(resource, owner, published_user):
    # Transfer ownership to published user to match HydroShare published behavior.
    UserResourcePrivilege.share(
        user=published_user,
        resource=resource,
        privilege=PrivilegeCodes.OWNER,
        grantor=owner,
    )
    resource.set_quota_holder(owner, published_user)

    doi = get_resource_doi(resource.short_id)
    resource.doi = doi
    resource.save()

    resource.set_public(True)
    resource.set_published(True)
    resource.raccess.review_pending = False
    resource.raccess.save()

    if not resource.metadata.publisher:
        resource.metadata.create_element(
            "Publisher",
            name="Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)",
            url="https://www.cuahsi.org",
        )

    now = datetime.datetime.now(tz.UTC)
    resource.metadata.create_element("date", type="published", start_date=now)
    if not resource.metadata.identifiers.filter(name="doi").exists():
        resource.metadata.create_element("Identifier", name="doi", url=doi)

    # Generate bag/checksum used by distribution metadata.
    create_bag_by_s3(resource.short_id, create_zip=False)


def _create_resource_via_api(owner, title, keywords, metadata, csv_bytes, api_host, api_scheme):
    """Create a resource through the hsapi create endpoint instead of direct model call."""
    upload_file = SimpleUploadedFile(
        "schemaorg_validation_timeseries.csv", csv_bytes, content_type="text/csv"
    )

    payload = {
        "resource_type": "CompositeResource",
        "title": title,
        "keywords": keywords,
        "file": upload_file,
    }

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.post(
        "/hsapi/resource/",
        payload,
        format="multipart",
        HTTP_HOST=api_host,
        wsgi_url_scheme=api_scheme,
    )
    if response.status_code != status.HTTP_201_CREATED:
        raise CommandError(f"API resource creation failed: {response.status_code} {response.data}")

    short_id = response.data.get("resource_id")
    if not short_id:
        raise CommandError(f"API resource creation returned invalid payload: {response.data}")

    # Apply full metadata via API update endpoint so creation follows hsapi flow.
    scimeta_payload = {
        "title": title,
        "subjects": [{"value": kw} for kw in keywords],
    }
    for element in metadata:
        key, value = list(element.items())[0]
        if key == "description":
            scimeta_payload["description"] = value.get("abstract", "")
        elif key == "creator":
            scimeta_payload.setdefault("creators", []).append(value)
        elif key == "contributor":
            scimeta_payload.setdefault("contributors", []).append(value)
        elif key == "coverage":
            scimeta_payload.setdefault("coverages", []).append(value)
        elif key == "rights":
            scimeta_payload["rights"] = value
        elif key == "relation":
            scimeta_payload.setdefault("relations", []).append(value)
        elif key == "fundingagency":
            scimeta_payload.setdefault("funding_agencies", []).append(value)
        elif key == "identifier":
            scimeta_payload.setdefault("identifiers", []).append(value)

    scimeta_response = client.put(
        f"/hsapi/resource/{short_id}/scimeta/elements/",
        scimeta_payload,
        format="json",
        HTTP_HOST=api_host,
        wsgi_url_scheme=api_scheme,
    )
    if scimeta_response.status_code != status.HTTP_202_ACCEPTED:
        raise CommandError(
            f"API metadata update failed: {scimeta_response.status_code} {scimeta_response.data}"
        )

    resource = BaseResource.objects.get(short_id=short_id)
    return resource


def _create_resource_via_external_api(
    title,
    keywords,
    metadata,
    csv_bytes,
    api_base_url,
    api_username,
    api_password,
):
    """Create/update resource by making outbound HTTP calls to a live hsapi endpoint."""
    try:
        import requests
    except ImportError as exc:
        raise CommandError("The 'requests' package is required for --external-api mode") from exc

    base = api_base_url.rstrip("/")
    if base.endswith("/hsapi"):
        hsapi_base = base
    else:
        hsapi_base = f"{base}/hsapi"

    create_url = f"{hsapi_base}/resource/"
    files = {
        "file": ("schemaorg_validation_timeseries.csv", csv_bytes, "text/csv"),
    }
    data = {
        "resource_type": "CompositeResource",
        "title": title,
        "keywords": ",".join(keywords),
    }

    create_response = requests.post(
        create_url,
        auth=(api_username, api_password),
        data=data,
        files=files,
        timeout=120,
    )
    if create_response.status_code != 201:
        raise CommandError(
            "External API resource creation failed: "
            f"{create_response.status_code} {create_response.text}"
        )

    create_payload = create_response.json()
    short_id = create_payload.get("resource_id")
    if not short_id:
        raise CommandError(f"External API create payload missing resource_id: {create_payload}")

    scimeta_payload = {
        "title": title,
        "subjects": [{"value": kw} for kw in keywords],
    }
    for element in metadata:
        key, value = list(element.items())[0]
        if key == "description":
            scimeta_payload["description"] = value.get("abstract", "")
        elif key == "creator":
            scimeta_payload.setdefault("creators", []).append(value)
        elif key == "contributor":
            scimeta_payload.setdefault("contributors", []).append(value)
        elif key == "coverage":
            scimeta_payload.setdefault("coverages", []).append(value)
        elif key == "rights":
            scimeta_payload["rights"] = value
        elif key == "relation":
            scimeta_payload.setdefault("relations", []).append(value)
        elif key == "fundingagency":
            scimeta_payload.setdefault("funding_agencies", []).append(value)
        elif key == "identifier":
            scimeta_payload.setdefault("identifiers", []).append(value)

    scimeta_url = f"{hsapi_base}/resource/{short_id}/scimeta/elements/"
    scimeta_response = requests.put(
        scimeta_url,
        auth=(api_username, api_password),
        json=scimeta_payload,
        timeout=120,
    )
    if scimeta_response.status_code != 202:
        raise CommandError(
            "External API metadata update failed: "
            f"{scimeta_response.status_code} {scimeta_response.text}"
        )

    return short_id


class Command(BaseCommand):
    help = "Create a single schema.org validation resource with comprehensive metadata"

    def _ensure_local_environment(self):
        # Safety guard: this command seeds synthetic data and must not run in production-like envs.
        if not settings.DEBUG:
            raise CommandError(
                "create_schemaorg_test_resource is restricted to local/dev environments (DEBUG=True)."
            )

    @staticmethod
    def _validate_api_base_url(api_base_url):
        parsed = urlparse(api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise CommandError("--api-base-url must be a valid absolute http(s) URL")

        host = parsed.hostname
        if host not in {"localhost", "127.0.0.1"}:
            raise CommandError(
                "--api-base-url must point to localhost/127.0.0.1 for safety."
            )

        return parsed

    def add_arguments(self, parser):
        parser.add_argument("--username", default="asdf", help="Owner username (default: asdf)")
        parser.add_argument(
            "--short-id",
            default=None,
            help="Optional resource short_id (32 chars). Default generates one automatically.",
        )
        parser.add_argument(
            "--title",
            default="HydroShare schema.org validation resource",
            help="Title for the test resource",
        )
        parser.add_argument(
            "--unpublished",
            action="store_true",
            help="Create as public (not published) instead of published",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing resource if short_id already exists",
        )
        parser.add_argument(
            "--use-api",
            action="store_true",
            help="Create the resource via /hsapi/resource/ instead of direct model call",
        )
        parser.add_argument(
            "--api-base-url",
            default="https://localhost",
            help="Base URL for API mode (default: https://localhost)",
        )
        parser.add_argument(
            "--external-api",
            action="store_true",
            help="Use outbound HTTP calls to the public hsapi endpoint",
        )
        parser.add_argument(
            "--api-username",
            default=None,
            help="Basic auth username for --external-api mode",
        )
        parser.add_argument(
            "--api-password",
            default=None,
            help="Basic auth password for --external-api mode (omit to be prompted)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        short_id = options["short_id"] or uuid.uuid4().hex
        title = options["title"]
        unpublished = options["unpublished"]
        force = options["force"]
        use_api = options["use_api"]
        api_base_url = options["api_base_url"]
        external_api = options["external_api"]
        api_username = options["api_username"]
        api_password = options["api_password"]

        if not external_api:
            self._ensure_local_environment()

        if use_api and external_api:
            raise CommandError("Use only one mode: --use-api or --external-api")

        if (use_api or external_api) and (options["short_id"] or force):
            raise CommandError("--use-api cannot be combined with --short-id or --force")

        if use_api:
            parsed_api_url = self._validate_api_base_url(api_base_url)
        elif external_api:
            parsed_api_url = urlparse(api_base_url)
            if parsed_api_url.scheme not in {"http", "https"} or not parsed_api_url.netloc:
                raise CommandError("--api-base-url must be a valid absolute http(s) URL")
        else:
            parsed_api_url = None

        if len(short_id) != 32:
            raise CommandError("short_id must be exactly 32 characters")

        try:
            owner = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist")

        existing = BaseResource.objects.filter(short_id=short_id).first()
        if existing:
            if not force:
                raise CommandError(
                    f"Resource with short_id '{short_id}' already exists. Use --force to recreate."
                )
            Identifier.objects.filter(url__contains=short_id).delete()
            if existing.metadata is not None:
                existing.delete()
            else:
                Page.objects.filter(id=existing.id).delete()

        linked_metadata_ids = BaseResource.objects.values_list("object_id", flat=True)
        CoreMetaData.objects.filter(
            id__in=Identifier.objects.filter(url__contains=short_id).values_list("object_id", flat=True)
        ).exclude(id__in=linked_metadata_ids).delete()

        csv_content = (
            "site_id,date,streamflow_cfs,stage_ft,temperature_c\n"
            "QA-01,2024-01-01,120.4,3.12,11.2\n"
            "QA-01,2024-01-02,118.1,3.08,10.9\n"
            "QA-01,2024-01-03,124.7,3.21,11.5\n"
        ).encode("utf-8")
        csv_file = io.BytesIO(csv_content)
        csv_file.name = "schemaorg_validation_timeseries.csv"

        metadata = _build_test_metadata(owner, short_id)
        keywords = ["schema.org", "json-ld", "validation", "datacite", "hydroshare"]
        if external_api:
            if not api_username:
                raise CommandError("--api-username is required for --external-api mode")
            if api_password is None:
                api_password = getpass.getpass("API password: ")

            self.stdout.write(
                f"Using external API mode against {parsed_api_url.scheme}://{parsed_api_url.netloc}"
            )
            created_short_id = _create_resource_via_external_api(
                title=title,
                keywords=keywords,
                metadata=metadata,
                csv_bytes=csv_content,
                api_base_url=api_base_url,
                api_username=api_username,
                api_password=api_password,
            )
            self.stdout.write(self.style.SUCCESS("Created schema.org validation resource via external API"))
            self.stdout.write(f"  short_id: {created_short_id}")
            self.stdout.write("  state: public")
            self.stdout.write(
                f"  url: {parsed_api_url.scheme}://{parsed_api_url.netloc}/resource/{created_short_id}/"
            )
            self.stdout.write(f"  verify: {api_base_url.rstrip('/')}/resource/{created_short_id}/scimeta/elements/")
            return
        elif use_api:
            self.stdout.write(
                f"Using API mode against {parsed_api_url.scheme}://{parsed_api_url.netloc}"
            )
            resource = _create_resource_via_api(
                owner=owner,
                title=title,
                keywords=keywords,
                metadata=metadata,
                csv_bytes=csv_content,
                api_host=parsed_api_url.netloc,
                api_scheme=parsed_api_url.scheme,
            )
        else:
            resource = create_resource(
                resource_type="CompositeResource",
                owner=owner,
                title=title,
                keywords=keywords,
                metadata=metadata,
                files=(csv_file,),
                short_id=short_id,
            )

        if unpublished:
            resource.set_public(True)
            state = "public"
        else:
            published_user = _ensure_published_user(self.stdout)
            _publish_without_datacite(resource, owner, published_user)
            state = "published"

        resource.refresh_from_db()
        resource.update_cached_metadata_field(field_name="all")

        self.stdout.write(self.style.SUCCESS("Created schema.org validation resource"))
        self.stdout.write(f"  short_id: {resource.short_id}")
        self.stdout.write(f"  state: {state}")
        self.stdout.write(f"  url: https://www.hydroshare.org/resource/{resource.short_id}/")
        self.stdout.write("  verify: python manage.py check_json_ld <short_id>")
