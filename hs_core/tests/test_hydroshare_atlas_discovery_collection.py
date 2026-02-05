import json
import logging
import os
import unittest
from urllib.parse import urlparse
import uuid

import boto3
from django.conf import settings
from django.test import SimpleTestCase
from pymongo import MongoClient

from hs_core import hydroshare_atlas_discovery_collection as collector
from hs_core.enums import RelationTypes
from hs_core.models import Relation


class HydroshareAtlasDiscoveryCollectionIntegrationTests(SimpleTestCase):
    """
    Integration-level tests that exercise the Atlas collector against the real
    MongoDB/Atlas-local container and MinIO S3 endpoint configured in local-dev.yml.
    """
    # No Django DB needed
    databases = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skip_reason = None
        cls.logger = logging.getLogger(__name__)
        cls._orig_s3 = collector.s3
        cls._orig_db = collector.hydroshare_atlas_db

        cls.bucket = f"atlas-test-{uuid.uuid4().hex[:8]}"
        s3_endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None) or os.getenv("AWS_ENDPOINT_URL")
        access_key = getattr(settings, "AWS_S3_ACCESS_KEY_ID", None) or os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = getattr(settings, "AWS_S3_SECRET_ACCESS_KEY", None) or os.getenv("AWS_SECRET_ACCESS_KEY")

        if not s3_endpoint:
            cls.skip_reason = "AWS_S3_ENDPOINT_URL/AWS_ENDPOINT_URL is not configured for MinIO"
            raise unittest.SkipTest(cls.skip_reason)

        try:
            cls.s3 = boto3.client(
                "s3",
                endpoint_url=s3_endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            cls.s3.create_bucket(Bucket=cls.bucket)
        except Exception as exc:
            cls.skip_reason = f"Cannot connect to S3 endpoint {s3_endpoint}: {exc}"
            raise unittest.SkipTest(cls.skip_reason)

        try:
            cls.mongo_client = MongoClient(settings.ATLAS_CONNECTION_URL, serverSelectionTimeoutMS=3000)
            cls.mongo_client.admin.command("ping")
            cls.collection = cls.mongo_client["hydroshare"]["discovery"]
        except Exception as exc:
            cls.skip_reason = f"Cannot connect to MongoDB at {settings.ATLAS_CONNECTION_URL}: {exc}"
            raise unittest.SkipTest(cls.skip_reason)

        # Wire the collector to use the real services.
        collector.s3 = cls.s3
        collector.hydroshare_atlas_db = cls.mongo_client["hydroshare"]

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "skip_reason", None):
            cls._cleanup_s3()
            cls._cleanup_mongo()
            collector.s3 = cls._orig_s3
            collector.hydroshare_atlas_db = cls._orig_db
            super().tearDownClass()
            return

        try:
            cls._clear_bucket()
            cls.s3.delete_bucket(Bucket=cls.bucket)
        finally:
            cls._cleanup_mongo()
            collector.s3 = cls._orig_s3
            collector.hydroshare_atlas_db = cls._orig_db
            super().tearDownClass()

    def setUp(self):
        if getattr(type(self), "skip_reason", None):
            self.skipTest(type(self).skip_reason)
        self.collection.delete_many({"_s3_filepath": {"$regex": f"^{self.bucket}/"}})
        self._clear_bucket()

    def tearDown(self):
        # Remove any objects created during a test, including the seeded fixtures.
        self.collection.delete_many({"_s3_filepath": {"$regex": f"^{self.bucket}/"}})
        self._clear_bucket()

    def test_sets_first_creator_and_preserves_existing_urls(self):
        resource_id = "res-preserve"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        part_key = f"{resource_id}/.hsjsonld/part.json"

        original_url = f"https://example.org/resource/{resource_id}"
        original_identifier = f"https://example.org/landing/{resource_id}"
        has_part_url = f"https://files.test/{self.bucket}/{part_key}"

        self._put_json(
            dataset_key,
            {
                "identifier": [original_identifier],
                "url": original_url,
                "creator": [{"name": "Alice"}, {"name": "Bob"}],
                "relations": [],
                "hasPart": [{"url": has_part_url}],
            },
        )
        self._put_json(part_key, {"additionalType": "Document"})

        collector.collect_file_to_catalog(f"{self.bucket}/{dataset_key}")
        stored = self.collection.find_one({"_s3_filepath": f"{self.bucket}/{dataset_key}"})

        self.assertIsNotNone(stored)
        self.assertEqual(stored["_s3_filepath"], f"{self.bucket}/{dataset_key}")
        self.assertEqual(stored["url"], original_url)
        self.assertEqual(stored["identifier"][0], original_identifier)
        self.assertEqual(stored["first_creator"], {"name": "Alice"})
        self.assertCountEqual(stored["content_types"], ["Document"])

    def test_preserves_version_relation(self):
        resource_id = "res-version"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        part_key = f"{resource_id}/.hsjsonld/part.json"

        version_label = dict(Relation.SOURCE_TYPES)[RelationTypes.isVersionOf.value]
        self._put_json(
            dataset_key,
            {
                "identifier": [f"https://example.org/resource/{resource_id}"],
                "url": f"https://example.org/resource/{resource_id}",
                "creator": [{"name": "Alice"}],
                "relations": [{"name": version_label, "description": "old version"}],
                "hasPart": [{"url": f"https://files.test/{self.bucket}/{part_key}"}],
            },
        )
        self._put_json(part_key, {"additionalType": "Document"})

        collector.collect_file_to_catalog(f"{self.bucket}/{dataset_key}")
        stored = self.collection.find_one({"_s3_filepath": f"{self.bucket}/{dataset_key}"})

        self.assertIsNotNone(stored)
        self.assertIn(
            version_label,
            [rel.get("name") for rel in stored.get("relations", [])],
        )

    def test_content_types_handles_missing_additional_type(self):
        resource_id = "res-content-types"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        part_a = f"{resource_id}/.hsjsonld/part-a.json"
        part_b = f"{resource_id}/.hsjsonld/part-b.json"

        self._put_json(
            dataset_key,
            {
                "identifier": ["id"],
                "url": "url",
                "creator": [{"name": "first"}],
                "hasPart": [
                    {"url": f"https://files.test/{self.bucket}/{part_a}"},
                    {"url": f"https://files.test/{self.bucket}/{part_b}"},
                ],
            },
        )
        self._put_json(part_a, {"additionalType": "Raster"})
        self._put_json(part_b, {})

        collector.collect_file_to_catalog(f"{self.bucket}/{dataset_key}")
        stored = self.collection.find_one({"_s3_filepath": f"{self.bucket}/{dataset_key}"})

        self.assertIsNotNone(stored)
        self.assertSetEqual(set(stored["content_types"]), {"Raster", None})

    def test_skips_replaced_resources(self):
        resource_id = "res-replaced"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"

        self._put_json(
            dataset_key,
            {
                "identifier": [f"https://example.org/resource/{resource_id}"],
                "url": f"https://example.org/resource/{resource_id}",
                "creator": [{"name": "Alice"}],
                "relations": [{"name": "This resource has been replaced by a newer version"}],
                "hasPart": [],
            },
        )

        collector.collect_file_to_catalog(f"{self.bucket}/{dataset_key}")
        stored = self.collection.find_one({"_s3_filepath": f"{self.bucket}/{dataset_key}"})
        self.assertIsNone(stored)

    def test_collection_sample_hasparts_as_resources(self):
        """Ensure seeded collection with member resource URLs ingests and records content types."""
        resource_id = "504d9c92dfda4aa09c784db63b590a9a"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        # Seed only for this test to avoid overhead in others.
        self._seed_collection()
        stored = self.collection.find_one({"_s3_filepath": f"{self.bucket}/{dataset_key}"})

        self.assertIsNotNone(stored, "seeded collection doc should exist")
        self.assertEqual(stored["url"], f"http://localhost:8000/resource/{resource_id}")
        self.assertEqual(stored["identifier"][0], f"http://localhost:8000/resource/{resource_id}")
        self.assertEqual(stored.get("additionalType"), "CollectionResource")
        self.assertEqual(len(stored.get("hasPart", [])), 3)
        self.assertSetEqual(set(stored.get("content_types", [])), {"MemberResource"})

    def _put_json(self, key: str, payload: dict):
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )

    @classmethod
    def _clear_bucket(cls):
        try:
            token = None
            while True:
                if token:
                    response = cls.s3.list_objects_v2(Bucket=cls.bucket, ContinuationToken=token)
                else:
                    response = cls.s3.list_objects_v2(Bucket=cls.bucket)
                for obj in response.get("Contents", []):
                    cls.s3.delete_object(Bucket=cls.bucket, Key=obj["Key"])
                if not response.get("IsTruncated"):
                    break
                token = response.get("NextContinuationToken")
        except Exception:
            # Bucket may not exist if setup failed
            pass

    def _seed_collection(self):
        """Seed the bucket with a realistic collection dataset mirroring the provided sample."""
        resource_id = "504d9c92dfda4aa09c784db63b590a9a"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"

        base_url = "https://test-hydroshare-url.org"
        has_parts = [
            f"{base_url}/resource/dc721672ae8c47bd97cbb84cf7e99dbf",
            f"{base_url}/resource/2bf4091543164eea96483aec5dce349a",
            f"{base_url}/resource/64ad660f50194c888ef5d3664c00a429",
        ]

        sample_metadata = {
            "context": "https://hydroshare.org/schema",
            "type": "ScientificDataset",
            "additionalType": "CollectionResource",
            "name": "New Collection Set",
            "description": "New Collection Set" * 60,
            "url": f"{base_url}/resource/{resource_id}",
            "identifier": [f"{base_url}/resource/{resource_id}"],
            "creator": [
                {
                    "type": "Person",
                    "email": "asdf@asdf.asdf",
                    "identifier": None,
                    "affiliation": {
                        "type": "Organization",
                        "url": None,
                        "address": None,
                        "name": "asdf",
                    },
                    "name": "asdf, asdf",
                }
            ],
            "dateCreated": "2026-02-02 05:17:24.034815+00:00",
            "keywords": ["ll", "co", "we"],
            "license": {
                "type": "CreativeWork",
                "name": "This resource is shared under the Creative Commons Attribution CC BY.",
                "description": None,
                "url": "http://creativecommons.org/licenses/by/4.0/",
            },
            "provider": {
                "type": "Organization",
                "url": "https://www.hydroshare.org/",
                "address": None,
                "name": "HydroShare",
            },
            "contributor": [],
            "publisher": None,
            "datePublished": None,
            "subjectOf": None,
            "version": None,
            "inLanguage": "eng",
            "creativeWorkStatus": {
                "type": "DefinedTerm",
                "name": "Discoverable",
                "description": (
                    "The resource is discoverable and can be found through search engines "
                    "or other discovery mechanisms"
                ),
            },
            "dateModified": "2026-02-02 05:18:25.686481+00:00",
            "funding": [],
            "temporalCoverage": None,
            "spatialCoverage": {
                "type": "Place",
                "name": None,
                "geo": {
                    "type": "GeoShape",
                    "box": "74.87367763620553 178.80173048092004 24.77967763620552 -39.95226951907995",
                },
                "additionalProperty": None,
                "srs": None,
            },
            "hasPart": [{"type": "CreativeWork", "name": None, "description": None, "url": url} for url in has_parts],
            "isPartOf": [],
            "relation": [
                (
                    "annotation=NoneType required=False default=None title='Relation' "
                    "description='All other types of relations'"
                )
            ],
            "additionalProperty": None,
            "associatedMedia": [],
            "citation": [
                f"asdf, a. (2026). New Collection Set, HydroShare, {base_url}/resource/{resource_id}"
            ],
            "coordinates": None,
            "includedInDataCatalog": None,
            "sourceOrganization": None,
            "sharing_status": None,
            "additional_metadata": {},
            "relations": [
                {
                    "type": "CreativeWork",
                    "name": "This resource includes",
                    "description": "member 1",
                    "url": has_parts[0],
                },
                {
                    "type": "CreativeWork",
                    "name": "This resource includes",
                    "description": "member 2",
                    "url": has_parts[1],
                },
                {
                    "type": "CreativeWork",
                    "name": "This resource includes",
                    "description": "member 3",
                    "url": has_parts[2],
                },
            ],
        }

        self._put_json(dataset_key, sample_metadata)

        for url in has_parts:
            part_key = "/".join(urlparse(url).path.split("/")[2:])
            self._put_json(part_key, {"additionalType": "MemberResource"})

        collector.collect_file_to_catalog(f"{self.bucket}/{dataset_key}")

    @classmethod
    def _cleanup_s3(cls):
        try:
            if getattr(cls, "s3", None) and getattr(cls, "bucket", None):
                cls.logger.info(f"cleanup: clearing bucket {cls.bucket}")
                cls._clear_bucket()
                cls.logger.info(f"cleanup: deleting bucket {cls.bucket}")
                cls.s3.delete_bucket(Bucket=cls.bucket)
            if getattr(cls, "s3", None) and hasattr(cls.s3, "close"):
                cls.logger.info("cleanup: closing s3 client")
                cls.s3.close()
        except Exception as e:
            cls.logger.warning(f"cleanup: s3 cleanup failed: {e}")

    @classmethod
    def _cleanup_mongo(cls):
        try:
            if getattr(cls, "collection", None) is not None:
                cls.logger.info(f"cleanup: deleting mongo docs for bucket {cls.bucket}")
                cls.collection.delete_many({"_s3_filepath": {"$regex": f"^{cls.bucket}/"}})
            if getattr(cls, "mongo_client", None) is not None:
                cls.logger.info("cleanup: closing mongo client")
                cls.mongo_client.close()
        except Exception as e:
            cls.logger.warning(f"cleanup: mongo cleanup failed: {e}")
