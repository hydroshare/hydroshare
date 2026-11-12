import json

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin

# Keys that must not appear in user_metadata.json -- the schema.org metadata generated from the
# ScientificDataset model
NON_COMPLIANT_KEYS = ("sharing_status", "review_started")
OMIT_WHEN_EMPTY_KEYS = ("coordinates", "sourceOrganization", "associatedMedia")


class TestResourceMetadataJsonFiles(MockS3TestCaseMixin, TestCase):
    """Tests the user/system metadata json files written to S3 for a resource."""

    def setUp(self):
        super().setUp()
        Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )
        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'test resource for metadata json files',
        )
        # set the view count without triggering save signals
        BaseResource.objects.filter(id=self.res.id).update(view_count=7)
        self.res.refresh_from_db()

    def tearDown(self):
        self.res.delete()
        super().tearDown()

    def _read_json(self, file_name):
        istorage = self.res.get_s3_storage()
        with istorage.download(f"{self.res.short_id}/.hsmetadata/{file_name}") as json_file:
            return json.loads(json_file.read())

    def test_user_metadata_json_has_no_non_compliant_fields(self):
        self.res.write_django_metadata_json_files()
        user_metadata = self._read_json("user_metadata.json")

        for key in NON_COMPLIANT_KEYS + OMIT_WHEN_EMPTY_KEYS:
            self.assertNotIn(key, user_metadata)
        # sharing status is represented by the schema.org compliant creativeWorkStatus
        self.assertEqual(user_metadata["creativeWorkStatus"]["name"], "Private")
        self.assertEqual(user_metadata["name"], "test resource for metadata json files")

    def test_system_metadata_json_has_view_count(self):
        self.res.write_django_metadata_json_files()
        system_metadata = self._read_json("system_metadata.json")
        self.assertEqual(system_metadata["viewCount"], 7)
        self.assertEqual(system_metadata["resource_id"], self.res.short_id)
