# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_labels', '0004_auto_add_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userresourceflags',
            name='kind',
            field=models.IntegerField(default=1, editable=False, choices=[(1, 'Favorite'), (2, 'Mine'), (3, 'Open With App')]),
        ),
    ]
