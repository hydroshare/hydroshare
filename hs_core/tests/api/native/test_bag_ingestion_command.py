# -*- coding: utf-8 -*-
import os
import shutil
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin


class TestIngestBag(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(TestIngestBag, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_bag_ingestion@email.com',
            username='bag_ingestion_test',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )

        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()

        # zip up the test bag
        dir_to_zip = 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e'
        self.zip_to_file_path = 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e'
        shutil.make_archive(self.zip_to_file_path, 'zip', dir_to_zip)

    def tearDown(self):
        super(TestIngestBag, self).tearDown()
        for res in CompositeResource.objects.all():
            res.delete()
        self.user.delete()
        self.hs_group.delete()
        os.remove(f"{self.zip_to_file_path}.zip")

    def test_bag_ingestion_command(self):
        assert CompositeResource.objects.all().count() == 0
        call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', user_id=str(self.user.id))
        assert CompositeResource.objects.all().count() == 1
        res = CompositeResource.objects.all().first()
        assert res.metadata.title.value == "czo res"
        assert res.files.all().count() == 1
        readme = res.files.all().first()
        assert readme.file_name == "README.md"
        # check file level system metadata
        assert readme._size > 0
        assert len(readme._checksum) > 0
        assert readme._modified_time is not None

    def test_bag_ingestion_command_overwrite(self):
        assert CompositeResource.objects.all().count() == 0
        res = hydroshare.create_resource("CompositeResource", self.user, "To overwrite")
        call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', user_id=str(self.user.id),
                     overwrite=True, resource_id=res.short_id)
        assert CompositeResource.objects.all().count() == 1
        res = CompositeResource.objects.all().first()
        assert res.metadata.title.value == "czo res"
        assert res.files.all().count() == 1
        readme = res.files.all().first()
        assert readme.file_name == "README.md"

    def test_bag_ingestion_command_overwrite_catch(self):
        res = hydroshare.create_resource("CompositeResource", self.user, "To overwrite")
        try:
            call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip',
                         user_id=str(self.user.id), resource_id=res.short_id)
            assert False, "should have thrown error"
        except ValidationError as e:
            assert f"Resource {res.short_id} exists, include the overwrite command or provide another resource_id." \
                   in str(e)
