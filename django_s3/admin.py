from django import forms
from django.contrib import admin
from django.conf import settings
from django.apps import apps
from django.core.exceptions import ValidationError

from .models import StorageZone


class StorageZoneForm(forms.ModelForm):
    secret_key = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to retain the existing secret.",
    )

    class Meta:
        model = StorageZone
        exclude = ("encrypted_secret",)

    def clean_secret_key(self):
        secret = self.cleaned_data["secret_key"]
        if not self.instance.pk and not secret:
            raise ValidationError("A secret key is required for a new zone.")
        return secret

    def clean(self):
        data = super().clean()
        name, bucket, alias = data.get("name"), data.get("bucket_name"), data.get("alias")
        if self.instance.pk:
            original = StorageZone.objects.get(pk=self.instance.pk)
            if name != original.name or bucket != original.bucket_name:
                raise ValidationError("Zone names and bucket names cannot be changed after creation.")
            if (original.enabled and not data.get("enabled") and apps.is_installed("theme")
                    and apps.get_model("theme", "UserQuota").objects.filter(zone=original.name).exists()):
                self.add_error("enabled", "This zone is assigned to users and cannot be disabled.")
        if name == settings.RESOURCE_S3_DEFAULT_ZONE and not data.get("enabled"):
            self.add_error("enabled", "The default zone must remain enabled.")
        others = StorageZone.objects.exclude(pk=self.instance.pk)
        if bucket and others.filter(alias=bucket).exists():
            self.add_error("bucket_name", "This bucket is already used as an alias.")
        if alias and (alias == bucket or others.filter(bucket_name=alias).exists()
                      or others.filter(alias=alias).exists()):
            self.add_error("alias", "This alias is already in use.")
        return data

    def save(self, commit=True):
        zone = super().save(commit=False)
        if self.cleaned_data["secret_key"]:
            zone.set_secret(self.cleaned_data["secret_key"])
        if commit:
            zone.save()
            self.save_m2m()
        return zone


@admin.register(StorageZone)
class StorageZoneAdmin(admin.ModelAdmin):
    form = StorageZoneForm
    list_display = ("name", "bucket_name", "endpoint", "enabled")
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False
