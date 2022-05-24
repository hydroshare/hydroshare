# -*- coding: utf-8 -*-
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_composite_resource.models import CompositeResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from django.core.management import call_command
from hs_core.tests.api.utils import zip_up
import os
import zipfile


class TestIngestBag(MockIRODSTestCaseMixin, TestCase):

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
        zipf = zipfile.ZipFile('hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', 'w')
        zip_up(zipf, 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e')

    def tearDown(self):
        super(TestIngestBag, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        os.remove('hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip')

    def test_bag_ingestion_command(self):
        assert CompositeResource.objects.all().count() == 0
        call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', user_id=str(self.user.id))
        assert CompositeResource.objects.all().count() == 1
        res = CompositeResource.objects.all().first()
        assert res.metadata.title.value == "czo res"
        assert res.files.all().count() == 1
        readme = res.files.all().first()
        assert readme.file_name == "README.md"

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
