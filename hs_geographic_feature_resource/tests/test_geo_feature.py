__author__ = 'drew'

import os
from dateutil import parser

from django.test import TestCase, TransactionTestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest, QueryDict

from hs_core.hydroshare import resource
from hs_core.models import ResourceFile
from hs_core import hydroshare

from hs_geographic_feature_resource.models import GeographicFeatureResource, OriginalCoverage, \
                                                  GeometryInformation, FieldInformation, OriginalFileInfo
from hs_geographic_feature_resource.receivers import geofeature_post_add_files_to_resource_handler,\
                                                     metadata_element_pre_create_handler,\
                                                     metadata_element_pre_update_handler,\
                                                     UNKNOWN_STR

class TestGeoFeature(TransactionTestCase):

    def setUp(self):
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
                                         profile_links=[{'type': 'researchID', 'url': cr_res_id},
                                                        {'type': 'researchGateID', 'url': cr_res_gate_id}])


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
        resource.create_metadata_element(self.resGeoFeature.short_id,'contributor',
                                         name=con_name,
                                         description=con_des,
                                         organization=con_org,
                                         email=con_email,
                                         address=con_address,
                                         phone=con_phone,
                                         homepage=con_homepage,
                                         profile_links=[{'type': 'researchID', 'url': con_res_id},
                                                        {'type': 'researchGateID', 'url': con_res_gate_id}])

        # add another creator with only the name
        resource.create_metadata_element(self.resGeoFeature.short_id, 'contributor', name='Contributor B')

        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2015', 'end': '12/31/2015'}
        resource.create_metadata_element(self.resGeoFeature.short_id,'coverage', type='period', value=value_dict)

        # add a point type coverage
        value_dict = {'name': 'Name for box coverage',
                      'northlimit': '1', 'eastlimit': '2',
                      'southlimit': '3', 'westlimit': '4'}

        value_dict["projection"] = "WGS 84 EPSG:4326"
        value_dict["units"] = "Decimal degrees"
        resource.create_metadata_element(self.resGeoFeature.short_id,'coverage', type='box', value=value_dict)

        # add date of type 'valid'
        resource.create_metadata_element(self.resGeoFeature.short_id,'date', type='valid',
                                         start_date=parser.parse('1/1/2012'), end_date=parser.parse('12/31/2012'))

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

    def test_geo_feature_res_specific_metadata(self):

        # originalfileinfo
        # no originalfileinfo obj
        self.assertEqual(OriginalFileInfo.objects.all().count(), 0)

        # create 1 originalfileinfo obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id, 'OriginalFileInfo', fileType='SHP',
                                         fileCount=3, baseFilename="baseFilename")
        self.assertEqual(OriginalFileInfo.objects.all().count(), 1)

        # may not create any more OriginalFileInfo
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resGeoFeature.short_id, 'OriginalFileInfo',
                                                                           fileType= 'ZSHP',
                                                                           fileCount= 5,
                                                                           baseFilename= "baseFilename2")

        self.assertEqual(OriginalFileInfo.objects.all().count(), 1)
        # update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id, 'OriginalFileInfo',
                                         element_id=OriginalFileInfo.objects.first().id,
                                         fileType='KML',
                                         fileCount=8,
                                         baseFilename="baseFilename3")
        self.assertEqual(OriginalFileInfo.objects.first().fileType, 'KML')
        self.assertEqual(OriginalFileInfo.objects.first().fileCount, 8)
        self.assertEqual(OriginalFileInfo.objects.first().baseFilename, 'baseFilename3')

        # delete OriginalCoverage obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'OriginalFileInfo',
                                         element_id=OriginalFileInfo.objects.first().id)
        self.assertEqual(OriginalFileInfo.objects.all().count(), 0)

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
                                             northlimit='1', eastlimit='2', southlimit='3', westlimit='4')

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
        self.assertEqual (FieldInformation.objects.all().count(), 2)

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

    def test_geofeature_pre_create_resource(self):
        resource_type = "GeographicFeatureResource"
        files = []
        target = 'hs_geographic_feature_resource/tests/states_shp_sample.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_shp_sample.zip'))
        self.assertEqual(len(files), 1)
        res_title = "test title"
        url_key = "page_redirect_url"
        page_url_dict, res_title, metadata = \
            hydroshare.utils.resource_pre_create_actions(resource_type=resource_type, files=files,
                                                         resource_title=res_title, page_redirect_url_key=url_key)
        self.assertEqual(len(files), 7)

        for item_dict in metadata:
            self.assertEqual(len(item_dict.keys()), 1)
            key = item_dict.keys()[0]
            if key == "OriginalFileInfo":
                self.assertEqual(item_dict["OriginalFileInfo"]["baseFilename"], "states")
                self.assertEqual(item_dict["OriginalFileInfo"]["fileCount"], 7)
                self.assertEqual(item_dict["OriginalFileInfo"]["fileType"], "ZSHP")
            elif key == "field_info_array":
                self.assertEqual(len(item_dict["field_info_array"]), 5)
            elif key == "geometryinformation":
                self.assertEqual(item_dict["geometryinformation"]["featureCount"], 51)
                self.assertEqual(item_dict["geometryinformation"]["geometryType"], "MULTIPOLYGON")
            elif key == "originalcoverage":
                self.assertEqual(item_dict["originalcoverage"]['datum'], 'North_American_Datum_1983')
                self.assertEqual(item_dict["originalcoverage"]['eastlimit'], -66.96927125875777)
                self.assertEqual(item_dict["originalcoverage"]['northlimit'], 71.40623539396698)
                self.assertEqual(item_dict["originalcoverage"]['southlimit'], 18.92178634508703)
                self.assertEqual(item_dict["originalcoverage"]['westlimit'], -178.21759836236586)
                self.assertEqual(item_dict["originalcoverage"]['unit'], 'Degree')
                self.assertEqual(item_dict["originalcoverage"]['projection_name'], 'GCS_North_American_1983')

    def test_geofeature_pre_add_files_to_resource(self):

        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_with_folder.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='gis.osm_adminareas_v06_with_folder.zip'))
        hydroshare.utils.resource_file_add_pre_process(self.resGeoFeature, files, self.user,)

        self.assertEqual(len(files), 5)
        self.assertNotEqual(self.resGeoFeature.metadata.originalfileinfo.all().first(), None)
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().baseFilename, "gis.osm_adminareas_v06")
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().fileCount, 5)
        self.assertEqual(self.resGeoFeature.metadata.originalfileinfo.all().first().fileType, "ZSHP")
        self.assertEqual(self.resGeoFeature.metadata.fieldinformation.all().count(), 7)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.all().first().featureCount, 87)
        self.assertEqual(self.resGeoFeature.metadata.geometryinformation.all().first().geometryType, "POLYGON")
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().first().datum, 'WGS_1984')
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.all().first().eastlimit - 3.4520493) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.all().first().northlimit - 45.0466382) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.all().first().southlimit - 42.5732416) < self.allowance)
        self.assertTrue(abs(self.resGeoFeature.metadata.originalcoverage.all().first().westlimit - (-0.3263017)) < self.allowance)
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().first().unit, 'Degree')
        self.assertEqual(self.resGeoFeature.metadata.originalcoverage.all().first().projection_name, 'GCS_WGS_1984')

    def test_geofeature_pre_delete_file(self):
        # Example
        # ResourceFileObj.resource_file.file.name
        # '/tmp/tmp7rsGzV'
        # ResourceFileObj.resource_file.name
        # u'dab1f89d9b2a4082aae083c9d0937d15/data/contents/states.sbx'

        # test: del .shp file (all files will be removed)
        for f in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            f.resource_file.delete()
            f.delete()
        # add files first
        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_with_folder.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='gis.osm_adminareas_v06_with_folder.zip'))
        hydroshare.utils.resource_file_add_pre_process(self.resGeoFeature, files, self.user,)

        hydroshare.add_resource_files(self.resGeoFeature.short_id, *files)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 5)

        for res_f_obj in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            del_f_fullname = res_f_obj.resource_file.name.lower()
            del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
            del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
            if del_f_ext == ".shp":
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, res_f_obj.id, self.user)
                self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 0)

        # test: del .prj file
        for f in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            f.resource_file.delete()
            f.delete()
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 0)

        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_with_folder.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='gis.osm_adminareas_v06_with_folder.zip'))
        hydroshare.utils.resource_file_add_pre_process(self.resGeoFeature, files, self.user,)
        hydroshare.add_resource_files(self.resGeoFeature.short_id, *files)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 5)
        for res_f_obj in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            del_f_fullname = res_f_obj.resource_file.name.lower()
            del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
            del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
            if del_f_ext == ".prj":
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, res_f_obj.id, self.user)
                self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 4)
                for res_f_obj_2 in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
                    del_f_fullname = res_f_obj_2.resource_file.name.lower()
                    del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
                    del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
                    self.assertNotEqual(del_f_ext, ".prj")
                    originalcoverage_obj = self.resGeoFeature.metadata.originalcoverage.all().first()
                    self.assertEqual(originalcoverage_obj.projection_string, UNKNOWN_STR)
                    self.assertEqual(self.resGeoFeature.metadata.coverages.all().count(), 0)

        # test: del .xml file
        for f in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            f.resource_file.delete()
            f.delete()
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 0)

        files = []
        target = 'hs_geographic_feature_resource/tests/states_shp_sample.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_shp_sample.zip'))
        hydroshare.utils.resource_file_add_pre_process(self.resGeoFeature, files, self.user,)
        hydroshare.add_resource_files(self.resGeoFeature.short_id, *files)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 7)
        for res_f_obj in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            del_f_fullname = res_f_obj.resource_file.name.lower()
            del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
            del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
            if del_f_ext == ".xml":
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, res_f_obj.id, self.user)
                self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 6)
                for res_f_obj_2 in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
                    del_f_fullname = res_f_obj_2.resource_file.name.lower()
                    del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
                    del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
                    self.assertNotEqual(del_f_ext, ".xml")

    def test_post_add_files_to_resource(self):
        # test: add all files
        for f in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
            f.resource_file.delete()
            f.delete()

        # add files first
        files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06_with_folder.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='gis.osm_adminareas_v06_with_folder.zip'))
        hydroshare.utils.resource_file_add_pre_process(self.resGeoFeature, files, self.user,)

        hydroshare.add_resource_files(self.resGeoFeature.short_id, *files)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 5)

        # remove .prj
        for res_f_obj in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):

            del_f_fullname = res_f_obj.resource_file.name.lower()
            del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
            del_f_name, del_f_ext = os.path.splitext(del_f_fullname)

            if del_f_ext == ".prj":
                hydroshare.delete_resource_file(self.resGeoFeature.short_id, res_f_obj.id, self.user)
                self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 4)
                for res_f_obj_2 in ResourceFile.objects.filter(object_id=self.resGeoFeature.id):
                    del_f_fullname = res_f_obj_2.resource_file.name.lower()
                    del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
                    del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
                    self.assertNotEqual(del_f_ext, ".prj")
                    originalcoverage_obj = self.resGeoFeature.metadata.originalcoverage.all().first()
                    self.assertEqual(originalcoverage_obj.projection_string, UNKNOWN_STR)
                    self.assertEqual(self.resGeoFeature.metadata.coverages.all().count(), 0)
        # add .prj
        add_files = []
        target = 'hs_geographic_feature_resource/tests/gis.osm_adminareas_v06/gis.osm_adminareas_v06.prj'
        add_files.append(UploadedFile(file=open(target, 'r'), name='gis.osm_adminareas_v06.prj'))
        hydroshare.add_resource_files(self.resGeoFeature.short_id, *add_files)
        self.assertEqual(ResourceFile.objects.filter(object_id=self.resGeoFeature.id).count(), 5)
        geofeature_post_add_files_to_resource_handler(sender=GeographicFeatureResource,
                                                      resource=self.resGeoFeature, files=add_files)
        originalcoverage_obj = self.resGeoFeature.metadata.originalcoverage.all().first()
        self.assertNotEqual(originalcoverage_obj.projection_string, UNKNOWN_STR)

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
