from django.test import TransactionTestCase, RequestFactory
from django.contrib.auth.models import Group

from hs_core import hydroshare

from hs_tools_resource.models import RequestUrlBase, RequestUrlBaseFile, \
    RequestUrlBaseAggregation, SupportedFileExtensions
from hs_core.testing import TestCaseCommonUtilities
from django.core.urlresolvers import reverse

from hs_core.views import add_metadata_element, update_metadata_element
from rest_framework import status


class TestWebAppValidationFeature(TestCaseCommonUtilities, TransactionTestCase):

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

        self.factory = RequestFactory()

    def test_file_level_keys_add_good(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_FILE_PATH}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_FILE_PATH}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbasefile", 'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbasefile")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseFile.objects.all().count())

    def test_file_level_keys_add_bad(self):
        bad_url = 'https://www.google.com?' \
                  'file_id=${BAD_KEY}'

        post_data = {'value': bad_url}
        url_params = {'element_name': "requesturlbasefile", 'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbasefile")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(0, RequestUrlBaseFile.objects.all().count())

    def test_file_level_keys_update(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_FILE_PATH}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_FILE_PATH}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbasefile", 'shortkey': self.resWebApp.short_id}

        # add url
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbasefile")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseFile.objects.all().count())
        self.assertEqual(good_url, RequestUrlBaseFile.objects.first().value)

        # update good url
        url_params["element_id"] = 1
        url = reverse('update_metadata_element', kwargs=url_params)
        updated_url = 'https://www.google.com?file_id=${HS_FILE_PATH}'
        post_data = {'value': updated_url}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        id = RequestUrlBaseFile.objects.first().id
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbasefile",
                                           element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseFile.objects.all().count())
        self.assertEqual(updated_url, RequestUrlBaseFile.objects.first().value)

        # update bad url
        url = reverse('update_metadata_element', kwargs=url_params)
        post_data = {'value': 'https://www.google.com?file_id=${BAD_KEY}'}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbasefile", element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseFile.objects.all().count())
        # ensure it did not change
        self.assertEqual(updated_url, RequestUrlBaseFile.objects.first().value)

    def test_aggregation_level_keys_add_good(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_RES_ID}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_AGG_PATH}' \
                   '&main=${HS_MAIN_FILE}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbaseaggregation",
                      'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbaseaggregation")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseAggregation.objects.all().count())

    def test_aggregation_level_keys_add_bad(self):
        bad_url = 'https://www.google.com?' \
                  'file_id=${BAD_KEY}'

        post_data = {'value': bad_url}
        url_params = {'element_name': "requesturlbaseaggregation",
                      'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbaseaggregation")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(0, RequestUrlBaseAggregation.objects.all().count())

    def test_aggregation_level_keys_update(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_RES_ID}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_AGG_PATH}' \
                   '&main=${HS_MAIN_FILE}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbaseaggregation",
                      'shortkey': self.resWebApp.short_id}

        # add url
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbaseaggregation")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseAggregation.objects.all().count())
        self.assertEqual(good_url, RequestUrlBaseAggregation.objects.first().value)

        # update good url
        url_params["element_id"] = 1
        url = reverse('update_metadata_element', kwargs=url_params)
        updated_url = 'https://www.google.com?file_id=${HS_AGG_PATH}'
        post_data = {'value': updated_url}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        id = RequestUrlBaseAggregation.objects.first().id
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbaseaggregation",
                                           element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseAggregation.objects.all().count())
        self.assertEqual(updated_url, RequestUrlBaseAggregation.objects.first().value)

        # update bad url
        url = reverse('update_metadata_element', kwargs=url_params)
        post_data = {'value': 'https://www.google.com?file_id=${BAD_KEY}'}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbaseaggregation", element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBaseAggregation.objects.all().count())
        # ensure it did not change
        self.assertEqual(updated_url, RequestUrlBaseAggregation.objects.first().value)

    def test_resource_level_keys_add_good(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_RES_ID}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_FILE_NAME}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbase", 'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbase")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBase.objects.all().count())

    def test_resource_level_keys_add_bad(self):
        bad_url = 'https://www.google.com?' \
                  'file_id=${BAD_KEY}'

        post_data = {'value': bad_url}
        url_params = {'element_name': "requesturlbase", 'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbase")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(0, RequestUrlBase.objects.all().count())

    def test_resource_level_keys_update(self):
        good_url = 'https://www.google.com?' \
                   'file_id=${HS_RES_ID}' \
                   '&res_id=${HS_RES_TYPE}' \
                   '&usr=${HS_USR_NAME}' \
                   '&fil=${HS_FILE_NAME}'

        post_data = {'value': good_url}
        url_params = {'element_name': "requesturlbase", 'shortkey': self.resWebApp.short_id}

        # add url
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="requesturlbase")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBase.objects.all().count())
        self.assertEqual(good_url, RequestUrlBase.objects.first().value)

        # update good url
        url_params["element_id"] = 1
        url = reverse('update_metadata_element', kwargs=url_params)
        updated_url = 'https://www.google.com?file_id=${HS_FILE_NAME}'
        post_data = {'value': updated_url}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        id = RequestUrlBase.objects.first().id
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbase",
                                           element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBase.objects.all().count())
        self.assertEqual(updated_url, RequestUrlBase.objects.first().value)

        # update bad url
        url = reverse('update_metadata_element', kwargs=url_params)
        post_data = {'value': 'https://www.google.com?file_id=${BAD_KEY}'}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbase", element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, RequestUrlBase.objects.all().count())
        # ensure it did not change
        self.assertEqual(updated_url, RequestUrlBase.objects.first().value)

    def test_file_extensions_update(self):
        good_extensions = '.tif, .txt,.html'

        post_data = {'value': good_extensions}
        url_params = {'element_name': "supportedfileextensions",
                      'shortkey': self.resWebApp.short_id}

        # add extensions
        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="supportedfileextensions")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, SupportedFileExtensions.objects.all().count())
        self.assertEqual(good_extensions, SupportedFileExtensions.objects.first().value)

        # update good extensions
        url_params["element_id"] = 1
        url = reverse('update_metadata_element', kwargs=url_params)
        updated_extensions = '.tif, .txt,.html, .yaml'
        post_data = {'value': updated_extensions}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        id = SupportedFileExtensions.objects.first().id
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="supportedfileextensions",
                                           element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, SupportedFileExtensions.objects.all().count())
        self.assertEqual(updated_extensions, SupportedFileExtensions.objects.first().value)

        # update bad extension
        url = reverse('update_metadata_element', kwargs=url_params)
        post_data = {'value': '.tif, htm'}
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = update_metadata_element(request, shortkey=self.resWebApp.short_id,
                                           element_name="requesturlbase", element_id=id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, SupportedFileExtensions.objects.all().count())
        # ensure it did not change
        self.assertEqual(updated_extensions, SupportedFileExtensions.objects.first().value)

    def test_file_extensions_add_good(self):
        good_extensions = '.tif, .html'

        post_data = {'value': good_extensions}
        url_params = {'element_name': "supportedfileextensions",
                      'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="supportedfileextensions")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(1, SupportedFileExtensions.objects.all().count())

    def test_file_extensions_add_bad(self):
        bad_extensions = 'tif, html'

        post_data = {'value': bad_extensions}
        url_params = {'element_name': "supportedfileextensions",
                      'shortkey': self.resWebApp.short_id}

        url = reverse('add_metadata_element', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'http_referer'
        response = add_metadata_element(request, shortkey=self.resWebApp.short_id,
                                        element_name="supportedfileextensions")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(0, SupportedFileExtensions.objects.all().count())
