# -*- coding: utf-8 -*-
import json
import logging

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group

from hs_core import hydroshare

class TestRefTS(TestCase):

    def setUp(self):
        self.logger = logging.getLogger("django")
        self.api_client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.url_to_get_his_urls = "/hsapi/_internal/get-his-urls/"
        self.url_to_search_sites = "/hsapi/_internal/search-sites/"
        self.url_to_search_variables = "/hsapi/_internal/search-variables/"
        self.url_to_time_series_from_service = "/hsapi/_internal/time-series-from-service/"
        self.url_to_create_ref_time_series = "/hsapi/_internal/create-ref-time-series/"
        self.url_to_download_resource_files = "/hsapi/_internal/{0}/download-refts-bag/"

    def test_get_his_central_urls(self):
        self.assertEqual(1, 1)
        resp = self.api_client.get(self.url_to_get_his_urls)
        resp_json = json.loads(resp.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertEqual(len(resp_json["url_list"]) > 0, True)
        self.his_central_urls_list = resp_json["url_list"]

    def test_search_sites(self):
        url_list = [
            "http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx?WSDL"
        ]

        for url in url_list:
            para = {"url": url}
            resp = self.api_client.get(self.url_to_search_sites, para)
            resp_json = json.loads(resp.content)
            self.assertEqual(resp_json["status"], "success", msg="{0} failed to return sites".format(url))
            self.assertEqual(len(resp_json["sites"]) > 0, True, msg="{0} has 0 sites".format(url))

    def test_search_variables(self):
        url = "http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx?WSDL"
        site_list = ['1. Adin Mtn [SNOTEL:301]']
        for site in site_list:
            para = {"url": url, "site": site}
            resp = self.api_client.get(self.url_to_search_variables, para)
            resp_json = json.loads(resp.content)
            self.assertEqual(resp_json["status"], "success")
            self.assertEqual(len(resp_json["variables"]) > 0, True)

    def test_create_resource_hydroserver_lite_1_1(self):
        url = "http://worldwater.byu.edu/interactive/snotel/services/index.php/cuahsi_1_1.asmx?WSDL"
        ref_type = "soap"
        site = '1. Adin Mtn [SNOTEL:301]'
        variable = "1. Temperature (ID:TAVG, Count:11497) [SNOTEL:TAVG:methodCode=1:sourceCode=1:qualityControlLevelCode=1]"

        # login
        self.api_client.login(username='creator', password='mybadpassword')
        self.assertIn('_auth_user_id', self.api_client.session)
        self.assertEqual(int(self.api_client.session['_auth_user_id']), self.user.pk)

        # test create the resource
        para = {"service_url": url, "ref_type": ref_type, "site": site, "variable": variable}
        resp = self.api_client.get(self.url_to_time_series_from_service, para)
        resp_json = json.loads(resp.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertNotEqual(self.api_client.session["ts"], None)

        # test create_ref_time_series
        para = {"title": "HIS Resource title"}
        resp = self.api_client.post(self.url_to_create_ref_time_series, para)
        self.assertEqual(resp.status_code, 302)
        res_landing_page = resp['Location']
        res_landing_page = res_landing_page[res_landing_page.find("/resource"):]
        resp = self.api_client.get(res_landing_page)
        self.logger.exception(res_landing_page)
        self.assertEqual(resp.status_code, 200)

        # test download resource bag
        res_id = res_landing_page[-33:-1]
        self.logger.error(res_id)
        url_to_download_resource_files = self.url_to_download_resource_files.format(res_id)
        self.logger.error(url_to_download_resource_files)
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 200)

        # log out current user and try to download this private res
        self.api_client.logout()
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 401)

    def test_create_resource_hydroserver_1_0(self):
        url = "http://icewater.usu.edu/MudLake/cuahsi_1_0.asmx?WSDL"
        ref_type = "soap"
        site = '2. Bear Lake outlet canal at Lifton [MudLake:USU-ML-Lifton]'
        variable = "11. Solids, total Suspended (ID:USU29, Count:12) [MudLake:USU29:methodCode=15:sourceCode=2:qualityControlLevelCode=1]"

        # login
        self.api_client.login(username='creator', password='mybadpassword')
        self.assertIn('_auth_user_id', self.api_client.session)
        self.assertEqual(int(self.api_client.session['_auth_user_id']), self.user.pk)

        # test create the resource
        para = {"service_url": url, "ref_type": ref_type, "site": site, "variable": variable}
        resp = self.api_client.get(self.url_to_time_series_from_service, para)
        resp_json = json.loads(resp.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertNotEqual(self.api_client.session["ts"], None)

        # test create_ref_time_series
        para = {"title": "HIS Resource title"}
        resp = self.api_client.post(self.url_to_create_ref_time_series, para)
        self.assertEqual(resp.status_code, 302)
        res_landing_page = resp['Location']
        res_landing_page = res_landing_page[res_landing_page.find("/resource"):]
        resp = self.api_client.get(res_landing_page)
        self.logger.exception(res_landing_page)
        self.assertEqual(resp.status_code, 200)

        # test download resource bag
        res_id = res_landing_page[-33:-1]
        self.logger.error(res_id)
        url_to_download_resource_files = self.url_to_download_resource_files.format(res_id)
        self.logger.error(url_to_download_resource_files)
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 200)

        # log out current user and try to download this private res
        self.api_client.logout()
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 401)

    def test_create_resource_hydroserver_1_1(self):
        url = "http://icewater.usu.edu/littlebearriver/cuahsi_1_1.asmx?WSDL"
        ref_type = "soap"
        site = '3. Utah State University Experimental Farm near Wellsville, Utah [LittleBearRiver:USU-LBR-ExpFarm]'
        variable = "15. Relative humidity (ID:USU28, Count:3108) [LittleBearRiver:USU28:methodCode=14:sourceCode=2:qualityControlLevelCode=0]"

        # login
        self.api_client.login(username='creator', password='mybadpassword')
        self.assertIn('_auth_user_id', self.api_client.session)
        self.assertEqual(int(self.api_client.session['_auth_user_id']), self.user.pk)

        # test create the resource
        para = {"service_url": url, "ref_type": ref_type, "site": site, "variable": variable}
        resp = self.api_client.get(self.url_to_time_series_from_service, para)
        resp_json = json.loads(resp.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertNotEqual(self.api_client.session["ts"], None)

        # test create_ref_time_series
        para = {"title": "HIS Resource title"}
        resp = self.api_client.post(self.url_to_create_ref_time_series, para)
        self.assertEqual(resp.status_code, 302)
        res_landing_page = resp['Location']
        res_landing_page = res_landing_page[res_landing_page.find("/resource"):]
        resp = self.api_client.get(res_landing_page)
        self.logger.exception(res_landing_page)
        self.assertEqual(resp.status_code, 200)

        # test download resource bag
        res_id = res_landing_page[-33:-1]
        self.logger.error(res_id)
        url_to_download_resource_files = self.url_to_download_resource_files.format(res_id)
        self.logger.error(url_to_download_resource_files)
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 200)

        # log out current user and try to download this private res
        self.api_client.logout()
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 401)

    def test_create_resource_hydroserver_REST(self):
        url = "http://data.iutahepscor.org/LoganRiverWOF/REST/waterml_2.svc/values?location=iutah:LR_WaterLab_AA&variable=iutah:BattVolt&startDate=2016-01-08T04:45:00Z&endDate=2016-01-11T04:45:00Z"
        ref_type = "rest"
        site = ''
        variable = ""

        # login
        self.api_client.login(username='creator', password='mybadpassword')
        self.assertIn('_auth_user_id', self.api_client.session)
        self.assertEqual(int(self.api_client.session['_auth_user_id']), self.user.pk)

        # test create the resource
        para = {"service_url": url, "ref_type": ref_type, "site": site, "variable": variable}
        resp = self.api_client.get(self.url_to_time_series_from_service, para)
        resp_json = json.loads(resp.content)
        self.assertEqual(resp_json["status"], "success")
        self.assertNotEqual(self.api_client.session["ts"], None)

        # test create_ref_time_series
        para = {"title": "HIS Resource title"}
        resp = self.api_client.post(self.url_to_create_ref_time_series, para)
        self.assertEqual(resp.status_code, 302)
        res_landing_page = resp['Location']
        res_landing_page = res_landing_page[res_landing_page.find("/resource"):]
        resp = self.api_client.get(res_landing_page)
        self.logger.exception(res_landing_page)
        self.assertEqual(resp.status_code, 200)

        # test download resource bag
        res_id = res_landing_page[-33:-1]
        self.logger.error(res_id)
        url_to_download_resource_files = self.url_to_download_resource_files.format(res_id)
        self.logger.error(url_to_download_resource_files)
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 200)

        # log out current user and try to download this private res
        self.api_client.logout()
        resp = self.api_client.get(url_to_download_resource_files)
        self.assertEqual(resp.status_code, 401)
