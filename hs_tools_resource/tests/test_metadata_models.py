__author__ = 'hydro'
from hs_core.hydroshare.resource import add_resource_files, create_resource, get_resource_map
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.hydroshare import utils, users, resource
from ref_ts.models import RefTimeSeries
from unittest import TestCase
from django.core.exceptions import ValidationError
from decimal import *
from hs_tools_resource.models import ToolResource

class TestRequestURLMetadataModel(TestCase):
    def setUp(self):
        User.objects.all().delete()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.tool_res = hydroshare.create_resource(
                resource_type='ToolResource',
                owner=self.user,
                title='Test Tools Resource')
        self.url1 = "www.example.com"
        self.url2 = "www.example2.com"

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()
        ToolResource.objects.all().delete()

    def test_create_url_base_orig(self):
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'RequestUrlBase', value=self.url1)
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 1)
        self.assertEqual(self.tool_res.metadata.url_bases.all()[0].value, self.url1)

    def test_update_url_base_orig(self):
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'RequestUrlBase', value=self.url1)
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 1)
        self.assertEqual(self.tool_res.metadata.url_bases.all()[0].value, self.url1)
        m = self.tool_res.metadata.url_bases.filter(value=self.url1)[0]
        resource.update_metadata_element(self.tool_res.short_id, 'RequestUrlBase', m.id, value=self.url2)
        self.assertEqual(self.tool_res.metadata.url_bases.all()[0].value, self.url2)

    def test_delete_url_base_orig(self):
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'RequestUrlBase', value=self.url1)
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 1)
        self.assertEqual(self.tool_res.metadata.url_bases.all()[0].value, self.url1)
        m = self.tool_res.metadata.url_bases.filter(value=self.url1)[0]
        resource.delete_metadata_element(self.tool_res.short_id, 'RequestUrlBase', m.id)
        self.assertEqual(len(self.tool_res.metadata.url_bases.all()), 0)

class TestResourceTypeMetadataModel(TestCase):
    def setUp(self):
        User.objects.all().delete()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.tool_res = hydroshare.create_resource(
                resource_type='ToolResource',
                owner=self.user,
                title='Test Tools Resource')
        self.resourcetypes1 = "ref_ts, timeseries"
        self.resourcetypes2 = "ref_ts, geograster"

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()
        ToolResource.objects.all().delete()

    def test_create_resource_types_orig(self):
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolResourceType', tool_res_type=self.resourcetypes1)
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 1)
        self.assertEqual(self.tool_res.metadata.res_types.all()[0].tool_res_type, self.resourcetypes1)

    def test_update_resource_types_orig(self):
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolResourceType', tool_res_type=self.resourcetypes1)
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 1)
        self.assertEqual(self.tool_res.metadata.res_types.all()[0].tool_res_type, self.resourcetypes1)
        m = self.tool_res.metadata.res_types.filter(tool_res_type=self.resourcetypes1)[0]
        resource.update_metadata_element(self.tool_res.short_id, 'ToolResourceType', m.id, tool_res_type=self.resourcetypes2)
        self.assertEqual(self.tool_res.metadata.res_types.all()[0].tool_res_type, self.resourcetypes2)

    def test_delete_resource_types_orig(self):
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolResourceType', tool_res_type=self.resourcetypes1)
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 1)
        self.assertEqual(self.tool_res.metadata.res_types.all()[0].tool_res_type, self.resourcetypes1)
        m = self.tool_res.metadata.res_types.filter(tool_res_type=self.resourcetypes1)[0]
        resource.delete_metadata_element(self.tool_res.short_id, 'ToolResourceType', m.id)
        self.assertEqual(len(self.tool_res.metadata.res_types.all()), 0)

class TestFeeMetadataModel(TestCase):
    def setUp(self):
        User.objects.all().delete()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.tool_res = hydroshare.create_resource(
                resource_type='ToolResource',
                owner=self.user,
                title='Test Tools Resource')
        self.desc1 = "free"
        self.desc2 = "a lot of money"
        self.value1 = Decimal('0.00')
        self.value2 = Decimal('500.55')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()
        ToolResource.objects.all().delete()

    def test_create_fee_orig(self):
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'Fee', description=self.desc1, value=self.value1)
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].description, self.desc1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].value, self.value1)

    def test_update_fee_orig(self):
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'Fee', description=self.desc1, value=self.value1)
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].description, self.desc1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].value, self.value1)
        m = self.tool_res.metadata.fees.filter(description=self.desc1)[0]
        resource.update_metadata_element(self.tool_res.short_id, 'Fee', m.id, description=self.desc2, value=self.value2)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].description, self.desc2)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].value, self.value2)

    def test_delete_fee_orig(self):
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'Fee', description=self.desc1, value=self.value1)
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].description, self.desc1)
        self.assertEqual(self.tool_res.metadata.fees.all()[0].value, self.value1)
        m = self.tool_res.metadata.fees.filter(description=self.desc1)[0]
        resource.delete_metadata_element(self.tool_res.short_id, 'Fee', m.id)
        self.assertEqual(len(self.tool_res.metadata.fees.all()), 0)


class TestToolVersionMetadataModel(TestCase):
    def setUp(self):
        User.objects.all().delete()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.tool_res = hydroshare.create_resource(
                resource_type='ToolResource',
                owner=self.user,
                title='Test Tools Resource')
        self.version1 = "1"
        self.version2 = "1.1"

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()
        ToolResource.objects.all().delete()

    def test_create_version_orig(self):
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolVersion', value=self.version1)
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 1)
        self.assertEqual(self.tool_res.metadata.versions.all()[0].value, self.version1)

    def test_update_version_orig(self):
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolVersion', value=self.version1)
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 1)
        self.assertEqual(self.tool_res.metadata.versions.all()[0].value, self.version1)
        m = self.tool_res.metadata.versions.filter(value=self.version1)[0]
        resource.update_metadata_element(self.tool_res.short_id, 'ToolVersion', m.id, value=self.version2)
        self.assertEqual(self.tool_res.metadata.versions.all()[0].value, self.version2)

    def test_delete_version_orig(self):
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 0)
        resource.create_metadata_element(self.tool_res.short_id, 'ToolVersion', value=self.version1)
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 1)
        self.assertEqual(self.tool_res.metadata.versions.all()[0].value, self.version1)
        m = self.tool_res.metadata.versions.filter(value=self.version1)[0]
        resource.delete_metadata_element(self.tool_res.short_id, 'ToolVersion', m.id)
        self.assertEqual(len(self.tool_res.metadata.versions.all()), 0)

