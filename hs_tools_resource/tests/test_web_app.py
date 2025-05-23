from urllib.parse import urlparse, parse_qs

from django.test import TransactionTestCase, RequestFactory
from django.contrib.auth.models import Group
from django.http import HttpRequest

from hs_core.hydroshare import resource
from hs_core import hydroshare

from hs_tools_resource.models import RequestUrlBase, ToolVersion, SupportedResTypes, ToolResource, \
    ToolIcon, AppHomePageUrl, SupportedSharingStatus, \
    RequestUrlBaseAggregation, SupportedFileExtensions, \
    SupportedAggTypes, RequestUrlBaseFile
from hs_tools_resource.receivers import metadata_element_pre_create_handler, \
    metadata_element_pre_update_handler
from hs_core.hydroshare import create_empty_resource, copy_resource
from hs_tools_resource.utils import parse_app_url_template
from hs_tools_resource.app_launch_helper import resource_level_tool_urls
from hs_core.testing import TestCaseCommonUtilities
from hs_tools_resource.app_keys import tool_app_key
from hs_core.hydroshare.utils import resource_file_add_process


class TestWebAppFeature(TestCaseCommonUtilities, TransactionTestCase):

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

        self.resComposite = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Composite Resource',
            keywords=['kw1', 'kw2'])

        self.test_file_path = 'hs_composite_resource/tests/data/{}'

        self.factory = RequestFactory()

    def test_web_app_res_specific_metadata(self):

        # Class: RequestUrlBase
        # no RequestUrlBase obj
        self.assertEqual(RequestUrlBase.objects.all().count(), 0)

        # create 1 RequestUrlBase obj with required params
        resource.create_metadata_element(self.resWebApp.short_id,
                                         'RequestUrlBase',
                                         value='https://www.google.com')
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

        # Class: ToolVersion
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

        # Class: SupportedResTypes
        # no SupportedResTypes obj
        self.assertEqual(SupportedResTypes.objects.all().count(), 0)

        # create 1 SupportedResTypes obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         supported_res_types=['CompositeResource'])
        self.assertEqual(SupportedResTypes.objects.all().count(), 1)
        # Try creating the 2nd SupportedResTypes obj with required params
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                             supported_res_types=['CompositeResource'])
        self.assertEqual(SupportedResTypes.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         element_id=SupportedResTypes.objects.first().id,
                                         supported_res_types=['CollectionResource'])
        self.assertEqual(SupportedResTypes.objects.first().supported_res_types.all()[0].description,
                         'CollectionResource')

        # try to delete 1st SupportedResTypes obj
        with self.assertRaises(Exception):
            resource.delete_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                             element_id=SupportedResTypes.objects.first().id)
        self.assertEqual(SupportedResTypes.objects.all().count(), 1)

        # Class: ToolIcon
        # verify no ToolIcon obj
        self.assertEqual(ToolIcon.objects.all().count(), 0)

        # no ToolIcon obj
        self.assertEqual(ToolIcon.objects.all().count(), 0)
        logo_sm_url = 'https://storage.googleapis.com/hydroshare-prod-static-media/static/img/logo-sm.png'

        # create 1 ToolIcon obj with required params
        resource.create_metadata_element(self.resWebApp.short_id,
                                         'ToolIcon',
                                         value=logo_sm_url)
        self.assertEqual(ToolIcon.objects.all().count(), 1)

        # may not create additional instance of ToolIcon
        with self.assertRaises(Exception):
            resource. \
                create_metadata_element(self.resWebApp.short_id,
                                        'ToolIcon',
                                        value=logo_sm_url)
        self.assertEqual(ToolIcon.objects.all().count(), 1)

        # update existing meta
        resource. \
            update_metadata_element(self.resWebApp.short_id, 'ToolIcon',
                                    element_id=ToolIcon.objects.first().id,
                                    value=logo_sm_url)
        self.assertEqual(ToolIcon.objects.first().value, logo_sm_url)

        # delete ToolIcon obj
        resource.delete_metadata_element(self.resWebApp.short_id, 'ToolIcon',
                                         element_id=ToolIcon.objects.first().id)
        self.assertEqual(ToolIcon.objects.all().count(), 0)

        # Class: AppHomePageUrl
        # verify no AppHomePageUrl obj
        self.assertEqual(AppHomePageUrl.objects.all().count(), 0)

        # create 1 AppHomePageUrl obj with required params
        resource.create_metadata_element(self.resWebApp.short_id,
                                         'AppHomePageUrl',
                                         value='https://my_web_app.com')
        self.assertEqual(AppHomePageUrl.objects.all().count(), 1)

        # may not create additional instance of AppHomePageUrl
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resWebApp.short_id,
                                             'AppHomePageUrl',
                                             value='https://my_web_app_2.com')
        self.assertEqual(AppHomePageUrl.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resWebApp.short_id, 'AppHomePageUrl',
                                         element_id=AppHomePageUrl.objects.first().id,
                                         value='http://my_web_app_3.com')
        self.assertEqual(AppHomePageUrl.objects.first().value, 'http://my_web_app_3.com')

        # delete AppHomePageUrl obj
        resource.delete_metadata_element(self.resWebApp.short_id, 'AppHomePageUrl',
                                         element_id=AppHomePageUrl.objects.first().id)
        self.assertEqual(AppHomePageUrl.objects.all().count(), 0)

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
        request.POST = {'supportedResTypes': ['Composite Resource']}
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

    def test_bulk_metadata_update(self):
        # here we are testing the update() method of the ToolMetaData class

        self.assertEqual(RequestUrlBase.objects.all().count(), 0)

        # create 1 RequestUrlBase obj with required params
        metadata = []
        metadata.append({'requesturlbase': {'value': 'https://www.google.com'}})
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(RequestUrlBase.objects.all().count(), 1)
        # no ToolVersion obj
        self.assertEqual(ToolVersion.objects.all().count(), 0)

        # create 1 ToolVersion obj with required params
        del metadata[:]
        metadata.append({'toolversion': {'value': '1.0'}})
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(ToolVersion.objects.all().count(), 1)

        # update/create multiple metadata elements
        del metadata[:]
        # no SupportedResTypes obj
        self.assertEqual(SupportedResTypes.objects.all().count(), 0)

        # create SupportedResTypes obj with required params
        metadata.append({'supportedrestypes': {
            'supported_res_types': ['CollectionResource', 'CompositeResource']}})

        # update tool version
        metadata.append({'toolversion': {'value': '2.0'}})
        # do the bulk metadata update
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(SupportedResTypes.objects.all().count(), 1)
        supported_res_type = SupportedResTypes.objects.first()
        for res_type in supported_res_type.supported_res_types.all():
            self.assertIn(res_type.description, ['CollectionResource', 'CompositeResource'])
        self.assertEqual(supported_res_type.supported_res_types.count(), 2)
        self.assertEqual(ToolVersion.objects.first().value, '2.0')

        # test updating SupportedSharingStatus
        del metadata[:]
        self.assertEqual(SupportedSharingStatus.objects.all().count(), 0)
        metadata.append({'supportedsharingstatus': {'sharing_status': ['Public', 'Discoverable']}})
        # do the bulk metadata update
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(SupportedSharingStatus.objects.all().count(), 1)
        supported_sharing_status = SupportedSharingStatus.objects.first()
        for sharing_status in supported_sharing_status.sharing_status.all():
            self.assertIn(sharing_status.description, ['Public', 'Discoverable'])

        # test creating ToolIcon element
        del metadata[:]
        self.assertEqual(ToolIcon.objects.all().count(), 0)

        # create 1 ToolIcon obj with required params
        metadata.append(
            {'toolicon':
             {'value': 'https://storage.googleapis.com/hydroshare-prod-static-media/static/img/logo-sm.png'}})
        # do the bulk metadata update
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(ToolIcon.objects.all().count(), 1)
        self.assertEqual(ToolIcon.objects.first().value,
                         'https://storage.googleapis.com/hydroshare-prod-static-media/static/img/logo-sm.png')

        # test creating AppHomePageURL element
        del metadata[:]
        # verify no AppHomePageUrl obj
        self.assertEqual(AppHomePageUrl.objects.all().count(), 0)

        # create 1 AppHomePageUrl obj with required params
        metadata.append({'apphomepageurl': {'value': 'https://mywebapp.com'}})
        # do the bulk metadata update
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(AppHomePageUrl.objects.all().count(), 1)
        self.assertEqual(AppHomePageUrl.objects.first().value, 'https://mywebapp.com')
        self.resWebApp.delete()

    def test_web_app_extended_metadata_appkey_association(self):
        # testing a resource can be associated with a web app tool resource via
        # appkey name-value additional metadata matching
        self.assertEqual(ToolResource.objects.count(), 1)
        metadata = []
        metadata.append({'requesturlbase': {'value': 'https://www.google.com'}})
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(RequestUrlBase.objects.all().count(), 1)

        self.assertEqual(self.resWebApp.extra_metadata, {})
        self.resWebApp.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resWebApp.save()

        self.assertNotEqual(self.resWebApp.extra_metadata, {})
        self.assertEqual(self.resWebApp.extra_metadata[tool_app_key], 'test-app-value')

        self.assertEqual(self.resComposite.extra_metadata, {})
        self.resComposite.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resComposite.save()

        self.assertNotEqual(self.resComposite.extra_metadata, {})
        self.assertEqual(self.resComposite.extra_metadata[tool_app_key], 'test-app-value')

        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None with appkey '
                                                 'matching')
        tc = relevant_tools['resource_level_app_counter']
        self.assertEqual(tc, 1, msg='open with app counter ' + str(tc) + ' is not 1')
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(tl['res_id'], self.resWebApp.short_id)
        self.assertEqual(tl['agg_types'], '')
        self.assertEqual(tl['file_extensions'], '')

        # delete all extra metadata
        self.resWebApp.extra_metadata = {}
        self.resWebApp.save()
        self.assertEqual(self.resWebApp.extra_metadata, {})

        self.resComposite.extra_metadata = {}
        self.resComposite.save()
        self.assertEqual(self.resComposite.extra_metadata, {})

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNone(relevant_tools, msg='relevant_tools should be None with no appkey '
                                              'matching')

    def test_web_app_extended_metadata_custom_key(self):
        # testing a web resource may contain custom keys
        self.user.ulabels.add_open_with_app(self.resWebApp)
        self.assertEqual(ToolResource.objects.count(), 1)
        metadata = []
        metadata.append({'requesturlbase': {'value': 'https://www.google.com?s=${search_string}'}})
        metadata.append({'supportedrestypes': {
            'supported_res_types': ['CompositeResource']}})
        metadata.append({'supportedsharingstatus': {'sharing_status': ['Private']}})
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(RequestUrlBase.objects.all().count(), 1)

        self.assertEqual(self.resComposite.extra_metadata, {})
        self.resComposite.extra_metadata = {'search_string': 'it works'}
        self.resComposite.save()

        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None')
        tc = relevant_tools['resource_level_app_counter']
        self.assertEqual(tc, 1, msg='open with app counter ' + str(tc) + ' is not 1')
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(tl['res_id'], self.resWebApp.short_id)
        self.assertEqual(tl['agg_types'], '')
        self.assertEqual(tl['file_extensions'], '')
        self.assertEqual(tl['url'], "{'value': 'https://www.google.com?s=it works'}")

        self.resComposite.extra_metadata = {}
        self.resComposite.save()
        self.assertEqual(self.resComposite.extra_metadata, {})

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNone(relevant_tools, msg='relevant_tools should be None with no web app '
                                              'matching')
        # test for default custom key value specified in the web app
        self.resWebApp.extra_metadata = {'search_string': 'it works'}
        self.resWebApp.save()
        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None with a default '
                                                 'web app key')
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(tl['url'], "{'value': 'https://www.google.com?s=it works'}")

        # test for resource override of default custom key value specified in the web app
        self.resComposite.extra_metadata = {'search_string': 'overridden'}
        self.resComposite.save()
        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None with a default '
                                                 'web app key')
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(tl['url'], "{'value': 'https://www.google.com?s=overridden'}")

    def test_utils(self):
        url_template_string = "http://www.google.com/?" \
                              "resid=${HS_RES_ID}&restype=${HS_RES_TYPE}&" \
                              "user=${HS_USR_NAME}"

        term_dict_user = {"HS_USR_NAME": self.user.username}
        new_url_string = parse_app_url_template(url_template_string,
                                                [self.resComposite.get_hs_term_dict(),
                                                 term_dict_user])
        o = urlparse(new_url_string)
        query = parse_qs(o.query)

        self.assertEqual(query["resid"][0], self.resComposite.short_id)
        self.assertEqual(query["restype"][0], "CompositeResource")
        self.assertEqual(query["user"][0], self.user.username)

        url_template_string = "http://www.google.com/?" \
                              "resid=${HS_RES_ID}&restype=${HS_RES_TYPE}&" \
                              "mypara=${HS_UNDEFINED_TERM}&user=${HS_USR_NAME}"
        new_url_string = parse_app_url_template(url_template_string,
                                                [self.resComposite.get_hs_term_dict(),
                                                 term_dict_user])
        self.assertEqual(new_url_string, None)

    def test_utils_parse_app_url_template_None(self):
        term_dict_user = {"HS_USR_NAME": self.user.username}

        url_template_string = None
        new_url_string = parse_app_url_template(url_template_string,
                                                [self.resComposite.get_hs_term_dict(),
                                                 term_dict_user])
        self.assertEqual(new_url_string, None)

    def test_agg_types(self):
        # set url launching pattern for aggregations
        metadata = [{'requesturlbaseaggregation': {
            'value': 'https://www.google.com?agg_path=${HS_AGG_PATH}'}}]
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(RequestUrlBaseAggregation.objects.all().count(), 1)

        # set web app to launch for geo raster
        self.resWebApp.metadata.update(metadata, self.user)
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedAggTypes',
                                         supported_agg_types=['GeoRasterLogicalFile'])

        self.assertEqual(1, SupportedAggTypes.objects.all().count())

        # add a geo raster aggregation to the resource
        open_file = open(self.test_file_path.format("small_logan.tif"), 'rb')
        resource_file_add_process(resource=self.resComposite,
                                  files=(open_file,), user=self.user)

        # setup the web app to be launched by the resource
        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        self.assertEqual(self.resWebApp.extra_metadata, {})
        self.resWebApp.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resWebApp.save()

        self.assertNotEqual(self.resWebApp.extra_metadata, {})
        self.assertEqual(self.resWebApp.extra_metadata[tool_app_key], 'test-app-value')

        self.assertEqual(self.resComposite.extra_metadata, {})
        self.resComposite.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resComposite.save()

        self.assertNotEqual(self.resComposite.extra_metadata, {})
        self.assertEqual(self.resComposite.extra_metadata[tool_app_key], 'test-app-value')

        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        # get the web tools and ensure agg_types is there
        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None with appkey '
                                                 'matching')
        tc = relevant_tools['resource_level_app_counter']
        self.assertEqual(0, tc)
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(self.resWebApp.short_id, tl['res_id'])
        self.assertEqual('GeoRasterLogicalFile', tl['agg_types'])
        self.assertEqual('', tl['file_extensions'])

        # Remove appkey to turn off openwithlist for this resource
        self.resWebApp.extra_metadata = {}
        self.resWebApp.save()

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNone(relevant_tools, msg='relevant_tools should have no approved resources')

    def test_file_extensions(self):
        # set url launching pattern for aggregations
        metadata = [
            {'requesturlbasefile': {'value': 'https://www.google.com?agg_path=${HS_FILE_PATH}'}}]
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(RequestUrlBaseFile.objects.all().count(), 1)

        # set web app to launch for geo raster
        metadata = [{'supportedfileextensions': {'value': '.tif'}}]
        self.resWebApp.metadata.update(metadata, self.user)
        self.assertEqual(SupportedFileExtensions.objects.all().count(), 1)

        # add a geo raster aggregation to the resource
        open_file = open(self.test_file_path.format("small_logan.tif"), 'rb')
        resource_file_add_process(resource=self.resComposite,
                                  files=(open_file,), user=self.user)

        # setup the web app to be launched by the resource
        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        self.assertEqual(self.resWebApp.extra_metadata, {})
        self.resWebApp.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resWebApp.save()

        self.assertNotEqual(self.resWebApp.extra_metadata, {})
        self.assertEqual(self.resWebApp.extra_metadata[tool_app_key], 'test-app-value')

        self.assertEqual(self.resComposite.extra_metadata, {})
        self.resComposite.extra_metadata = {tool_app_key: 'test-app-value'}
        self.resComposite.save()

        self.assertNotEqual(self.resComposite.extra_metadata, {})
        self.assertEqual(self.resComposite.extra_metadata[tool_app_key], 'test-app-value')

        url = '/resource/' + self.resComposite.short_id + '/'
        request = self.factory.get(url)
        request.user = self.user

        # get the web tools
        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNotNone(relevant_tools, msg='relevant_tools should not be None with appkey '
                                                 'matching')
        tc = relevant_tools['resource_level_app_counter']
        self.assertEqual(0, tc)
        tl = relevant_tools['tool_list'][0]
        self.assertEqual(self.resWebApp.short_id, tl['res_id'])
        self.assertEqual('', tl['agg_types'])
        self.assertEqual('.tif', tl['file_extensions'])

        # Remove appkey to turn off openwithlist for this resource
        self.resWebApp.extra_metadata = {}
        self.resWebApp.save()

        relevant_tools = resource_level_tool_urls(self.resComposite, request)
        self.assertIsNone(relevant_tools, msg='relevant_tools should have no approved resources')

    def test_copy(self):

        # create 1 SupportedResTypes obj with required params
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedResTypes',
                                         supported_res_types=['CompositeResource'])
        self.assertEqual(SupportedResTypes.objects.all().count(), 1)

        # set url launching pattern for aggregations
        metadata = [{'requesturlbaseaggregation': {
            'value': 'https://www.google.com?agg_path=${HS_AGG_PATH}'}}]
        self.resWebApp.metadata.update(metadata, self.user)
        resource.create_metadata_element(self.resWebApp.short_id, 'SupportedAggTypes',
                                         supported_agg_types=['GeoRasterLogicalFile'])

        self.assertEqual(1, SupportedAggTypes.objects.all().count())

        # make a new copy of web app
        new_web_app = create_empty_resource(self.resWebApp.short_id, self.user,
                                            action='copy')

        new_web_app = copy_resource(self.resWebApp, new_web_app)

        # test the new copy is a web app
        self.assertTrue(isinstance(new_web_app, ToolResource))
        # test that added types are copied
        self.assertEqual(2, SupportedResTypes.objects.all().count())
        self.assertEqual(2, SupportedAggTypes.objects.all().count())
