# -*- coding: utf-8 -*-
from tastypie.test import ResourceTestCase
from tastypie.test import TestApiClient
from django.test import Client
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import GenericResource
from tastypie.serializers import Serializer
import urllib
import logging
from ref_ts.models import RefTimeSeries


class RefTSGetSites(ResourceTestCase):

    def setUp(self):
        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = TestApiClient()

        self.client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.wsdl_url_swe = "http://hydroportal.cuahsi.org/SwedishMonitoringData/webapp/cuahsi_1_1.asmx?WSDL"
        self.wsdl_url_wwo = "http://worldwater.byu.edu/app/index.php/default/services/cuahsi_1_1.asmx?WSDL"
        self.rest_url = "http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx/GetValues?location=WWO:S-PRHD&variable=WWO:JSWL&startDate=&endDate="
        self.site_code_swe = "wq2371"
        self.site_code_wwo = "S-PRHD"

        self.post_data = {
            'title': 'My REST API-created resource',
            'resource_type': 'GenericResource'
        }

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    #TODO: This throws an encoding error...
    # def test_get_sites_wwo(self):
    #     resp = self.api_client.get("/hsapi/_internal/search-sites/?wsdl_url="+self.wsdl_url_wwo)
    #     self.assertEqual(resp.status_code, 200)

    def test_get_sites_swedish(self):
        resp = self.api_client.get("/hsapi/_internal/search-sites/?url="+self.wsdl_url_swe)
        self.assertEqual(resp.status_code, 200)

    def test_get_variables_wwo(self):
        resp = self.api_client.get("/hsapi/_internal/search-variables/?url="+self.wsdl_url_wwo+"&site="+self.site_code_wwo)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Water level' in resp.content)



class RefTSSnotel(ResourceTestCase):

    def setUp(self):
        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = TestApiClient()

        self.client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.wsdl_url = "http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx?WSDL"
        self.rest_url = "http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx/GetValuesObject?location=SNOTEL:1039&variable=SNOTEL:WTEQ&startDate=2014-10-01&endDate=2015-03-19"
        self.time_series_base_rest = "/hsapi/_internal/time-series-from-service/?ref_type=rest&service_url="
        self.time_series_base_soap = "/hsapi/_internal/time-series-from-service/?ref_type=soap&service_url="
        self.site_code_swe = "wq2371"
        self.site_code_wwo = "S-PRHD"

        self.post_data = {
            'title': 'My REST API-created resource',
            'resource_type': 'GenericResource'
        }

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_time_series_from_service_rest(self):
        url = urllib.quote(self.rest_url)
        resp = self.api_client.get(self.time_series_base_rest+url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)

    def test_time_series_from_service_soap(self):
        url = urllib.quote(self.wsdl_url)
        resp = self.api_client.get(self.time_series_base_soap+url+"&site=823&variable=WTEQ")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)



class RefTSGetDataViews(ResourceTestCase):

    def setUp(self):
        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = TestApiClient()

        self.client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.wsdl_url_swe = "http://hydroportal.cuahsi.org/SwedishMonitoringData/webapp/cuahsi_1_1.asmx?WSDL"
        self.wsdl_url_wwo = "http://worldwater.byu.edu/app/index.php/default/services/cuahsi_1_1.asmx?WSDL"
        self.rest_url = "http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx/GetValues?location=WWO:S-PRHD&variable=WWO:JSWL&startDate=&endDate="
        self.site_code_swe = "wq2371"
        self.site_code_wwo = "S-PRHD"

        self.post_data = {
            'title': 'My REST API-created resource',
            'resource_type': 'GenericResource'
        }

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    #TODO: This throws an encoding error...
    # def test_get_sites_wwo(self):
    #     resp = self.api_client.get("/hsapi/_internal/search-sites/?wsdl_url="+self.wsdl_url_wwo)
    #     self.assertEqual(resp.status_code, 200)

    def test_get_sites_swedish(self):
        resp = self.api_client.get("/hsapi/_internal/search-sites/?url="+self.wsdl_url_swe)
        self.assertEqual(resp.status_code, 200)

    def test_get_variables_wwo(self):
        resp = self.api_client.get("/hsapi/_internal/search-variables/?url="+self.wsdl_url_wwo+"&site="+self.site_code_wwo)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Water level' in resp.content)

    #TODO: this has the same encoding error though it works through the interface...
    # def test_get_variables_swedish(self):
    #     resp = self.api_client.get("/hsapi/_internal/search-variables/?wsdl_url="+self.wsdl_url_swe+"&site="+self.site_code_swe)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertEqual('Water level', resp.content)

    def test_time_series_from_service_rest_world_water(self):
        url = urllib.quote('http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx/GetValues?location=WWO:S-PRHD&variable=WWO:JSWL&startDate=&endDate=')
        resp = self.api_client.get("/hsapi/_internal/time-series-from-service/?ref_type=rest&service_url="+url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)

    def test_time_series_from_service_rest_jeff_h(self):
        url = urllib.quote('http://data.iutahepscor.org/RedButteCreekWOF/REST/waterml_1_1.svc/datavalues?location=iutah:RB_ARBR_C&variable=iutah:AirTemp_Avg/methodCode=1/sourceCode=1/qualityControlLevelCode=0&startDate=&endDate=')
        resp = self.api_client.get("/hsapi/_internal/time-series-from-service/?ref_type=rest&service_url="+url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)

    def test_time_series_from_service_rest_jiri(self):
        url = urllib.quote('http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValues?location=CHMI-H:89&variable=CHMI-H:PRUTOK&startDate=2015-01-01&endDate=2015-03-01&authToken=')
        resp = self.api_client.get("/hsapi/_internal/time-series-from-service/?ref_type=rest&service_url="+url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)

    def test_time_series_from_service_rest_snotel(self):
        url = urllib.quote('http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx/GetValuesObject?location=SNOTEL:823&variable=SNOTEL:WTEQ&startDate=2014-10-01&endDate=2015-03-17')
        resp = self.api_client.get("/hsapi/_internal/time-series-from-service/?ref_type=rest&service_url="+url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('visualization' in resp.content)

class TestCreateRefTSView(ResourceTestCase):

    def setUp(self):
        RefTimeSeries.objects.all().delete()

        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.api_client.login(username=self.username, password=self.password)

                # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            title='My resource',
            owner=self.user_creator,
        )



    def tearDown(self):
        User.objects.all().delete()
        RefTimeSeries.objects.all().delete()

    def test_create_ref_time_series_wwo_rest(self):
        post_data = {
            'url': 'http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx/GetValues?location=WWO:S-PRHD&variable=WWO:JSWL&startDate=&endDate=',
            'short_id': self.resource.short_id,
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)

    def test_create_ref_time_series_wwo_soap(self):
        post_data = {
            'url': 'http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx?WSDL',
            'short_id': self.resource.short_id,
            'site': 'Provo River Harbor Drive: S-PRHD',
            'variable': 'Water level: JSWL',
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)

    def test_create_ref_time_series_jiri_rest(self):
        post_data = {
            'url': 'http://hydrodata.info/chmi-h/cuahsi_1_1.asmx/GetValues?location=CHMI-H:89&variable=CHMI-H:PRUTOK&startDate=2015-01-01&endDate=2015-03-01&authToken=',
            'short_id': self.resource.short_id,
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }

        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)

    def test_create_ref_time_series_jeffh_rest(self):
        post_data = {
            'url': 'http://data.iutahepscor.org/RedButteCreekWOF/REST/waterml_1_1.svc/datavalues?location=iutah:RB_ARBR_C&variable=iutah:AirTemp_Avg/methodCode=1/sourceCode=1/qualityControlLevelCode=0&startDate=&endDate=',
            'short_id': self.resource.short_id,
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)


class TestCzech(ResourceTestCase):

    def setUp(self):
        RefTimeSeries.objects.all().delete()

        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.api_client.login(username=self.username, password=self.password)

                # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            title='My resource',
            owner=self.user_creator,
        )



    def tearDown(self):
        User.objects.all().delete()
        RefTimeSeries.objects.all().delete()

    def test_create_ref_time_series_wwo_rest(self):
        post_data = {
            'url': 'http://hydrodata.info/chmi-d/cuahsi_1_1.asmx/GetValuesObject?location=CHMI-D:1&variable=CHMI-D:SNIH&startDate=2014-11-01&endDate=2015-03-27&authToken=',
            'short_id': self.resource.short_id,
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)

    def test_create_ref_time_series_czech_soap(self):
        site = 'Labská bouda: 1'
        post_data = {
            'url': 'http://hydrodata.info/chmi-d/cuahsi_1_1.asmx?WSDL',
            'short_id': self.resource.short_id,
            'site': site.decode('utf-8'),
            'variable': 'Snow depth: SNIH',
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)

    def test_create_ref_time_series_wwo_soap(self):
        post_data = {
            'url': 'http://worldwater.byu.edu/interactive/sandbox/services/index.php/cuahsi_1_1.asmx?WSDL',
            'short_id': self.resource.short_id,
            'site': 'Provo River Harbor Drive: S-PRHD',
            'variable': 'Water level: JSWL',
            'metadata': """[{'title': {'value': u'example title'}}, {'language': {'code': 'eng'}}, {'rights': {'url': 'http://creativecommons.org/licenses/by/4.0/', 'statement': 'This resource is shared under the Creative Commons Attribution CC BY.'}}]""",
            'title': 'example title'
        }
        resp = self.api_client.post("/hsapi/_internal/create-ref-time-series/", post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('example title' in resp.content)
