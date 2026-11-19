from django.db import models as m
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.conf import settings
from cryptography.fernet import Fernet
from urllib.parse import urlsplit


class AVU(m.Model):
    name = m.TextField()
    attName = m.TextField()
    attVal = m.TextField(null=True)

    class Meta:
        verbose_name = 'AVU'
        constraints = [
            m.UniqueConstraint(fields=['name', 'attName'], name='unique_avu')
        ]


def zone_cipher():
    key_path = getattr(settings, "S3_ZONE_ENCRYPTION_KEY_FILE", "")
    if not key_path:
        raise ImproperlyConfigured("S3_ZONE_ENCRYPTION_KEY_FILE is required for database zones")
    with open(key_path, "rb") as key_file:
        return Fernet(key_file.read().strip())


def validate_storage_endpoint(value):
    try:
        parsed = urlsplit(value)
        if (any(char.isspace() or ord(char) < 32 or char == "\\" for char in value)
                or parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or parsed.port == 0):
            raise ValueError
    except ValueError:
        raise ValidationError("Enter an HTTP(S) endpoint without credentials, query, or fragment.")


class StorageZone(m.Model):
    name = m.SlugField(unique=True, max_length=100)
    bucket_name = m.CharField(max_length=255, unique=True)
    alias = m.CharField(max_length=255, blank=True)
    endpoint = m.CharField(max_length=500, validators=[validate_storage_endpoint])
    public_endpoint = m.CharField(max_length=500, validators=[validate_storage_endpoint])
    access_key = m.CharField(max_length=255)
    encrypted_secret = m.BinaryField(editable=False)
    region = m.CharField(max_length=100, default="auto")
    copy_method = m.CharField(max_length=20, choices=[
        ("copy_object", "Copy object"), ("managed_copy", "Managed copy")
    ], default="copy_object")
    multipart_copy_threshold = m.PositiveBigIntegerField(default=5 * 1024 ** 3)
    enabled = m.BooleanField(default=True)

    def set_secret(self, secret):
        self.encrypted_secret = zone_cipher().encrypt(secret.encode("utf-8"))

    def get_secret(self):
        return zone_cipher().decrypt(bytes(self.encrypted_secret)).decode("utf-8")

    def as_config(self):
        return {
            "bucket_name": self.bucket_name,
            "alias": self.alias,
            "aws_s3_endpoint_url": self.endpoint,
            "aws_s3_endpoint_url_public": self.public_endpoint,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.get_secret(),
            "region": self.region,
            "copy_method": self.copy_method,
            "multipart_copy_threshold": self.multipart_copy_threshold,
        }

    def __str__(self):
        return self.name
