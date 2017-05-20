from dateutil import parser

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from hs_core.hydroshare import resource
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_file_types.models import geofeature
from hs_geographic_feature_resource.models import GeographicFeatureResource, OriginalCoverage, \
                                                  GeometryInformation, FieldInformation
from hs_geographic_feature_resource.receivers import metadata_element_pre_create_handler,\
                                                     metadata_element_pre_update_handler


class TestGeoFeature(MockIRODSTestCaseMixin, TransactionTestCase):

    def setUp(self):
        super(TestGeoFeature, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'zhiyu.li@byu.edu',
            username='drew',
            first_name='Zhiyu',
            last_name='Li',
            superuser=False,
            groups=[self.group]
        )
        self.allowance = 0.00001

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2']
        )

    def test_geo_feature_basic_metadata(self):
        # add another creator with all sub_elements
        cr_name = 'Creator A'
        cr_des = 'http://hydroshare.org/user/001'
        cr_org = "BYU"
        cr_email = 'creator.a@byu.edu'
        cr_address = "Provo, UT, USA"
        cr_phone = '123-456-7890'
        cr_homepage = 'http://home.byu.edu/'
        cr_res_id = 'http://research.org/001'
        cr_res_gate_id = 'http://research-gate.org/001'
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'creator',
                                         name=cr_name,
                                         description=cr_des,
                                         organization=cr_org,
                                         email=cr_email,
                                         address=cr_address,
                                         phone=cr_phone,
                                         homepage=cr_homepage,
                                         profile_links=[{'type': 'researchID',
                                                         'url': cr_res_id},
                                                        {'type': 'researchGateID',
                                                         'url': cr_res_gate_id}])

        # add another creator with only the name
        resource.create_metadata_element(self.resGeoFeature.short_id, 'creator', name='Creator B')

        # test adding a contributor with all sub_elements
        con_name = 'Contributor A'
        con_des = 'http://hydroshare.org/user/002'
        con_org = "BYU"
        con_email = 'contributor.a@byu.edu'
        con_address = "Provo, UT, USA"
        con_phone = '123-456-7890'
        con_homepage = 'http://usu.edu/homepage/009'
        con_res_id = 'http://research.org/009'
        con_res_gate_id = 'http://research-gate.org/009'
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'contributor',
                                         name=con_name,
                                         description=con_des,
                                         organization=con_org,
                                         email=con_email,
                                         address=con_address,
                                         phone=con_phone,
                                         homepage=con_homepage,
                                         profile_links=[{'type': 'researchID',
                                                         'url': con_res_id},
                                                        {'type': 'researchGateID',
                                                         'url': con_res_gate_id}])

        # add another creator with only the name
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'contributor', name='Contributor B')

        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2015', 'end': '12/31/2015'}
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'coverage',
                                         type='period',
                                         value=value_dict)

        # add a point type coverage
        value_dict = {'name': 'Name for box coverage',
                      'northlimit': '80', 'eastlimit': '130',
                      'southlimit': '70', 'westlimit': '120'}

        value_dict["projection"] = "WGS 84 EPSG:4326"
        value_dict["units"] = "Decimal degrees"
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'coverage', type='box', value=value_dict)

        # add date of type 'valid'
        resource.create_metadata_element(self.resGeoFeature.short_id,
                                         'date',
                                         type='valid',
                                         start_date=parser.parse('1/1/2012'),
                                         end_date=parser.parse('12/31/2012'))

        # add a format element
        format = 'shp'
        resource.create_metadata_element(self.resGeoFeature.short_id, 'format', value=format)

        # add a relation element of uri type
        resource.create_metadata_element(self.resGeoFeature.short_id, 'relation', type='isPartOf',
                                         value='http://hydroshare.org/resource/001')

        # add another relation element of non-uri type
        resource.create_metadata_element(self.resGeoFeature.short_id, 'relation', type='isDataFor',
                                         value='This resource is for another resource')

        # add a source element of uri type
        resource.create_metadata_element(self.resGeoFeature.short_id, 'source',
                                         derived_from='http://hydroshare.org/resource/0002')

        # add a subject element
        resource.create_metadata_element(self.resGeoFeature.short_id, 'subject', value='sub-1')

        # add another subject element
        resource.create_metadata_element(self.resGeoFeature.short_id, 'subject', value='sub-2')
        self.resGeoFeature.delete()

    def test_geo_feature_res_specific_metadata(self):

        # originalcoverage
        # no OriginalCoverage obj
        self.assertEqual(OriginalCoverage.objects.all().count(), 0)

        # create OriginalCoverage obj without a required para: southlimit
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resGeoFeature.short_id, 'originalcoverage',
                                             northlimit='1', eastlimit='2', southlimit='3')

        # no OriginalCoverage obj
        self.assertEqual(OriginalCoverage.objects.all().count(), 0)

        # create 1 OriginalCoverage obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id, 'originalcoverage',
                                         northlimit='1',  eastlimit='2',
                                         southlimit='3',  westlimit='4')
        self.assertEqual(OriginalCoverage.objects.all().count(), 1)

        # may not create any more OriginalCoverage
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resGeoFeature.short_id, 'originalcoverage',
                                             northlimit='1', eastlimit='2',
                                             southlimit='3', westlimit='4')

        self.assertEqual(OriginalCoverage.objects.all().count(), 1)
        # update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id, 'originalcoverage',
                                         element_id=OriginalCoverage.objects.first().id,
                                         northlimit='11',  eastlimit='22',
                                         southlimit='33',  westlimit='44',
                                         projection_string='projection_string1',
                                         projection_name='projection_name1',
                                         datum='datum1', unit='unit1')
        self.assertEqual(OriginalCoverage.objects.first().unit, 'unit1')

        # delete OriginalCoverage obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'originalcoverage',
                                         element_id=OriginalCoverage.objects.first().id)
        self.assertEqual(OriginalCoverage.objects.all().count(), 0)

        # GeometryInformation
        # no GeometryInformation obj
        self.assertEqual(GeometryInformation.objects.all().count(), 0)

        # no GeometryInformation obj
        self.assertEqual(GeometryInformation.objects.all().count(), 0)

        # create 1 GeometryInformation obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id, 'GeometryInformation',
                                         featureCount='1', geometryType='Polygon_test')
        self.assertEqual(GeometryInformation.objects.all().count(), 1)

        # may not create any more GeometryInformation
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resGeoFeature.short_id, 'GeometryInformation',
                                             featureCount='1', geometryType='Polygon_test')

        # update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id, 'GeometryInformation',
                                         element_id=GeometryInformation.objects.first().id,
                                         featureCount='2', geometryType='Point_test')
        self.assertEqual(GeometryInformation.objects.first().geometryType, 'Point_test')
        self.assertEqual(GeometryInformation.objects.first().featureCount, 2)

        # delete GeometryInformation obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'GeometryInformation',
                                         element_id=GeometryInformation.objects.first().id)
        self.assertEqual(GeometryInformation.objects.all().count(), 0)

        # FieldInformation
        # no FieldInformation obj
        self.assertEqual(FieldInformation.objects.all().count(), 0)

        # no FieldInformation obj
        self.assertEqual(FieldInformation.objects.all().count(), 0)

        # create 1 FieldInformation obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id, 'FieldInformation',
                                         fieldName='fieldName1', fieldType='fieldType1')
        self.assertEqual(FieldInformation.objects.all().count(), 1)

        resource.create_metadata_element(self.resGeoFeature.short_id, 'FieldInformation',
                                         fieldName='fieldName2', fieldType='fieldType2')
        self.assertEqual(FieldInformation.objects.all().count(), 2)

        # update existing meta
        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1')
        self.assertEqual(field_info_obj_list.count(), 1)
        field_1_ele_id_old = field_info_obj_list[0].id
        resource.update_metadata_element(self.resGeoFeature.short_id, 'FieldInformation',
                                         element_id=field_1_ele_id_old,
                                         fieldName='fieldName1_new',
                                         fieldType='fieldType1_new')

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1_new')
        self.assertEqual(field_info_obj_list.count(), 1)
        field_1_ele_id_new = field_info_obj_list[0].id
        # ele_id should not change
        self.assertEqual(field_1_ele_id_new, field_1_ele_id_old)
        # old value is gone
        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1')
        self.assertEqual(field_info_obj_list.count(), 0)

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName2')
        self.assertEqual(field_info_obj_list.count(), 1)
        field_2_ele_id_old = field_info_obj_list[0].id

        self.assertEqual(FieldInformation.objects.all().count(), 2)

        # delete FieldInformation obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'FieldInformation',
                                         element_id=field_1_ele_id_old)
        self.assertEqual(FieldInformation.objects.all().count(), 1)

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1_new')
        self.assertEqual(field_info_obj_list.count(), 0)

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName2')
        self.assertEqual(field_info_obj_list.count(), 1)

        resource.delete_metadata_element(self.resGeoFeature.short_id, 'FieldInformation',
                                         element_id=field_2_ele_id_old)
        self.assertEqual(FieldInformation.objects.all().count(), 0)
        self.resGeoFeature.delete()

    def test_create_resource_with_zip_file(self):
        # test that file upload will be successful and metadata gets extracted
        # if the zip file has the 3 required files
        # this zip file has only the required 3 files (.shp, .shx and .dbf)
        files = []
        target = 'hs_geographic_feature_resource/tests/states_required_files.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_required_files.zip'))

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2'],
            files=files
        )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature, user=self.user,
                                                      metadata=[])

        # check that the resource has 3 files
        self.assertEqual(self.resGeoFeature.files.count(), 3)

        # test extracted metadata

        # there should not be any resource level coverage
        self.assertEqual(self.resGeoFeature.metadata.coverages.count(), 0)
        self.assertNotEqual(self.resGeoFeature.metadata.geometryinformation, None)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.featureCount, 51)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.geometryType,
                         "MULTIPOLYGON")

        self.assertNotEqual(self.resGeoFeature.metadata.originalcoverage, None)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum,
                         'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'unknown')
        self.assertGreater(len(self.resGeoFeature.metadata.originalcoverage.projection_string), 0)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.eastlimit, -66.9692712587578)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.northlimit, 71.406235393967)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.southlimit, 18.921786345087)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.westlimit,
                         -178.217598362366)

        self.resGeoFeature.delete()

    def test_create_resource_with_invalid_zip_file(self):
        # test that file upload will fail when an invalid zip file is used to create a resource

        files = []
        target = 'hs_geographic_feature_resource/tests/states_invalid.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_invalid.zip'))

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2'],
            files=files
        )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler - should fail - no file get uploaded
        with self.assertRaises(ValidationError):
            hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature,
                                                          user=self.user, metadata=[])

        # check that the resource has no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

    def test_add_zip_file_to_resource(self):
        # here we are using a zip file that has all the 15 (3 required + 12 optional) files

        # check that the resource has no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_all_files.zip'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='gis.osm_adminareas_v06_all_files.zip'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user)

        # check that the resource has 15 files
        self.assertEqual(self.resGeoFeature.files.count(), 15)

        # test extracted metadata
        self.assertEqual(self.resGeoFeature.metadata.fieldinformations.all().count(), 7)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.featureCount, 87)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.geometryType, "POLYGON")
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum, 'WGS_1984')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.eastlimit -
                            3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.northlimit -
                            45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.southlimit -
                            42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.westlimit -
                            (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'GCS_WGS_1984')
        self.resGeoFeature.delete()

    def test_delete_shp_shx_dbf_file(self):
        # test that deleting any of the required files (.shp, .shx or .dbf) file deletes all files

        self._test_delete_file(file_extension='.shp')
        self._test_delete_file(file_extension='.shx')
        self._test_delete_file(file_extension='.dbf')
        self.resGeoFeature.delete()

    def test_delete_optional_files(self):
        # test that deleting any of the optional files deletes only that file

        for ext in ('.prj', '.sbx', '.sbn', '.cpg', '.xml', '.fbn', '.ain', '.aih', '.atx', '.ixs',
                    '.mxs', '.fbx'):
            self._test_delete_optional_file(file_extension=ext)

    def test_delete_prj_file(self):
        # deleting .prj file should set attributes (datum, unit, and projection_name) of
        # the orginalcoverage element to 'uknown' and delete the spatial covarage at the resource
        # level
        self.assertEqual(self.resGeoFeature.files.count(), 0)

        # add files first
        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_all_files.zip'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='gis.osm_adminareas_v06_all_files.zip'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user, )

        # check that the resource has 15 files
        self.assertEqual(self.resGeoFeature.files.count(), 15)
        self.assertTrue(self.resGeoFeature.metadata.coverages.filter(type='box').exists())
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum, 'WGS_1984')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.eastlimit -
                            3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.northlimit -
                            45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.southlimit -
                            42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.westlimit -
                            (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'GCS_WGS_1984')
        self.assertGreater(len(self.resGeoFeature.metadata.originalcoverage.projection_string), 0)

        # find the .shp file and delete it
        for f in self.resGeoFeature.files.all():
            if f.extension == '.prj':
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, f.id, self.user)
                break
        # resource should have 14 files
        self.assertEqual(self.resGeoFeature.files.count(), 14)
        # resource level spatial coverage should have been deleted
        self.assertFalse(self.resGeoFeature.metadata.coverages.filter(type='box').exists())
        # test original coverage
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum, 'unknown')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.eastlimit -
                            3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.northlimit -
                            45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.southlimit -
                            42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.westlimit -
                            (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name, 'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_string, 'unknown')
        self.resGeoFeature.delete()

    def test_add_prj_file(self):
        # test that if a prj file gets added then the attributes (datum, unit and projection_name)
        # of originalcoverage element gets populated and resource level spatial coverage element
        # gets created

        # this zip file has only the required 3 files (.shp, .shx and .dbf)
        files = []
        target = 'hs_geographic_feature_resource/tests/states_required_files.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_required_files.zip'))

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2'],
            files=files
        )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature, user=self.user,
                                                      metadata=[])

        # check that the resource has 3 files
        self.assertEqual(self.resGeoFeature.files.count(), 3)

        # test extracted metadata

        # there should not be any resource level coverage
        self.assertEqual(self.resGeoFeature.metadata.coverages.count(), 0)
        self.assertNotEqual(self.resGeoFeature.metadata.geometryinformation, None)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.featureCount, 51)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.geometryType,
                         "MULTIPOLYGON")

        self.assertNotEqual(self.resGeoFeature.metadata.originalcoverage, None)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum,
                         'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'unknown')
        self.assertGreater(len(self.resGeoFeature.metadata.originalcoverage.projection_string), 0)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'unknown')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.eastlimit, -66.9692712587578)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.northlimit, 71.406235393967)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.southlimit, 18.921786345087)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.westlimit,
                         -178.217598362366)

        # now add the .prj file
        files = []
        target = 'hs_geographic_feature_resource/tests/states.prj'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='states.prj'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user)

        # there should not be a spacial coverage at resource level coverage
        self.assertTrue(self.resGeoFeature.metadata.coverages.filter(type='box').exists())
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.datum,
                         'North_American_Datum_1983')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.projection_name,
                         'GCS_North_American_1983')
        self.assertGreater(len(self.resGeoFeature.metadata.originalcoverage.projection_string), 0)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.eastlimit, -66.9692712587578)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.northlimit, 71.406235393967)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.southlimit, 18.921786345087)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.westlimit,
                         -178.217598362366)
        self.resGeoFeature.delete()

    def test_add_xml_file_one(self):
        # test that if a .xml file gets added then the resource abstract and keywords get
        # updated. Abstract gets updated only if the there is no abstract already
        # this zip file has only the required 3 files (.shp, .shx and .dbf)
        files = []
        target = 'hs_geographic_feature_resource/tests/states_required_files.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_required_files.zip'))

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2'],
            files=files
        )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature, user=self.user,
                                                      metadata=[])

        # check that the resource has 3 files
        self.assertEqual(self.resGeoFeature.files.count(), 3)
        # there should not be any abstract
        self.assertEqual(self.resGeoFeature.metadata.description, None)
        # there should be 2 keywords
        self.assertEqual(self.resGeoFeature.metadata.subjects.count(), 2)
        # now add the .shp.xml file
        files = []
        target = 'hs_geographic_feature_resource/tests/states.shp.xml'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='states.shp.xml'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user)
        # check that the resource has 4 files
        self.assertEqual(self.resGeoFeature.files.count(), 4)
        # there should be abstract now (abstract came from the xml file)
        self.assertNotEqual(self.resGeoFeature.metadata.description, None)
        # there should be 4 (2 keywords came from the xml file) keywords
        self.assertEqual(self.resGeoFeature.metadata.subjects.count(), 4)
        self.resGeoFeature.delete()

    def test_add_xml_file_two(self):
        # test that if a .xml file gets added then the resource title and abstract gets
        # updated. Abstract gets updated only if the there is no abstract already. Title
        # gets updated only if the resource has the default title (untitled resource)
        # this zip file has only the required 3 files (.shp, .shx and .dbf)
        files = []
        target = 'hs_geographic_feature_resource/tests/states_required_files.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_required_files.zip'))

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Untitled resource',
            files=files
        )
        # uploaded file validation and metadata extraction happens in post resource
        # creation handler
        hydroshare.utils.resource_post_create_actions(resource=self.resGeoFeature, user=self.user,
                                                      metadata=[])

        # check that the resource has 3 files
        self.assertEqual(self.resGeoFeature.files.count(), 3)
        # there should title
        self.assertEqual(self.resGeoFeature.metadata.title.value, 'Untitled resource')
        # there should not be any abstract
        self.assertEqual(self.resGeoFeature.metadata.description, None)
        # there should be no keywords
        self.assertEqual(self.resGeoFeature.metadata.subjects.count(), 0)
        # now add the .shp.xml file
        files = []
        target = 'hs_geographic_feature_resource/tests/states.shp.xml'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='states.shp.xml'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user)
        # check that the resource has 4 files
        self.assertEqual(self.resGeoFeature.files.count(), 4)
        # there title should not be 'Untitled resource
        self.assertNotEqual(self.resGeoFeature.metadata.title.value, 'Untitled resource')
        # there should be abstract now (abstract came from the xml file)
        self.assertNotEqual(self.resGeoFeature.metadata.description, None)
        # there should be 2 (2 keywords came from the xml file) keywords
        self.assertEqual(self.resGeoFeature.metadata.subjects.count(), 2)
        self.resGeoFeature.delete()

    def test_metadata_element_pre_create_and_update(self):
        request = HttpRequest()

        # originalcoverage
        request.POST = {"northlimit": 123, "eastlimit": 234,
                        "southlimit": 345, "westlimit": 456,
                        "projection_string": "proj str",
                        "projection_name": "prj name1",
                        "datum": "dam1", "unit": "u1"}

        data = metadata_element_pre_create_handler(sender=GeographicFeatureResource,
                                                   element_name="originalcoverage",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=GeographicFeatureResource,
                                                   element_name="originalcoverage",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        # fieldinformation
        request.POST = {"fieldName": "fieldName 1",
                        "fieldType": "fieldType 1",
                        "fieldTypeCode": "fieldTypeCode 1",
                        "fieldWidth": 5,
                        "fieldPrecision": 1}

        data = metadata_element_pre_create_handler(sender=GeographicFeatureResource,
                                                   element_name="fieldinformation",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=GeographicFeatureResource,
                                                   element_name="fieldinformation",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        # geometryinformation
        request.POST = {"featureCount": 12, "geometryType": "geometryType 1"}
        data = metadata_element_pre_create_handler(sender=GeographicFeatureResource,
                                                   element_name="geometryinformation",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=GeographicFeatureResource,
                                                   element_name="geometryinformation",
                                                   request=request)
        self.assertTrue(data["is_valid"])

    def test_single_point_shp(self):

        shp_full_path = "hs_geographic_feature_resource/tests/single_point_shp/logan_Outletmv.shp"
        meta_dict = geofeature.extract_metadata(shp_full_path)
        coverage_dict = meta_dict.get("coverage", None)
        self.assertNotEqual(coverage_dict, None)
        self.assertEqual(coverage_dict["Coverage"]["type"].lower(), "point")
        self.assertTrue(abs(coverage_dict["Coverage"]
                            ["value"]["east"] + 111.790377929) < self.allowance)
        self.assertTrue(abs(coverage_dict["Coverage"]
                            ["value"]["north"] - 41.7422180799) < self.allowance)

    def test_read_shp_xml(self):
        # test parsing shapefile xml metadata
        shp_xml_full_path = 'hs_geographic_feature_resource/tests/beaver_ponds_1940.shp.xml'
        metadata = geofeature.parse_shp_xml(shp_xml_full_path)
        resGeoFeature2 = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title="",
            metadata=metadata
        )

        # test abstract
        self.assertIn("white aerial photographs taken in July 1940 by the U.S. "
                      "Department of Agriculture",
                      resGeoFeature2.metadata.description.abstract)

        # test title
        self.assertIn("beaver_ponds_1940",
                      resGeoFeature2.metadata.title.value)

        # test keywords
        self.assertEqual(resGeoFeature2.metadata.subjects.all().count(), 3)
        subject_list = [s.value for s in resGeoFeature2.metadata.subjects.all()]
        self.assertIn("beaver ponds", subject_list)
        self.assertIn("beaver meadows", subject_list)
        self.assertIn("Voyageurs National Park", subject_list)
        resGeoFeature2.delete()

    def _test_delete_file(self, file_extension):
        # test that deleting the file with the specified extension *file_extension*
        # deletes all files

        # check that the resource has no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

        # add files first
        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_all_files.zip'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='gis.osm_adminareas_v06_all_files.zip'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user, )

        # check that the resource has 15 files
        self.assertEqual(self.resGeoFeature.files.count(), 15)

        # find the .shp file and delete it
        for f in self.resGeoFeature.files.all():
            if f.extension == file_extension:
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, f.id, self.user)
                break
        # resource should have no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

    def _test_delete_optional_file(self, file_extension):
        # test that deleting the optional file with the specified extension *file_extension*
        # deletes only that file

        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)'
        )
        # check that the resource has no files
        self.assertEqual(self.resGeoFeature.files.count(), 0)

        # add files first
        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_all_files.zip'
        files.append(UploadedFile(file=open(target, 'r'),
                                  name='gis.osm_adminareas_v06_all_files.zip'))
        hydroshare.utils.resource_file_add_process(self.resGeoFeature, files, self.user, )

        # check that the resource has 15 files
        self.assertEqual(self.resGeoFeature.files.count(), 15)

        # find the .shp file and delete it
        for f in self.resGeoFeature.files.all():
            if f.extension == file_extension:
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, f.id, self.user)
                break
        # resource should have 14 files
        self.assertEqual(self.resGeoFeature.files.count(), 14)
        self.resGeoFeature.delete()
