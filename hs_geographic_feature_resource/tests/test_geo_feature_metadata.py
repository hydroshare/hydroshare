__author__ = 'drew'

from unittest import TestCase
from django.contrib.contenttypes.models import ContentType
from hs_core.hydroshare import utils, users, resource
from hs_core.models import GenericResource, Creator, Contributor, CoreMetaData, \
    Coverage, Rights, Title, Language, Publisher, Identifier, \
    Type, Subject, Description, Date, Format, Relation, Source

from hs_geographic_feature_resource.models import *
from hs_geographic_feature_resource.receivers import *
from django.contrib.auth.models import Group, User
from hs_core import hydroshare


class TestGeoFeatureMetadata(TestCase):
    def setUp(self):
        try:
            #self.user = User.objects.create_user('user1', email='user1@nowhere.com')
            self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
            self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )
        except:
            self.tearDown()
            self.user = User.objects.create_user('user1', email='user1@nowhere.com')


        self.resGeoFeature = hydroshare.create_resource(
            resource_type='GeographicFeatureResource',
            owner=self.user,
            title='Test Geographic Feature (shapefiles)',
            keywords=['kw1', 'kw2']
        )
    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        Creator.objects.all().delete()
        Contributor.objects.all().delete()
        CoreMetaData.objects.all().delete()
        Coverage.objects.all().delete()
        Rights.objects.all().delete()
        Title.objects.all().delete()
        Publisher.objects.all().delete()
        Description.objects.all().delete()
        Relation.objects.all().delete()
        Subject.objects.all().delete()
        Source.objects.all().delete()
        Identifier.objects.all().delete()
        Type.objects.all().delete()
        Format.objects.all().delete()
        Date.objects.all().delete()
        Language.objects.all().delete()
        #remove res specific model objs here
        #Variable.objects.all().delete()
        OriginalCoverage.objects.all().delete()
        GeometryInformation.objects.all().delete()
        FieldInformation.objects.all().delete()
        OriginalFileInfo.objects.all().delete()


    def test_geo_feature_basic_metadata(self):
        self.assertEqual(1,1)
        # add a type element
        # resource.create_metadata_element(self.resGeoFeature.short_id, 'type', url="http://hydroshare.org/geographicfeature")

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
        resource.create_metadata_element(self.resGeoFeature.short_id,'creator',
                                         name=cr_name,
                                         description=cr_des,
                                         organization=cr_org,
                                         email=cr_email,
                                         address=cr_address,
                                         phone=cr_phone,
                                         homepage=cr_homepage,
                                         researcherID=cr_res_id,
                                         researchGateID=cr_res_gate_id)

        # # add another creator with only the name
        resource.create_metadata_element(self.resGeoFeature.short_id,'creator', name='Creator B')

        #test adding a contributor with all sub_elements
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
                                         researcherID=con_res_id,
                                         researchGateID=con_res_gate_id)

        # add another creator with only the name
        resource.create_metadata_element(self.resGeoFeature.short_id,'contributor', name='Contributor B')

        # add a period type coverage
        # add a period type coverage
        value_dict = {'name':'Name for period coverage' , 'start':'1/1/2015', 'end':'12/31/2015'}
        resource.create_metadata_element(self.resGeoFeature.short_id,'coverage', type='period', value=value_dict)

        # add a point type coverage
        value_dict = {'name':'Name for box coverage', 'northlimit':'1', 'eastlimit':'2', 'southlimit':'3', 'westlimit':'4'}

        value_dict["projection"]="WGS 84 EPSG:4326"
        value_dict["units"]="Decimal degrees"
        resource.create_metadata_element(self.resGeoFeature.short_id,'coverage', type='box', value=value_dict)

        # add date of type 'valid'
        resource.create_metadata_element(self.resGeoFeature.short_id,'date', type='valid', start_date='1/1/2012', end_date='12/31/2012')

        # add a format element
        format = 'shp'
        resource.create_metadata_element(self.resGeoFeature.short_id,'format', value=format)


        # add a language element
        #resource.create_metadata_element(self.resGeoFeature.short_id,'language', code='eng')

        # # add 'Publisher' element
        # original_file_name = 'original.txt'
        # original_file = open(original_file_name, 'w')
        # original_file.write("original text")
        # original_file.close()
        #
        # original_file = open(original_file_name, 'r')
        # # add the file to the resource
        # hydroshare.add_resource_files(self.resGeoFeature.short_id, original_file)

        # resource.create_metadata_element(self.resGeoFeature.short_id,'publisher', name="HydroShare", url="http://hydroshare.org")

        # add a relation element of uri type
        resource.create_metadata_element(self.resGeoFeature.short_id,'relation', type='isPartOf',
                                         value='http://hydroshare.org/resource/001')

        # add another relation element of non-uri type
        resource.create_metadata_element(self.resGeoFeature.short_id,'relation', type='isDataFor',
                                         value='This resource is for another resource')


        # add a source element of uri type
        resource.create_metadata_element(self.resGeoFeature.short_id,'source', derived_from='http://hydroshare.org/resource/0002')

        # # add a rights element
        # resource.create_metadata_element(self.resGeoFeature.short_id,'rights', statement='This is the rights statement for this resource',
        #                                  url='http://rights.ord/001')

        # add a subject element
        resource.create_metadata_element(self.resGeoFeature.short_id,'subject', value='sub-1')

        # add another subject element
        resource.create_metadata_element(self.resGeoFeature.short_id,'subject', value='sub-2')

##########################################################################################################3
        # originalfileinfo
        #no originalfileinfo obj
        self.assertEqual (len(OriginalFileInfo.objects.all()), 0)

        #create originalfileinfo obj without a required para: southlimit
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', fileType='SHP'))

        # #create originalfileinfo obj without a predefined keywords
        # self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', fileType='MY_SHP', fileCount=3, baseFilename="baseFilename"))

        #no originalfileinfo obj
        self.assertEqual (len(OriginalFileInfo.objects.all()), 0)

        #create 1 originalfileinfo obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', fileType='SHP', fileCount=3, baseFilename="baseFilename")
        self.assertEqual (len(OriginalFileInfo.objects.all()), 1)

        #may not create any more OriginalFileInfo
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', fileType='ZSHP', fileCount=5, baseFilename="baseFilename2"))

        self.assertEqual (len(OriginalFileInfo.objects.all()), 1)
        #update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', element_id=OriginalFileInfo.objects.first().id, fileType='KML', fileCount=8, baseFilename="baseFilename3")
        self.assertEqual(OriginalFileInfo.objects.first().fileType,'KML')
        self.assertEqual(OriginalFileInfo.objects.first().fileCount,8)
        self.assertEqual(OriginalFileInfo.objects.first().baseFilename,'baseFilename3')

        #delete OriginalCoverage obj
        resource.delete_metadata_element(self.resGeoFeature.short_id,'OriginalFileInfo', element_id=OriginalFileInfo.objects.first().id)
        self.assertEqual (len(OriginalFileInfo.objects.all()), 0)


        # originalcoverage
        #no OriginalCoverage obj
        self.assertEqual (len(OriginalCoverage.objects.all()), 0)

        #create OriginalCoverage obj without a required para: southlimit
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'originalcoverage', northlimit='1',  eastlimit='2',  southlimit='3'))

        #no OriginalCoverage obj
        self.assertEqual (len(OriginalCoverage.objects.all()), 0)

        #create 1 OriginalCoverage obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id,'originalcoverage', northlimit='1',  eastlimit='2',  southlimit='3',  westlimit='4')
        self.assertEqual (len(OriginalCoverage.objects.all()), 1)

        #may not create any more OriginalCoverage
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'originalcoverage', northlimit='1',  eastlimit='2',  southlimit='3',  westlimit='4'))

        self.assertEqual (len(OriginalCoverage.objects.all()), 1)
        #update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id,'originalcoverage', element_id=OriginalCoverage.objects.first().id, northlimit='11',  eastlimit='22',  southlimit='33',  westlimit='44', projection_string='projection_string1', projection_name='projection_name1', datum='datum1', unit='unit1')
        self.assertEqual(OriginalCoverage.objects.first().unit,'unit1')

        #delete OriginalCoverage obj
        resource.delete_metadata_element(self.resGeoFeature.short_id,'originalcoverage', element_id=OriginalCoverage.objects.first().id)
        self.assertEqual (len(OriginalCoverage.objects.all()), 0)



        #GeometryInformation
        #no GeometryInformation obj
        self.assertEqual (len(GeometryInformation.objects.all()), 0)

        #create GeometryInformation obj without a required para: geometryType
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'GeometryInformation', featureCount='1'))

        #no GeometryInformation obj
        self.assertEqual (len(GeometryInformation.objects.all()), 0)

        #create 1 GeometryInformation obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id,'GeometryInformation', featureCount='1', geometryType='Polygon_test')
        self.assertEqual (len(GeometryInformation.objects.all()), 1)

        #may not create any more GeometryInformation
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'GeometryInformation', featureCount='1', geometryType='Polygon_test'))

        #update existing meta
        resource.update_metadata_element(self.resGeoFeature.short_id,'GeometryInformation', element_id=GeometryInformation.objects.first().id,
                                         featureCount='2', geometryType='Point_test')
        self.assertEqual(GeometryInformation.objects.first().geometryType, 'Point_test')
        self.assertEqual(GeometryInformation.objects.first().featureCount, 2)

        #delete GeometryInformation obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'GeometryInformation', element_id=GeometryInformation.objects.first().id)
        self.assertEqual (len(GeometryInformation.objects.all()), 0)


        #FieldInformation
        #no FieldInformation obj
        self.assertEqual (len(FieldInformation.objects.all()), 0)

        #create FieldInformation obj without a required para: geometryType
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.resGeoFeature.short_id,'FieldInformation', fieldName='fieldName0'))

        #no FieldInformation obj
        self.assertEqual (len(FieldInformation.objects.all()), 0)

        #create 1 FieldInformation obj with required para
        resource.create_metadata_element(self.resGeoFeature.short_id,'FieldInformation', fieldName='fieldName1', fieldType='fieldType1')
        self.assertEqual (len(FieldInformation.objects.all()), 1)

        resource.create_metadata_element(self.resGeoFeature.short_id,'FieldInformation', fieldName='fieldName2', fieldType='fieldType2')
        self.assertEqual (len(FieldInformation.objects.all()), 2)

        #update existing meta
        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1')
        self.assertEqual(len(field_info_obj_list), 1)
        field_1_ele_id_old=field_info_obj_list[0].id
        resource.update_metadata_element(self.resGeoFeature.short_id,'FieldInformation', element_id=field_1_ele_id_old,
                                          fieldName='fieldName1_new', fieldType='fieldType1_new')

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1_new')
        self.assertEqual(len(field_info_obj_list), 1)
        field_1_ele_id_new=field_info_obj_list[0].id
        # ele_id should not change
        self.assertEqual(field_1_ele_id_new, field_1_ele_id_old)
        # old value is gone
        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1')
        self.assertEqual(len(field_info_obj_list), 0)


        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName2')
        self.assertEqual(len(field_info_obj_list), 1)
        field_2_ele_id_old=field_info_obj_list[0].id

        self.assertEqual (len(FieldInformation.objects.all()), 2)

        #delete FieldInformation obj
        resource.delete_metadata_element(self.resGeoFeature.short_id, 'FieldInformation', element_id=field_1_ele_id_old)
        self.assertEqual (len(FieldInformation.objects.all()), 1)

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName1_new')
        self.assertEqual(len(field_info_obj_list), 0)

        field_info_obj_list = FieldInformation.objects.filter(fieldName='fieldName2')
        self.assertEqual(len(field_info_obj_list), 1)

        resource.delete_metadata_element(self.resGeoFeature.short_id, 'FieldInformation', element_id=field_2_ele_id_old)
        self.assertEqual (len(FieldInformation.objects.all()), 0)

        #test receivers.py
        #test geofeature_pre_create_resource(sender, **kwargs):

        resource_type="GeographicFeatureResource"
        resource_cls = hydroshare.check_resource_type(resource_type)
        from django.core.files.uploadedfile import UploadedFile
        files = []
        target='hs_geographic_feature_resource/tests/states_shp_sample.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_shp_sample.zip'))
        metadata = []
        validate_files_dict = {"are_files_valid":"", "message":""}
        res_title = "test title"
        url_key = "page_redirect_url"
        page_url_dict, res_title, metadata = hydroshare.utils.resource_pre_create_actions(resource_type=resource_type, files=files,
                                                                    resource_title=res_title,
                                                                    page_redirect_url_key=url_key)

        self.assertEqual (len(files), 7)

        res_list=[]
        for file in ResourceFile.objects.filter(object_id=resource.id):
             res_list.append(file.resource_file)
        for f in ResourceFile.objects.filter(object_id=resource.id):
            hydroshare.delete_resource_file(resource.short_id, f.id, self.user)

        files=[]
        target='hs_geographic_feature_resource/tests/states_shp_sample.zip'
        files.append(UploadedFile(file=open(target, 'r'), name='states_shp_sample.zip'))
        hydroshare.utils.resource_file_add_pre_process(resource, files, self.user,)
        #self.assertEqual (len(resource.files.all()), 7)


        #hydroshare.utils.resource_file_add_process(resource, files, self.user, )






