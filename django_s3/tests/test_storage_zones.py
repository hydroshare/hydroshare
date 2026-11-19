import os
import tempfile
from cryptography.fernet import Fernet, InvalidToken
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase, override_settings

from django_s3.admin import StorageZoneForm
from django_s3.internal_views import zone_configuration
from django_s3.models import StorageZone
from django_s3.settings import (
    get_default_zone_config,
    get_default_zone_name,
    get_resource_s3_zones_config,
    get_zone_config,
)


def clear_caches():
    for function in (get_default_zone_config, get_default_zone_name,
                     get_resource_s3_zones_config, get_zone_config):
        function.cache_clear()


LOCAL_ZONES = {
    name: {
        "bucket_name": bucket,
        "alias": alias,
        "aws_s3_endpoint_url": "http://minio:9000",
        "aws_s3_endpoint_url_public": "http://localhost:9000",
        "aws_access_key_id": "cuahsi",
        "aws_secret_access_key": "devpassword",
    }
    for name, bucket, alias in (
        ("hydroshare", "resource", "res"),
        ("published", "published", ""),
        ("ciroh", "ciroh", ""),
    )
}


class StorageZoneTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        key_path = os.path.join(self.directory.name, "key")
        self.token_path = os.path.join(self.directory.name, "token")
        with open(key_path, "wb") as file:
            file.write(Fernet.generate_key())
        with open(self.token_path, "w", encoding="utf-8") as file:
            file.write("test-token")
        self.settings_override = override_settings(
            S3_ZONES_DATABASE_ENABLED=True,
            S3_ZONE_ENCRYPTION_KEY_FILE=key_path,
            S3_ZONE_API_TOKEN_FILE=self.token_path,
            RESOURCE_S3_DEFAULT_ZONE="hydroshare",
            RESOURCE_S3_ZONES_CONFIG=LOCAL_ZONES,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        clear_caches()
        self.addCleanup(clear_caches)

    def test_seed_encrypts_and_disables_snapshot_zones(self):
        imported = StorageZone(
            name="other", bucket_name="other", endpoint="https://production.example",
            public_endpoint="https://production.example", access_key="prod",
            encrypted_secret=b"not-the-local-key",
        )
        imported.save()
        call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        imported.refresh_from_db()
        self.assertFalse(imported.enabled)
        zone = StorageZone.objects.get(name="hydroshare")
        self.assertNotIn(b"devpassword", bytes(zone.encrypted_secret))
        self.assertEqual(zone.get_secret(), "devpassword")
        self.assertEqual(get_zone_config("hydroshare").bucket_name, "resource")
        self.assertNotIn("other", get_resource_s3_zones_config().resource_s3_zones_config)

    def test_snapshot_encrypted_with_another_key_fails_closed(self):
        zone = StorageZone(
            name="hydroshare", bucket_name="resource", endpoint="https://production.example",
            public_endpoint="https://production.example", access_key="prod",
            encrypted_secret=Fernet(Fernet.generate_key()).encrypt(b"production-secret"),
        )
        zone.save()
        with self.assertRaises(InvalidToken):
            get_resource_s3_zones_config()

    def test_internal_endpoint_requires_token_and_disables_caching(self):
        call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        factory = RequestFactory()
        response = zone_configuration(factory.get("/_internal/s3-zones/"))
        self.assertEqual(response.status_code, 403)
        response = zone_configuration(factory.get(
            "/_internal/s3-zones/", HTTP_AUTHORIZATION="Bearer test-token"
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"devpassword", response.content)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_admin_form_keeps_existing_secret_and_rejects_rebinding(self):
        call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        zone = StorageZone.objects.get(name="hydroshare")
        data = {
            "name": zone.name, "bucket_name": zone.bucket_name, "alias": zone.alias,
            "endpoint": zone.endpoint, "public_endpoint": zone.public_endpoint,
            "access_key": zone.access_key, "region": zone.region, "copy_method": zone.copy_method,
            "multipart_copy_threshold": zone.multipart_copy_threshold,
            "enabled": True, "secret_key": "",
        }
        form = StorageZoneForm(data, instance=zone)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(zone.get_secret(), "devpassword")
        data["bucket_name"] = "different"
        self.assertFalse(StorageZoneForm(data, instance=zone).is_valid())

    def test_seed_requires_explicit_confirmation(self):
        with self.assertRaises(CommandError):
            call_command("seed_local_s3_zones")

    def test_seed_uses_original_configuration(self):
        config = {**LOCAL_ZONES, "hydroshare": {
            **LOCAL_ZONES["hydroshare"], "aws_access_key_id": "another-key",
            "aws_secret_access_key": "another-secret", "region": "local-region",
            "copy_method": "managed_copy", "multipart_copy_threshold": 12345,
        }}
        with override_settings(RESOURCE_S3_ZONES_CONFIG=config):
            call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        zone = StorageZone.objects.get(name="hydroshare")
        self.assertEqual(zone.access_key, "another-key")
        self.assertEqual(zone.get_secret(), "another-secret")
        self.assertEqual(zone.region, "local-region")
        self.assertEqual(zone.copy_method, "managed_copy")
        self.assertEqual(zone.multipart_copy_threshold, 12345)

    def test_seed_rejects_non_local_endpoint_before_disabling_imported_zones(self):
        imported = StorageZone.objects.create(
            name="other", bucket_name="other", endpoint="https://production.example",
            public_endpoint="https://production.example", access_key="prod",
            encrypted_secret=b"snapshot",
        )
        config = {**LOCAL_ZONES, "hydroshare": {
            **LOCAL_ZONES["hydroshare"], "aws_s3_endpoint_url": "https://production.example"
        }}
        with override_settings(RESOURCE_S3_ZONES_CONFIG=config), self.assertRaises(CommandError):
            call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        imported.refresh_from_db()
        self.assertTrue(imported.enabled)

    def test_seed_rejects_non_local_public_endpoint(self):
        config = {**LOCAL_ZONES, "hydroshare": {
            **LOCAL_ZONES["hydroshare"], "aws_s3_endpoint_url_public": "https://production.example",
        }}
        with override_settings(RESOURCE_S3_ZONES_CONFIG=config), self.assertRaises(CommandError):
            call_command("seed_local_s3_zones", confirm=True, verbosity=0)

    def test_changes_require_cache_refresh_for_existing_process(self):
        call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        self.assertEqual(get_zone_config("hydroshare").aws_secret_access_key, "devpassword")
        zone = StorageZone.objects.get(name="hydroshare")
        zone.set_secret("replacement")
        zone.save()
        self.assertEqual(get_zone_config("hydroshare").aws_secret_access_key, "devpassword")
        clear_caches()
        self.assertEqual(get_zone_config("hydroshare").aws_secret_access_key, "replacement")

    def test_duplicate_bucket_aliases_fail_closed(self):
        call_command("seed_local_s3_zones", confirm=True, verbosity=0)
        zone = StorageZone.objects.get(name="published")
        zone.alias = "resource"
        zone.save()
        with self.assertRaisesMessage(ValueError, "Duplicate S3 bucket or alias"):
            get_resource_s3_zones_config()

    def test_missing_key_is_not_replaced_by_plaintext(self):
        with override_settings(S3_ZONE_ENCRYPTION_KEY_FILE=""):
            zone = StorageZone()
            with self.assertRaisesMessage(Exception, "S3_ZONE_ENCRYPTION_KEY_FILE"):
                zone.set_secret("secret")
