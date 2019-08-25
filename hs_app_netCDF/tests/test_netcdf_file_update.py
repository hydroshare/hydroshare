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
from hs_core.views import update_key_value_metadata
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.hydroshare import utils

from hs_app_netCDF.views import update_netcdf_file


class TestUpdateNetcdfFile(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestUpdateNetcdfFile, self).setUp()
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
        self.netcdf_file_name = 'netcdf_file_update.nc'
        self.netcdf_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_file_name)
        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

        self.genResource = hydroshare.create_resource(resource_type='GenericResource',
                                                      owner=self.john,
                                                      title='Test Resource',
                                                      metadata=[])

        self.factory = RequestFactory()

    def tearDown(self):
        super(TestUpdateNetcdfFile, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_netcdf_file(self):
        # create a netcdf resource
        files = [UploadedFile(file=self.netcdf_file_obj, name=self.netcdf_file_name)]
        _, _, metadata = utils.resource_pre_create_actions(
            resource_type='NetcdfResource',
            resource_title='Untitled resource',
            page_redirect_url_key=None,
            files=files,
            metadata=None,)

        self.resNetcdf = hydroshare.create_resource(
            'NetcdfResource',
            self.john,
            'Untitled resource',
            files=files,
            metadata=metadata
            )

        utils.resource_post_create_actions(self.resNetcdf, self.john, metadata)
        res_metadata = self.resNetcdf.metadata

        # update title for setting flag
        self.assertFalse(res_metadata.is_dirty)
        element = res_metadata.title
        res_metadata.update_element('title', element.id, value='new title')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update temporal coverage for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.create_element('coverage',
                                              type='period',
                                              value={'start': '01/01/2000',
                                                     'end': '12/12/2010'})
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('coverage', element.id, type='period',
                                    value={'start': '01/02/2000', 'end': '01/03/2000'})
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update spatial coverage for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.create_element('coverage',
                                              type='box',
                                              value={'northlimit': 12,
                                                     'eastlimit': 12,
                                                     'southlimit': 1,
                                                     'westlimit': 1,
                                                     'units': 'Decimal degree',
                                                     'projection': 'WGS84'}
                                              )
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('coverage', element.id, type='box',
                                    value={'northlimit': '13',
                                           'eastlimit': '13',
                                           'southlimit': '2',
                                           'westlimit': '2',
                                           'units': 'Decimal degree',
                                           'projection': 'WGS84'}
                                    )
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update description for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.create_element('description', abstract='new abstract')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('description', element.id, abstract='update abstract')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create subject for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.create_element('subject', value='new keyword2')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update/delete source for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.create_element('source',
                                              derived_from='new source')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('source', element.id, abstract='update source')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.delete_element('source', element.id)
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update/delete relation for setting flag
        res_metadata.is_dirty = False
        res_metadata.save()

        element_1 = res_metadata.create_element('relation',
                                                type='isHostedBy',
                                                value='new host')
        res_metadata.refresh_from_db()
        self.assertFalse(res_metadata.is_dirty)
        element_2 = res_metadata.create_element('relation',
                                                type='cites',
                                                value='new reference')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('relation', element_1.id, type='isHostedBy',
                                    value='update host')
        res_metadata.refresh_from_db()
        self.assertFalse(res_metadata.is_dirty)

        res_metadata.update_element('relation', element_2.id, type='cites',
                                    value='update reference')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.delete_element('relation', element_2.id)
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # update creator
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.creators.all().first()
        res_metadata.update_element('creator', element.id, name='update name')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # create/update/delete contributor
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.create_element('contributor',
                                              name='new name')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.update_element('contributor', element.id, name='update name')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        res_metadata.is_dirty = False
        res_metadata.save()

        res_metadata.delete_element('contributor', element.id)
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # update variable
        res_metadata.is_dirty = False
        res_metadata.save()

        element = res_metadata.variables.all().first()
        res_metadata.update_element('variable',
                                    element.id,
                                    name=element.name,
                                    unit='update unit',
                                    type=element.type,
                                    shape=element.shape,
                                    missing_value='1',
                                    descriptive_name='update long name',
                                    method='update method')
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

        # check file content update request
        url = reverse("update_netcdf_resfile", kwargs={'resource_id': self.resNetcdf.short_id})
        request = self.factory.post(url)
        request.user = self.john
        self._set_request_message_attributes(request)
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_netcdf_file(request, resource_id=self.resNetcdf.short_id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # check file update content
        nc_dump_res_file = None
        for f in self.resNetcdf.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        self.assertNotEqual(nc_dump_res_file, None)
        self.assertIn('title = "new title"',
                      nc_dump_res_file.resource_file.read())
        res_metadata.refresh_from_db()
        self.assertFalse(res_metadata.is_dirty)

        # test extra metadata update for setting flag
        self.assertEqual(self.resNetcdf.extra_metadata, {})

        url_params = {'shortkey': self.resNetcdf.short_id}
        post_data = {'key1': 'key-1', 'value1': 'value-1'}
        url = reverse('update_key_value_metadata', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.john

        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self._set_request_message_attributes(request)
        response = update_key_value_metadata(request, shortkey=self.resNetcdf.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_metadata.refresh_from_db()
        self.assertTrue(res_metadata.is_dirty)

    def test_update_netcdf_file_exception(self):
        # trying to update netcdf file for non netcdf resource should raise exception
        url = reverse("update_netcdf_resfile", kwargs={'resource_id': self.genResource.short_id})
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self._set_request_message_attributes(request)
        request.user = self.john
        with self.assertRaises(ValidationError):
            update_netcdf_file(request, resource_id=self.genResource.short_id)

    def _set_request_message_attributes(self, request):
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
