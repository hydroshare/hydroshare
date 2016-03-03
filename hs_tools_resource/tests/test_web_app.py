__author__ = 'shawn'

from urlparse import urlparse, parse_qs

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import Group, User
from django.http import HttpRequest, QueryDict

from hs_core.hydroshare import resource
from hs_core import hydroshare

from hs_tools_resource.models import RequestUrlBase, ToolVersion, SupportedResTypes, ToolResource, ToolIcon
from hs_tools_resource.receivers import metadata_element_pre_create_handler, metadata_element_pre_update_handler
from hs_tools_resource.utils import parse_app_url_template

class TestWebAppFeature(TransactionTestCase):

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'scrawley@byu.edu',
                username='scrawley',
                first_name='Shawn',
                last_name='Crawley',
                superuser=False,
                groups=[self.group]
        )
        self.allowance = 0.00001

        self.resWebApp = hydroshare.create_resource(
                resource_type='ToolResource',
                owner=self.user,
                title='Test Web App Resource',
                keywords=['kw1', 'kw2'])

        self.resGeneric = hydroshare.create_resource(
                resource_type='GenericResource',
                owner=self.user,
                title='Test Generic Resource',
                keywords=['kw1', 'kw2'])

    def test_web_app_res_specific_metadata(self):

        #######################
        # Class: RequestUrlBase
        #######################
        # no RequestUrlBase obj
        self.assertEqual(RequestUrlBase.objects.all().count(), 0)

        # create 1 RequestUrlBase obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'RequestUrlBase', value='https://www.google.com')
        self.assertEqual(RequestUrlBase.objects.all().count(), 1)

        # may not create additional instance of RequestUrlBase
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resWebApp.short_id, 'RequestUrlBase',
                                             value='https://www.facebook.com')

        self.assertEqual(RequestUrlBase.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'RequestUrlBase',
                                         element_id=RequestUrlBase.objects.first().id,
                                         value='https://www.yahoo.com')
        self.assertEqual(RequestUrlBase.objects.first().value, 'https://www.yahoo.com')

        # delete RequestUrlBase obj
        resource.delete_metadata_element(self.resWebApp.short_id, 'RequestUrlBase',
                                         element_id=RequestUrlBase.objects.first().id)
        self.assertEqual(RequestUrlBase.objects.all().count(), 0)

        ####################
        # Class: ToolVersion
        ####################
        # verify no ToolVersion obj
        self.assertEqual(ToolVersion.objects.all().count(), 0)

        # no ToolVersion obj
        self.assertEqual(ToolVersion.objects.all().count(), 0)

        # create 1 ToolVersion obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'ToolVersion', value='1.0')
        self.assertEqual(ToolVersion.objects.all().count(), 1)

        # may not create additional instance of ToolVersion
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resWebApp.short_id, 'ToolVersion', value='2.0')
        self.assertEqual(ToolVersion.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'ToolVersion',
                                         element_id=ToolVersion.objects.first().id,
                                         value='3.0')
        self.assertEqual(ToolVersion.objects.first().value, '3.0')

        # delete ToolVersion obj
        resource.delete_metadata_element(self.resWebApp.short_id, 'ToolVersion',
                                         element_id=ToolVersion.objects.first().id)
        self.assertEqual(ToolVersion.objects.all().count(), 0)

        ##########################
        # Class: SupportedResTypes
        ##########################
        # no SupportedResTypes obj
        self.assertEqual(SupportedResTypes.objects.all().count(), 0)

        # create 2 SupportedResTypes obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         supported_res_types=['NetCDF Resource'])
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         supported_res_types=['NetCDF Resource'])
        self.assertEqual(SupportedResTypes.objects.all().count(), 2)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         element_id=SupportedResTypes.objects.first().id,
                                         supported_res_types=['Time Series Resource'])
        self.assertEqual(SupportedResTypes.objects.first().supported_res_types.all()[0].description,
                         'Time Series Resource')

        # try to delete 1st SupportedResTypes obj
        with self.assertRaises(Exception):
            resource.delete_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                             element_id=SupportedResTypes.objects.first().id)
        self.assertEqual(SupportedResTypes.objects.all().count(), 2)

        ####################
        # Class: ToolIcon
        ####################
        # verify no ToolIcon obj
        self.assertEqual(ToolIcon.objects.all().count(), 0)

        # no ToolIcon obj
        self.assertEqual(ToolIcon.objects.all().count(), 0)

        # create 1 ToolIcon obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'ToolIcon', url='https://test_icon_url.png')
        self.assertEqual(ToolIcon.objects.all().count(), 1)

        # may not create additional instance of ToolIcon
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resWebApp.short_id, 'ToolIcon', url='https://test_icon_url_2.png')
        self.assertEqual(ToolIcon.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'ToolIcon',
                                         element_id=ToolIcon.objects.first().id,
                                         url='https://test_icon_url_3.png')
        self.assertEqual(ToolIcon.objects.first().url, 'https://test_icon_url_3.png')

        # delete ToolIcon obj
        resource.delete_metadata_element(self.resWebApp.short_id, 'ToolIcon',
                                         element_id=ToolIcon.objects.first().id)
        self.assertEqual(ToolIcon.objects.all().count(), 0)

    def test_metadata_element_pre_create_and_update(self):
        request = HttpRequest()

        # RequestUrlBase
        request.POST = {'value': 'https://www.msn.com'}

        data = metadata_element_pre_create_handler(sender=ToolResource,
                                                   element_name="RequestUrlBase",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=ToolResource,
                                                   element_name="RequestUrlBase",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        # ToolVersion
        request.POST = {'value': '4.0'}

        data = metadata_element_pre_create_handler(sender=ToolResource,
                                                   element_name="ToolVersion",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=ToolResource,
                                                   element_name="ToolVersion",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        # SupportedResTypes
        request.POST = {'supportedResTypes': ['NetCDF Resource']}
        data = metadata_element_pre_create_handler(sender=ToolResource,
                                                   element_name="SupportedResTypes",
                                                   request=request)
        self.assertTrue(data["is_valid"])
        data = metadata_element_pre_update_handler(sender=ToolResource,
                                                   element_name="SupportedResTypes",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        # ToolIcon
        request.POST = {'icon': 'https://test_icon_url_3.png'}

        data = metadata_element_pre_create_handler(sender=ToolResource,
                                                   element_name="ToolIcon",
                                                   request=request)
        self.assertTrue(data["is_valid"])

    def test_utils(self):
        url_template_string = "http://www.google.com/?resid=${HS_RES_ID}&restype=${HS_RES_TYPE}&user=${HS_USR_NAME}"

        term_dict_user = {"HS_USR_NAME": self.user.username}
        new_url_string = parse_app_url_template(url_template_string, [self.resGeneric.get_hs_term_dict(), term_dict_user])
        o = urlparse(new_url_string)
        query = parse_qs(o.query)

        self.assertEqual(query["resid"][0], self.resGeneric.short_id)
        self.assertEqual(query["restype"][0], "GenericResource")
        self.assertEqual(query["user"][0], self.user.username)

        url_template_string = "http://www.google.com/?resid=${HS_RES_ID}&restype=${HS_RES_TYPE}&mypara=${HS_UNDEFINED_TERM}&user=${HS_USR_NAME}"
        new_url_string = parse_app_url_template(url_template_string, [self.resGeneric.get_hs_term_dict(), term_dict_user])
        self.assertEqual(new_url_string, None)