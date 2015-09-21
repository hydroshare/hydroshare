__author__ = 'shaun'

from unittest import TestCase
from django.contrib.contenttypes.models import ContentType
from hs_core.hydroshare import utils, users, resource
from hs_core.models import BaseResource, Creator, Contributor, CoreMetaData, \
    Coverage, Rights, Title, Language, Publisher, Identifier, \
    Type, Subject, Description, Date, Format, Relation, Source

from ref_ts.models import Method, QualityControlLevel, Variable, Site

from django.contrib.auth.models import Group, User
from hs_core import hydroshare
from dateutil import parser
from lxml import etree


class TestRefTSMetadata(TestCase):
    def setUp(self):
        try:
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


        self.res = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            owner=self.user,
            title='Test RefTimeSeries Resource',
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
        Variable.objects.all().delete()

    def test_method_metadata(self):
        # create an element
        #resource.create_metadata_element(self.res.short_id, 'method', value='blerg')
        # test if it's there
        # test it's values
        # delete it
        # test if it's gone
        pass

    def test_quality_metadata(self):
        # create an element
        # test if it's there
        # test it's values
        # delete it
        # test if it's gone
        pass

    def test_variable_metadata(self):
        # create an element
        # test if it's there
        # test it's values
        # delete it
        # test if it's gone
        pass

    def test_site_metadata(self):
        # create an element
        # test if it's there
        # test it's values
        # delete it
        # test if it's gone
        pass

    # def test_refts_metadata(self):
    #     # add a type element
    #     resource.create_metadata_element(self.res.short_id, 'type', url="http://hydroshare.org/netcdf")
    #
    #     # add another creator with all sub_elements
    #     cr_name = 'Mike Sundar'
    #     cr_des = 'http://hydroshare.org/user/001'
    #     cr_org = "USU"
    #     cr_email = 'mike.sundar@usu.edu'
    #     cr_address = "11 River Drive, Logan UT-84321, USA"
    #     cr_phone = '435-567-0989'
    #     cr_homepage = 'http://usu.edu/homepage/001'
    #     cr_res_id = 'http://research.org/001'
    #     cr_res_gate_id = 'http://research-gate.org/001'
    #     resource.create_metadata_element(self.res.short_id,'creator',
    #                                      name=cr_name,
    #                                      description=cr_des,
    #                                      organization=cr_org,
    #                                      email=cr_email,
    #                                      address=cr_address,
    #                                      phone=cr_phone,
    #                                      homepage=cr_homepage,
    #                                      researcherID=cr_res_id,
    #                                      researchGateID=cr_res_gate_id)
    #
    #     # add another creator with only the name
    #     resource.create_metadata_element(self.res.short_id,'creator', name='Lisa Holley')
    #
    #     #test adding a contributor with all sub_elements
    #     con_name = 'Sujan Peterson'
    #     con_des = 'http://hydroshare.org/user/002'
    #     con_org = "USU"
    #     con_email = 'sujan.peterson@usu.edu'
    #     con_address = "101 Center St, Logan UT-84321, USA"
    #     con_phone = '435-567-3245'
    #     con_homepage = 'http://usu.edu/homepage/009'
    #     con_res_id = 'http://research.org/009'
    #     con_res_gate_id = 'http://research-gate.org/009'
    #     resource.create_metadata_element(self.res.short_id,'contributor',
    #                                      name=con_name,
    #                                      description=con_des,
    #                                      organization=con_org,
    #                                      email=con_email,
    #                                      address=con_address,
    #                                      phone=con_phone,
    #                                      homepage=con_homepage,
    #                                      researcherID=con_res_id,
    #                                      researchGateID=con_res_gate_id)
    #
    #     # add another creator with only the name
    #     resource.create_metadata_element(self.res.short_id,'contributor', name='Andrew Smith')
    #
    #     # add a period type coverage
    #     # add a period type coverage
    #     value_dict = {'name':'Name for period coverage' , 'start':'1/1/2000', 'end':'12/12/2012'}
    #     resource.create_metadata_element(self.res.short_id,'coverage', type='period', value=value_dict)
    #
    #     # add a point type coverage
    #     value_dict = {'name':'Name for point coverage', 'east':'56.45678', 'north':'12.6789'}
    #     resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)
    #
    #     # add date of type 'valid'
    #     resource.create_metadata_element(self.res.short_id,'date', type='valid', start_date='8/10/2011', end_date='8/11/2012')
    #
    #     # add a format element
    #     format_nc = 'netcdf'
    #     resource.create_metadata_element(self.res.short_id,'format', value=format_nc)
    #
    #     # add 'DOI' identifier
    #     #resource.create_metadata_element(self.res.short_id,'identifier', name='DOI', url="http://dx.doi.org/001")
    #
    #     # add a language element
    #     resource.create_metadata_element(self.res.short_id,'language', code='eng')
    #
    #     # add 'Publisher' element
    #     original_file_name = 'original.txt'
    #     original_file = open(original_file_name, 'w')
    #     original_file.write("original text")
    #     original_file.close()
    #
    #     original_file = open(original_file_name, 'r')
    #     # add the file to the resource
    #     hydroshare.add_resource_files(self.res.short_id, original_file)
    #     resource.create_metadata_element(self.res.short_id,'publisher', name="HydroShare", url="http://hydroshare.org")
    #
    #     # add a relation element of uri type
    #     resource.create_metadata_element(self.res.short_id,'relation', type='isPartOf',
    #                                      value='http://hydroshare.org/resource/001')
    #
    #     # add another relation element of non-uri type
    #     resource.create_metadata_element(self.res.short_id,'relation', type='isDataFor',
    #                                      value='This resource is for another resource')
    #
    #
    #     # add a source element of uri type
    #     resource.create_metadata_element(self.res.short_id,'source', derived_from='http://hydroshare.org/resource/0002')
    #
    #     # add a rights element
    #     resource.create_metadata_element(self.res.short_id,'rights', statement='This is the rights statement for this resource',
    #                                      url='http://rights.ord/001')
    #
    #     # add a subject element
    #     resource.create_metadata_element(self.res.short_id,'subject', value='sub-1')
    #
    #     # add another subject element
    #     resource.create_metadata_element(self.res.short_id,'subject', value='sub-2')
    #
    #     # add a netcdf specific element (variable)
    #     resource.create_metadata_element(self.res.short_id,'variable', name='temp', unit='deg C', type='float', shape='shape_unknown')
    #
    #     print self.res.metadata.get_xml()
