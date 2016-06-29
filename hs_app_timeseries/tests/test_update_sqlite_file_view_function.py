import os
import tempfile
import shutil

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from rest_framework import status

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_app_timeseries.views import update_sqlite_file


class TestUpdateSQLiteFile(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestUpdateSQLiteFile, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.temp_dir = tempfile.mkdtemp()
        self.odm2_sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_file_name)
        shutil.copy(self.odm2_sqlite_file, target_temp_sqlite_file)
        self.odm2_sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        # create a timeseries resource
        self.resTimeSeries = hydroshare.create_resource(
            resource_type='TimeSeriesResource',
            owner=self.john,
            title='Test Time Series Resource',
            files=(UploadedFile(file=self.odm2_sqlite_file_obj, name=self.odm2_sqlite_file_name),)
        )

        self.genResource = hydroshare.create_resource(resource_type='GenericResource',
                                                      owner=self.john,
                                                      title='Test Resource',
                                                      metadata=[]
                                                     )

        self.factory = RequestFactory()

    def tearDown(self):
        super(TestUpdateSQLiteFile, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_sqlite_file(self):
        url = reverse('update_sqlite_file', kwargs={'resource_id': self.resTimeSeries.short_id})
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self._set_request_message_attributes(request)
        request.user = self.john
        response = update_sqlite_file(request, resource_id=self.resTimeSeries.short_id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_update_sqlite_file_exception(self):
        # trying to update sqlite file for non timeseries resource should raise exception
        url = reverse('update_sqlite_file', kwargs={'resource_id': self.genResource.short_id})
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self._set_request_message_attributes(request)
        request.user = self.john
        with self.assertRaises(ValidationError):
            update_sqlite_file(request, resource_id=self.genResource.short_id)

    def _set_request_message_attributes(self, request):
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
