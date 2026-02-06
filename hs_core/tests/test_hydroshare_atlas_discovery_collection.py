import json
import logging
import os
import time
import unittest

import boto3
from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TransactionTestCase
from pymongo import MongoClient

from hs_core import hydroshare
from hs_core import hydroshare_atlas_discovery_collection as collector
from hs_core.hydroshare.utils import current_site_url

logger = logging.getLogger(__name__)

_POLL_TIMEOUT_SEC = 10
_POLL_INTERVAL_SEC = 0.3


def _poll_mongo_for_doc(collection, filter_dict, expect_exists, timeout=_POLL_TIMEOUT_SEC):
    """Poll Mongo until doc exists or does not exist, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        doc = collection.find_one(filter_dict)
        if expect_exists and doc is not None:
            return doc
        if not expect_exists and doc is None:
            return True
        time.sleep(_POLL_INTERVAL_SEC)
    if expect_exists:
        raise AssertionError(
            f"Document matching {filter_dict} did not appear in discovery collection within {timeout}s"
        )
    doc = collection.find_one(filter_dict)
    if doc is not None:
        raise AssertionError(
            f"Document matching {filter_dict} should have been removed from discovery collection within {timeout}s"
        )
    return True


class TestAtlasDiscoveryE2E(TransactionTestCase):
    """E2E discovery tests: Django models, set_public triggers indexing, Mongo validation."""

    databases = "__all__"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._orig_s3 = collector.s3
        cls._orig_db = collector.hydroshare_atlas_db

        allow_skip = os.environ.get("ALLOW_ATLAS_INTEGRATION_SKIP", "").strip() == "1"
        s3_endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None) or os.getenv("AWS_ENDPOINT_URL")
        access_key = getattr(settings, "AWS_S3_ACCESS_KEY_ID", None) or os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = getattr(settings, "AWS_S3_SECRET_ACCESS_KEY", None) or os.getenv("AWS_SECRET_ACCESS_KEY")

        if not s3_endpoint and allow_skip:
            raise unittest.SkipTest("AWS_S3_ENDPOINT_URL not configured; ALLOW_ATLAS_INTEGRATION_SKIP=1")
        if not s3_endpoint:
            raise AssertionError(
                "AWS_S3_ENDPOINT_URL/AWS_ENDPOINT_URL is not configured; required for E2E discovery tests"
            )

        try:
            cls.s3_client = boto3.client(
                "s3",
                endpoint_url=s3_endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
        except Exception as exc:
            if allow_skip:
                raise unittest.SkipTest(f"Cannot create S3 client: {exc}")
            raise

        try:
            cls.mongo_client = MongoClient(
                settings.ATLAS_CONNECTION_URL, serverSelectionTimeoutMS=3000
            )
            cls.mongo_client.admin.command("ping")
            cls.discovery_collection = cls.mongo_client["hydroshare"]["discovery"]
        except Exception as exc:
            if allow_skip:
                raise unittest.SkipTest(f"Cannot connect to MongoDB: {exc}")
            raise

        collector.s3 = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        collector.hydroshare_atlas_db = cls.mongo_client["hydroshare"]

    @classmethod
    def tearDownClass(cls):
        collector.s3 = cls._orig_s3
        collector.hydroshare_atlas_db = cls._orig_db
        if getattr(cls, "mongo_client", None):
            cls.mongo_client.close()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "discovery_test@example.com",
            username=f"discovery_test_{id(self)}",
            first_name="Discovery",
            last_name="Tester",
            superuser=False,
            groups=[self.group],
        )
        self.resources_to_delete = []

    def tearDown(self):
        for res_id in self.resources_to_delete:
            try:
                hydroshare.delete_resource(res_id)
            except Exception as e:
                logger.warning("tearDown: failed to delete resource %s: %s", res_id, e)
        for res_id in self.resources_to_delete:
            self.discovery_collection.delete_many(
                {"_s3_filepath": {"$regex": f".*/{res_id}/.hsjsonld/dataset_metadata.json"}}
            )
        if getattr(self, "user", None):
            try:
                self.user.uaccess.delete()
                self.user.delete()
            except Exception as exc:
                logger.warning("tearDown: user cleanup failed: %s", exc)
        super().tearDown()

    def _stage_hsjsonld(self, resource, creator=None, relations=None, has_part_parts=None):
        """Stage .hsjsonld/dataset_metadata.json and part JSONs in S3 (simulates extractor output)."""
        bucket = resource.quota_holder.userprofile.bucket_name
        resource_id = resource.short_id
        base_url = current_site_url()
        res_url = f"{base_url}/resource/{resource_id}"

        try:
            self.s3_client.head_bucket(Bucket=bucket)
        except Exception:
            self.s3_client.create_bucket(Bucket=bucket)

        creators = creator if creator is not None else [{"name": f"{self.user.first_name} {self.user.last_name}"}]
        relations = relations or []
        has_part_parts = has_part_parts or [{"additionalType": "Raster"}]

        s3_endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None) or os.getenv("AWS_ENDPOINT_URL")
        has_parts = []
        for i, part in enumerate(has_part_parts):
            part_key = f"{resource_id}/.hsjsonld/part_{i}.json"
            part_url = f"{s3_endpoint.rstrip('/')}/{bucket}/{part_key}"
            has_parts.append({"url": part_url})
            part_body = json.dumps(part).encode("utf-8")
            self.s3_client.put_object(
                Bucket=bucket,
                Key=part_key,
                Body=part_body,
                ContentType="application/json",
            )

        dataset = {
            "identifier": [res_url],
            "url": res_url,
            "creator": creators,
            "relations": relations,
            "hasPart": has_parts,
        }

        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        self.s3_client.put_object(
            Bucket=bucket,
            Key=dataset_key,
            Body=json.dumps(dataset).encode("utf-8"),
            ContentType="application/json",
        )

    def test_happy_path_indexing(self):
        """Create resource, stage .hsjsonld, set_public -> discovery doc in Mongo with expected fields."""
        raster_path = "hs_core/tests/data/cea.tif"
        with open(raster_path, "rb") as f:
            res = hydroshare.create_resource(
                "CompositeResource",
                self.user,
                "Discovery Happy Path Resource",
                files=(f,),
                keywords=("test", "discovery"),
                metadata=[{"description": {"abstract": "Test abstract for discovery"}}],
            )
        self.resources_to_delete.append(res.short_id)

        self._stage_hsjsonld(res, has_part_parts=[{"additionalType": "GeographicRaster"}])

        res.set_public(True, user=self.user)

        doc = _poll_mongo_for_doc(
            self.discovery_collection,
            {"_s3_filepath": {"$regex": f".*/{res.short_id}/.hsjsonld/dataset_metadata.json"}},
            expect_exists=True,
        )
        base_url = current_site_url()
        self.assertEqual(doc["url"], f"{base_url}/resource/{res.short_id}")
        self.assertEqual(doc["identifier"][0], f"{base_url}/resource/{res.short_id}")
        self.assertEqual(doc["first_creator"]["name"], f"{self.user.first_name} {self.user.last_name}")
        self.assertIn("GeographicRaster", doc.get("content_types", []))

    def test_access_toggle_removes_from_discovery(self):
        """Discoverable -> doc appears; not discoverable -> doc removed. Skips when Haystack delete path unavailable."""
        if getattr(settings, "DISABLE_HAYSTACK", False):
            raise unittest.SkipTest("Haystack disabled; delete path not executed")
        connections = getattr(settings, "HAYSTACK_CONNECTIONS", None) or {}
        if not connections:
            raise unittest.SkipTest("No Haystack connections; delete path not executed")
        try:
            from haystack.routers import DefaultRouter
        except ImportError:
            raise unittest.SkipTest("Haystack routers unavailable; delete path not executed")

        with open("hs_core/tests/data/test.txt", "rb") as f:
            res = hydroshare.create_resource(
                "CompositeResource",
                self.user,
                "Toggle Test Resource",
                files=(f,),
                keywords=("test",),
                metadata=[{"description": {"abstract": "Toggle test"}}],
            )
        self.resources_to_delete.append(res.short_id)

        if not DefaultRouter().for_write(instance=res):
            raise unittest.SkipTest("No Haystack backends; delete path not executed")

        self._stage_hsjsonld(res, has_part_parts=[{"additionalType": "Document"}])
        res.set_discoverable(True, user=self.user)

        _poll_mongo_for_doc(
            self.discovery_collection,
            {"_s3_filepath": {"$regex": f".*/{res.short_id}/.hsjsonld/dataset_metadata.json"}},
            expect_exists=True,
        )

        res.set_discoverable(False, user=self.user)

        _poll_mongo_for_doc(
            self.discovery_collection,
            {"_s3_filepath": {"$regex": f".*/{res.short_id}/.hsjsonld/dataset_metadata.json"}},
            expect_exists=False,
        )

    def test_replaced_resource_excluded_from_discovery(self):
        """Resource with 'replaced by newer version' relation must not appear in discovery."""
        with open("hs_core/tests/data/test.txt", "rb") as f:
            res = hydroshare.create_resource(
                "CompositeResource",
                self.user,
                "Replaced Resource",
                files=(f,),
                keywords=("test",),
                metadata=[{"description": {"abstract": "Replaced"}}],
            )
        self.resources_to_delete.append(res.short_id)

        self._stage_hsjsonld(
            res,
            relations=[{"name": "This resource has been replaced by a newer version"}],
        )
        res.set_public(True, user=self.user)

        _poll_mongo_for_doc(
            self.discovery_collection,
            {"_s3_filepath": {"$regex": f".*/{res.short_id}/.hsjsonld/dataset_metadata.json"}},
            expect_exists=False,
        )

    def test_mixed_haspart_content_types(self):
        """Mixed hasPart: some parts have additionalType, some do not. Verifies content_types derivation."""
        with open("hs_core/tests/data/test.txt", "rb") as f:
            res = hydroshare.create_resource(
                "CompositeResource",
                self.user,
                "Mixed HasPart Resource",
                files=(f,),
                keywords=("test",),
                metadata=[{"description": {"abstract": "Mixed hasPart"}}],
            )
        self.resources_to_delete.append(res.short_id)

        self._stage_hsjsonld(
            res,
            has_part_parts=[
                {"additionalType": "Raster"},
                {},
                {"additionalType": "Document"},
            ],
        )
        res.set_public(True, user=self.user)

        doc = _poll_mongo_for_doc(
            self.discovery_collection,
            {"_s3_filepath": {"$regex": f".*/{res.short_id}/.hsjsonld/dataset_metadata.json"}},
            expect_exists=True,
        )

        content_types = doc.get("content_types", [])
        self.assertIn("Raster", content_types)
        self.assertIn("Document", content_types)
