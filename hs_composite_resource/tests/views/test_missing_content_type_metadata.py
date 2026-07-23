from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin
from hs_file_types.tests.utils import CompositeResourceTestMixin


class TestContentTypeMissingMetadataViewFunction(MockS3TestCaseMixin, CompositeResourceTestMixin, TestCase):
    def setUp(self):
        super(TestContentTypeMissingMetadataViewFunction, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )
        self.composite_resource = None

    def tearDown(self):
        if self.composite_resource:
            self.composite_resource.delete()
        super(TestContentTypeMissingMetadataViewFunction, self).tearDown()

    def test_get_missing_file_type_metadata_success(self):
        self.client.login(username=self.username, password=self.password)
        self.res_title = 'Test Composite Resource'
        self.create_composite_resource()

        response = self.client.get(
            f'/hsapi/_internal/{self.composite_resource.short_id}/missing-file-type-metadata/'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'SUCCESS')
        self.assertIn('file_type_missing_metadata', data)
        self.assertEqual(
            data['file_type_missing_metadata'],
            self.composite_resource.get_missing_file_type_metadata_info(),
        )
