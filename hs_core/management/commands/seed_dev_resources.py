"""
Seed the local dev database with example resources for testing.

Creates:
  - 5 public (not published) Resources
  - 5 published Resources

Each resource contains a small synthetic hydrologic CSV dataset.
All resources are owned by the specified user (default: asdf).

Usage:
    docker exec hydroshare python manage.py seed_dev_resources
    docker exec hydroshare python manage.py seed_dev_resources --username myuser
    docker exec hydroshare python manage.py seed_dev_resources --force  # re-create if exists
"""

import io
import random
import datetime

from dateutil import tz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from pymongo import MongoClient

from mezzanine.pages.models import Page

from hs_access_control.models import UserAccess, UserResourcePrivilege, PrivilegeCodes
from hs_core.hydroshare import create_resource
from hs_core.hydroshare.resource import get_resource_doi
from hs_core.hydroshare_atlas_discovery_collection import collect_file_to_catalog
from hs_core.models import BaseResource, CoreMetaData, Identifier
from hs_core.tasks import create_bag_by_s3
from theme.models import UserQuota


# ---------------------------------------------------------------------------
# Fixed short_ids — deterministic so URLs are consistent across resets.
# ---------------------------------------------------------------------------
PUBLIC_SHORT_IDS = [
    f"aaaa{'0' * 27}{i}" for i in range(1, 6)
]
PUBLISHED_SHORT_IDS = [
    f"bbbb{'0' * 27}{i}" for i in range(1, 6)
]

# ---------------------------------------------------------------------------
# Shared author / org for all seed resources.
# ---------------------------------------------------------------------------
AUTHOR_NAME = "Jordan Rivers"
AUTHOR_ORG = "Center for Watershed Science"
AUTHOR_EMAIL = "jrivers@example.edu"

# ---------------------------------------------------------------------------
# Per-resource metadata pools — indexed 0–4.
# ---------------------------------------------------------------------------
TITLES = [
    "Streamflow and Water Quality Observations: Flint River Headwaters",
    "Wetland Hydrodynamics Dataset: Alapaha River Basin",
    "Seasonal Discharge Records: Withlacoochee River Tributaries",
    "Groundwater-Surface Water Exchange: Suwannee River Corridor",
    "Precipitation and Runoff Monitoring: Satilla River Watershed",
]

ABSTRACTS = [
    ("Continuous streamflow, stage, and water quality measurements collected at five monitoring "
     "stations in the Flint River headwaters region of southwestern Georgia. Data span water "
     "years 2018–2022 and include discharge, specific conductance, dissolved oxygen, turbidity, "
     "pH, and water temperature. Measurements were obtained using YSI multiparameter sondes "
     "and USGS stage-discharge rating curves."),
    ("Time-series observations of water level, inundation extent, and water quality parameters "
     "from wetland complexes within the Alapaha River Basin. Dataset supports analysis of "
     "hydroperiod dynamics, nutrient cycling, and wetland-stream connectivity under variable "
     "rainfall conditions. Sampling conducted monthly from April 2019 through March 2023."),
    ("Discharge and water quality records from three ungauged tributaries to the Withlacoochee "
     "River in north-central Florida. Measurements collected during high-flow and low-flow "
     "periods to characterize seasonal variability. Includes grab samples for nutrients and "
     "continuous sensor data for temperature, dissolved oxygen, and specific conductance."),
    ("Field measurements characterizing hyporheic exchange and groundwater contributions to "
     "baseflow along a 12 km reach of the Suwannee River. Tracer injection experiments, "
     "piezometer networks, and streambed temperature profiles were used to quantify lateral "
     "and vertical exchange fluxes. Data collected summers 2020 and 2021."),
    ("Rainfall, overland flow, and channel discharge observations from an instrumented "
     "headwater catchment in the Satilla River watershed. Dataset includes 15-minute "
     "precipitation totals, soil moisture profiles, and streamflow at catchment outlet. "
     "Intended to support event-scale rainfall-runoff modeling and regionalization studies."),
]

KEYWORDS_POOL = [
    ["streamflow", "water quality", "Georgia", "Flint River", "dissolved oxygen"],
    ["wetlands", "hydroperiod", "Alapaha", "water level", "nutrient cycling"],
    ["discharge", "tributaries", "Withlacoochee", "Florida", "baseflow"],
    ["groundwater", "hyporheic zone", "Suwannee", "tracer experiment", "exchange flux"],
    ["precipitation", "runoff", "Satilla River", "soil moisture", "rainfall-runoff"],
]

# (northlimit, southlimit, eastlimit, westlimit) — southeastern US bounding boxes
BBOXES = [
    (31.35, 31.20, -84.40, -84.60),
    (31.10, 30.90, -83.20, -83.50),
    (29.10, 28.75, -82.40, -82.70),
    (30.40, 30.10, -82.90, -83.20),
    (31.00, 30.75, -82.00, -82.30),
]

# (start, end) for temporal coverage
TIME_PERIODS = [
    ("2018-10-01", "2022-09-30"),
    ("2019-04-01", "2023-03-31"),
    ("2020-06-01", "2022-05-31"),
    ("2020-06-15", "2021-08-31"),
    ("2019-01-01", "2022-12-31"),
]

# ---------------------------------------------------------------------------
# Synthetic CSV generation
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "site_id",
    "date",
    "streamflow_cfs",
    "stage_ft",
    "precipitation_in",
    "temperature_c",
    "dissolved_oxygen_mg_l",
    "specific_conductance_uS_cm",
    "turbidity_NTU",
    "ph"
]

SITE_IDS = ["WS-01", "WS-02", "WS-03", "WS-04", "WS-05"]


def _generate_csv(resource_index):
    """Return CSV bytes for a synthetic 20-row hydrologic dataset."""
    rng = random.Random(resource_index * 1337 + 42)

    base_date = datetime.date(2020, 1, 1) + datetime.timedelta(days=resource_index * 30)

    buf = io.StringIO()
    buf.write(",".join(CSV_COLUMNS) + "\n")

    for row in range(20):
        site = SITE_IDS[row % len(SITE_IDS)]
        date = base_date + datetime.timedelta(days=row * 7)
        streamflow = round(rng.uniform(5.0, 500.0), 3)
        stage = round(rng.uniform(0.5, 8.0), 3)
        precip = round(rng.uniform(0.0, 3.5), 3)
        temp = round(rng.uniform(8.0, 28.0), 2)
        do = round(rng.uniform(5.0, 12.0), 2)
        cond = round(rng.uniform(80.0, 400.0), 1)
        turb = round(rng.uniform(0.5, 50.0), 2)
        ph = round(rng.uniform(6.2, 8.5), 2)
        buf.write(
            f"{site},{date},{streamflow},{stage},{precip},{temp},{do},{cond},{turb},{ph}\n"
        )

    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Published-user bootstrap
# ---------------------------------------------------------------------------

def _ensure_published_user(stdout):
    publisher_username = getattr(settings, "PUBLISHER_USER_NAME", "published")

    pub_user, created = User.objects.get_or_create(
        username=publisher_username,
        defaults={"email": "published@hydroshare.org", "is_active": True},
    )
    if created:
        pub_user.set_unusable_password()
        pub_user.save()
        stdout.write(f"  Created '{publisher_username}' user")
    else:
        stdout.write(f"  '{publisher_username}' user already exists")

    UserAccess.objects.get_or_create(user=pub_user)

    profile = pub_user.userprofile
    if not profile.bucket_name:
        profile._assign_bucket_name()
        profile.save()
        stdout.write(f"  Assigned bucket_name='{profile.bucket_name}' to '{publisher_username}'")

    UserQuota.objects.get_or_create(user=pub_user, zone="hydroshare")

    return pub_user


# ---------------------------------------------------------------------------
# Resource creation helpers
# ---------------------------------------------------------------------------

def _stagger_dates(resource, index):
    """Back-date created/modified so resources have distinct, sortable timestamps.

    Index 0 = oldest (8 days ago), index 4 = most recent (today).
    Updates the Date metadata elements, the Mezzanine Page.updated field, and
    the cached_metadata JSON field so all date sources are consistent.
    """
    offset = datetime.timedelta(days=(4 - index) * 2)
    backdated = datetime.datetime.now(tz.UTC) - offset

    # 1. Update Date metadata elements (hs_core_date table)
    resource.metadata.dates.filter(type__in=("created", "modified")).update(start_date=backdated)

    # 2. Update Mezzanine Page fields (used as fallback in cached_metadata and for display)
    Page.objects.filter(id=resource.id).update(updated=backdated, publish_date=backdated)

    # 3. Sync cached_metadata JSON from the updated Date elements
    resource.refresh_from_db()
    resource.update_cached_metadata_field(field_name='all')


def _base_metadata(owner, index):
    bbox = BBOXES[index]
    period = TIME_PERIODS[index]
    return [
        {
            "creator": {
                "name": AUTHOR_NAME,
                "email": AUTHOR_EMAIL,
                "organization": AUTHOR_ORG,
                "hydroshare_user_id": owner.id,
            }
        },
        {
            "description": {
                "abstract": ABSTRACTS[index]
            }
        },
        {
            "coverage": {
                "type": "box",
                "value": {
                    "northlimit": bbox[0],
                    "southlimit": bbox[1],
                    "eastlimit": bbox[2],
                    "westlimit": bbox[3],
                    "units": "Decimal degrees",
                    "name": TITLES[index],
                }
            }
        },
        {
            "coverage": {
                "type": "period",
                "value": {
                    "start": period[0],
                    "end": period[1]
                }
            }
        }
    ]


def _create_public_resource(owner, index, short_id, stdout):
    """Create a public (unpublished) resource."""
    csv_bytes = _generate_csv(index)
    csv_file = io.BytesIO(csv_bytes)
    csv_file.name = f"streamflow_data_{index + 1:02d}.csv"

    # Clean up any orphaned CoreMetaData from a previous partial run. BaseResource.delete() does
    # not cascade to CoreMetaData (GFK relationship), so it may be left behind with its child
    # elements (Identifier, Publisher, Date, etc.). Deleting CoreMetaData cascades via
    # GenericRelation to all of those.
    linked_metadata_ids = BaseResource.objects.values_list('object_id', flat=True)
    CoreMetaData.objects.filter(
        id__in=Identifier.objects.filter(url__contains=short_id).values_list('object_id', flat=True)
    ).exclude(id__in=linked_metadata_ids).delete()

    resource = create_resource(
        resource_type="CompositeResource",
        owner=owner,
        title=TITLES[index],
        keywords=KEYWORDS_POOL[index],
        metadata=_base_metadata(owner, index),
        files=(csv_file,),
        short_id=short_id,
    )

    resource.set_public(True)

    _stagger_dates(resource, index)
    stdout.write(f"  Created public resource {short_id}: {TITLES[index][:50]}…")
    return resource


def _create_published_resource(owner, published_user, index, short_id, stdout):
    """Create a fully published resource, bypassing DataCite."""
    csv_bytes = _generate_csv(index + 5)  # different seed from public resources
    csv_file = io.BytesIO(csv_bytes)
    csv_file.name = f"streamflow_data_published_{index + 1:02d}.csv"

    title = TITLES[index] + " (Published)"

    # Clean up any orphaned CoreMetaData from a previous partial run.
    linked_metadata_ids = BaseResource.objects.values_list('object_id', flat=True)
    CoreMetaData.objects.filter(
        id__in=Identifier.objects.filter(url__contains=short_id).values_list('object_id', flat=True)
    ).exclude(id__in=linked_metadata_ids).delete()

    resource = create_resource(
        resource_type="CompositeResource",
        owner=owner,
        title=title,
        keywords=KEYWORDS_POOL[index],
        metadata=_base_metadata(owner, index),
        files=(csv_file,),
        short_id=short_id,
    )

    # --- Transfer ownership to published user ---
    UserResourcePrivilege.share(
        user=published_user,
        resource=resource,
        privilege=PrivilegeCodes.OWNER,
        grantor=owner,
    )
    resource.set_quota_holder(owner, published_user)

    # --- Set publish state directly (no DataCite call) ---
    doi = get_resource_doi(short_id)
    resource.doi = doi
    resource.save()

    resource.set_public(True)
    resource.set_published(True)
    resource.raccess.review_pending = False
    resource.raccess.save()

    # --- Publish metadata elements ---
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

    # --- Generate bag (creates .hsjsonld/dataset_metadata.json in MinIO) ---
    _stagger_dates(resource, index)
    stdout.write(f"  Generating bag for {short_id}…")
    create_bag_by_s3(short_id, create_zip=False)

    # --- Index into MongoDB directly and verify ---
    bucket = published_user.userprofile.bucket_name
    filepath = f"{bucket}/{short_id}/.hsjsonld/dataset_metadata.json"
    try:
        collect_file_to_catalog(filepath)
        mongo_client = MongoClient(settings.ATLAS_CONNECTION_URL)
        db = mongo_client[settings.ATLAS_DB_NAME]
        object_key = f"{short_id}/.hsjsonld/dataset_metadata.json"
        doc = db["discovery"].find_one({"_s3_filepath": object_key})
        if doc:
            stdout.write(f"  ✓ Indexed in MongoDB: {short_id}")
        else:
            stdout.write(f"  ✗ WARNING: MongoDB document not found for {short_id}")
        mongo_client.close()
    except Exception as e:
        stdout.write(f"  ✗ WARNING: MongoDB indexing failed for {short_id}: {e}")

    stdout.write(f"  Created published resource {short_id}: {title[:50]}…")
    return resource


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed the local dev database with example public and published resources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="asdf",
            help="Username of the resource owner (default: asdf)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and re-create seed resources if they already exist",
        )

    def handle(self, *args, **options):
        username = options["username"]
        force = options["force"]

        try:
            owner = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist. Create it first.")

        self.stdout.write("\n=== Ensuring 'published' system user exists ===")
        published_user = _ensure_published_user(self.stdout)

        self.stdout.write("\n=== Creating public (not published) resources ===")
        for i, short_id in enumerate(PUBLIC_SHORT_IDS):
            if BaseResource.objects.filter(short_id=short_id).exists():
                if force:
                    self.stdout.write(f"  --force: deleting existing resource {short_id}")
                    Identifier.objects.filter(url__contains=short_id).delete()
                    res = BaseResource.objects.get(short_id=short_id)
                    if res.metadata is not None:
                        res.delete()
                    else:
                        # metadata already gone (partial prev run); delete page row directly
                        Page.objects.filter(id=res.id).delete()
                else:
                    self.stdout.write(f"  Skipping {short_id} (already exists; use --force to recreate)")
                    continue
            _create_public_resource(owner, i, short_id, self.stdout)

        self.stdout.write("\n=== Creating published resources ===")
        for i, short_id in enumerate(PUBLISHED_SHORT_IDS):
            if BaseResource.objects.filter(short_id=short_id).exists():
                if force:
                    self.stdout.write(f"  --force: deleting existing resource {short_id}")
                    Identifier.objects.filter(url__contains=short_id).delete()
                    res = BaseResource.objects.get(short_id=short_id)
                    if res.metadata is not None:
                        res.delete()
                    else:
                        Page.objects.filter(id=res.id).delete()
                else:
                    self.stdout.write(f"  Skipping {short_id} (already exists; use --force to recreate)")
                    continue
            _create_published_resource(owner, published_user, i, short_id, self.stdout)

        self.stdout.write("\n=== Seed complete ===")
        self.stdout.write("Public resource URLs:")
        for sid in PUBLIC_SHORT_IDS:
            self.stdout.write(f"  http://localhost/resource/{sid}/")
        self.stdout.write("Published resource URLs:")
        for sid in PUBLISHED_SHORT_IDS:
            self.stdout.write(f"  http://localhost/resource/{sid}/")
        self.stdout.write("")
