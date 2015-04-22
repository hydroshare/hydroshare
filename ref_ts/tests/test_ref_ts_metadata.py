__author__ = 'hydro'
from hs_core.hydroshare.resource import add_resource_files, create_resource, get_resource_map
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.hydroshare import utils, users, resource
from ref_ts.models import RefTimeSeries
from unittest import TestCase
from django.core.exceptions import ValidationError
from decimal import *

class TestQualityControlLevelMetadataModel(TestCase):
    def setUp(self):

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()
        pass

    def test_create_quality_control_level_orig(self):
        self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'QualityControlLevel', value='test quality level')
        self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 1)
        self.assertEqual(self.refts_res.metadata.quality_levels.all()[0].value, 'test quality level')

    def test_create_quality_control_level_duplicate(self):
        self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
        self.assertRaises(ValidationError, resource.create_metadata_element(
            self.refts_res.short_id,
            'QualityControlLevel',
            value='test quality level'))

    # def test_create_quality_control_level_no_qcl(self):
    #     self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
    #     self.assertRaises(ValidationError,
    #                       resource.create_metadata_element(self.refts_res.short_id, 'QualityControlLevel'))


    def test_update_quality_control_level(self):
        self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'QualityControlLevel', value='test quality level')
        self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 1)
        self.assertEqual(self.refts_res.metadata.quality_levels.all()[0].value, 'test quality level')
        q = self.refts_res.metadata.quality_levels.filter(value='test quality level')[0]
        resource.update_metadata_element(self.refts_res.short_id, 'QualityControlLevel', q.id, value='updated value')
        self.assertEqual(self.refts_res.metadata.quality_levels.all()[0].value, 'updated value')

    # def test_delete_quality_control_level(self):
    #     self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
    #     resource.create_metadata_element(self.refts_res.short_id, 'QualityControlLevel', value='test quality level')
    #     self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 1)
    #     self.assertEqual(self.refts_res.metadata.quality_levels.all()[0].value, 'test quality level')
    #     q = self.refts_res.metadata.quality_levels.filter(value='test quality level')[0]
    #     # resource.delete_metadata_element(self.refts_res.short_id, 'QualityControlLevel', q.id)
    #     # self.assertEqual(len(self.refts_res.metadata.quality_levels.all()), 0)
    #     self.assertRaises(ValidationError, resource.delete_metadata_element(self.refts_res.short_id, 'QualityControlLevel', q.id))


class TestRefURLMetadataModel(TestCase):
    def setUp(self):

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()

    def test_create_refurl_orig(self):
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'ReferenceURL', value='www.google.com', type='SOAP')
        self.assertEqual(len(self.refts_res.metadata.referenceURLs.all()), 1)
        self.assertEqual(self.refts_res.metadata.referenceURLs.all()[0].value, 'www.google.com')
        self.assertEqual(self.refts_res.metadata.referenceURLs.all()[0].type, 'SOAP')



class TestMethodMetadataModel(TestCase):
    def setUp(self):

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()

    def test_create_method_orig(self):
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'Method', value='test method')
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 1)
        self.assertEqual(self.refts_res.metadata.methods.all()[0].value, 'test method')

    def test_update_method_orig(self):
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'Method', value='test method')
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 1)
        self.assertEqual(self.refts_res.metadata.methods.all()[0].value, 'test method')
        m = self.refts_res.metadata.methods.filter(value='test method')[0]
        resource.update_metadata_element(self.refts_res.short_id, 'Method', m.id, value='updated method')
        self.assertEqual(self.refts_res.metadata.methods.all()[0].value, 'updated method')

    def test_delete_method_orig(self):
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 0)
        resource.create_metadata_element(self.refts_res.short_id, 'Method', value='test method')
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 1)
        self.assertEqual(self.refts_res.metadata.methods.all()[0].value, 'test method')
        m = self.refts_res.metadata.methods.filter(value='test method')[0]
        resource.delete_metadata_element(self.refts_res.short_id, 'Method', m.id)
        self.assertEqual(len(self.refts_res.metadata.methods.all()), 0)


class TestVariableMetadataModel(TestCase):

    def setUp(self):

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()

    def test_create_variable_orig(self):
        self.assertEqual(len(self.refts_res.metadata.variables.all()), 0)
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Variable',
                name='test variable name',
                code='test code',
                data_type='test data type',
                sample_medium='test sample medium')
        self.assertEqual(len(self.refts_res.metadata.variables.all()), 1)
        self.assertEqual(self.refts_res.metadata.variables.all()[0].name, 'test variable name')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].code, 'test code')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].data_type, 'test data type')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].sample_medium, 'test sample medium')

    def test_update_variable_orig(self):
        self.assertEqual(len(self.refts_res.metadata.variables.all()), 0)
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Variable',
                name='test variable name',
                code='test code',
                data_type='test data type',
                sample_medium='test sample medium')
        self.assertEqual(len(self.refts_res.metadata.variables.all()), 1)
        self.assertEqual(self.refts_res.metadata.variables.all()[0].name, 'test variable name')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].code, 'test code')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].data_type, 'test data type')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].sample_medium, 'test sample medium')
        v = self.refts_res.metadata.variables.filter(name='test variable name')[0]
        resource.update_metadata_element(
                self.refts_res.short_id,
                'Variable',
                v.id,
                name='test variable name2',
                code='test code2',
                data_type='test data type2',
                sample_medium='test sample medium2')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].name, 'test variable name2')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].code, 'test code2')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].data_type, 'test data type2')
        self.assertEqual(self.refts_res.metadata.variables.all()[0].sample_medium, 'test sample medium2')


class TestSiteMetadataModel(TestCase):

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')

    def tearDown(self):
        User.objects.filter(username=self.user.username).delete()

    def test_create_site_orig(self):
        self.assertEqual(len(self.refts_res.metadata.sites.all()), 0)
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Site',
                name='test site name',
                code='test site code',
                latitude=150.15,
                longitude=150.15)
        self.assertEqual(len(self.refts_res.metadata.sites.all()), 1)
        self.assertEqual(self.refts_res.metadata.sites.all()[0].name, 'test site name')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].code, 'test site code')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].latitude, Decimal('150.150000'))
        self.assertEqual(self.refts_res.metadata.sites.all()[0].longitude, Decimal('150.150000'))

    def test_update_site_orig(self):
        self.assertEqual(len(self.refts_res.metadata.sites.all()), 0)
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Site',
                name='test site name',
                code='test site code',
                latitude=150.15,
                longitude=150.15)
        self.assertEqual(len(self.refts_res.metadata.sites.all()), 1)
        self.assertEqual(self.refts_res.metadata.sites.all()[0].name, 'test site name')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].code, 'test site code')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].latitude, Decimal('150.150000'))
        self.assertEqual(self.refts_res.metadata.sites.all()[0].longitude, Decimal('150.150000'))
        s = self.refts_res.metadata.sites.filter(name='test site name')[0]
        resource.update_metadata_element(
                self.refts_res.short_id,
                'Site',
                s.id,
                name='test site name2',
                code='test site code2',
                latitude=150.17,
                longitude=150.17)
        self.assertEqual(len(self.refts_res.metadata.sites.all()), 1)
        self.assertEqual(self.refts_res.metadata.sites.all()[0].name, 'test site name2')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].code, 'test site code2')
        self.assertEqual(self.refts_res.metadata.sites.all()[0].latitude, Decimal('150.170000'))
        self.assertEqual(self.refts_res.metadata.sites.all()[0].longitude, Decimal('150.170000'))


class TestXMLCreationModel(TestCase):

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        self.refts_res = hydroshare.create_resource(
                resource_type='RefTimeSeries',
                owner=self.user,
                title='Test RefTS resource')
        resource.create_metadata_element(self.refts_res.short_id, 'QualityControlLevel', value='test quality level')
        resource.create_metadata_element(self.refts_res.short_id, 'ReferenceURL', value='www.example.com', type='REST')
        resource.create_metadata_element(self.refts_res.short_id, 'Method', value='test method')
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Variable',
                name='test variable name',
                code='test code',
                data_type='test data type',
                sample_medium='test sample medium')
        resource.create_metadata_element(
                self.refts_res.short_id,
                'Site',
                name='test site name',
                code='test site code',
                latitude=150.15,
                longitude=150.15)

    def test_xml_creation(self):
        xml_doc = self.refts_res.metadata.get_xml()
        self.assertTrue('test quality level' in xml_doc)
        self.assertTrue('www.example.com' in xml_doc)
        self.assertTrue('REST' in xml_doc)
        self.assertTrue('test method' in xml_doc)
        self.assertTrue('test variable name' in xml_doc)
        self.assertTrue('test code' in xml_doc)
        self.assertTrue('test data type' in xml_doc)
        self.assertTrue('test sample medium' in xml_doc)
        self.assertTrue('test site name' in xml_doc)
        self.assertTrue('test site code' in xml_doc)
        self.assertTrue('150.150000' in xml_doc)

    def test_xml_creation(self):
        xml_doc = self.refts_res.metadata.get_xml()
        self.assertTrue('test quality level' in xml_doc)
        self.assertTrue('test method' in xml_doc)
        self.assertTrue('test variable name' in xml_doc)
        self.assertTrue('test code' in xml_doc)
        self.assertTrue('test data type' in xml_doc)
        self.assertTrue('test sample medium' in xml_doc)
        self.assertTrue('test site name' in xml_doc)
        self.assertTrue('test site code' in xml_doc)
        self.assertTrue('150.150000' in xml_doc)

        q = self.refts_res.metadata.quality_levels.filter(value='test quality level')[0]
        resource.update_metadata_element(self.refts_res.short_id, 'QualityControlLevel', q.id, value='testing quality leve')
        m = self.refts_res.metadata.methods.filter(value='test method')[0]
        resource.update_metadata_element(self.refts_res.short_id, 'Method', m.id, value='testing metho')
        v = self.refts_res.metadata.variables.filter(name='test variable name')[0]
        resource.update_metadata_element(
                self.refts_res.short_id,
                'Variable',
                v.id,
                name='testing variable nam',
                code='testing cod',
                data_type='testing data typ',
                sample_medium='testing sample mediu')
        s = self.refts_res.metadata.sites.filter(name='test site name')[0]
        resource.update_metadata_element(
                self.refts_res.short_id,
                'Site',
                s.id,
                name='testing site nam',
                code='testing site cod',
                latitude=150.17,
                longitude=150.17)

        xml_doc = self.refts_res.metadata.get_xml()
        self.assertTrue('testing quality leve' in xml_doc)
        self.assertTrue('testing metho' in xml_doc)
        self.assertTrue('testing variable nam' in xml_doc)
        self.assertTrue('testing cod' in xml_doc)
        self.assertTrue('testing data typ' in xml_doc)
        self.assertTrue('testing sample mediu' in xml_doc)
        self.assertTrue('testing site nam' in xml_doc)
        self.assertTrue('testing site cod' in xml_doc)
        self.assertTrue('150.170000' in xml_doc)

        self.assertFalse('test quality level' in xml_doc)
        self.assertFalse('test method' in xml_doc)
        self.assertFalse('test variable name' in xml_doc)
        self.assertFalse('test code' in xml_doc)
        self.assertFalse('test data type' in xml_doc)
        self.assertFalse('test sample medium' in xml_doc)
        self.assertFalse('test site name' in xml_doc)
        self.assertFalse('test site code' in xml_doc)
        self.assertFalse('150.150000' in xml_doc)







