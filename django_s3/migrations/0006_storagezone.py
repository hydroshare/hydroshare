from django.db import migrations, models
import django_s3.models


class Migration(migrations.Migration):
    dependencies = [("django_s3", "0005_alter_avu_attval")]

    operations = [
        migrations.CreateModel(
            name="StorageZone",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.SlugField(max_length=100, unique=True)),
                ("bucket_name", models.CharField(max_length=255, unique=True)),
                ("alias", models.CharField(blank=True, max_length=255)),
                ("endpoint", models.CharField(max_length=500, validators=[django_s3.models.validate_storage_endpoint])),
                ("public_endpoint", models.CharField(max_length=500,
                                                     validators=[django_s3.models.validate_storage_endpoint])),
                ("access_key", models.CharField(max_length=255)),
                ("encrypted_secret", models.BinaryField(editable=False)),
                ("region", models.CharField(default="auto", max_length=100)),
                ("copy_method", models.CharField(
                    choices=[("copy_object", "Copy object"), ("managed_copy", "Managed copy")],
                    default="copy_object", max_length=20,
                )),
                ("multipart_copy_threshold", models.PositiveBigIntegerField(default=5368709120)),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
    ]
