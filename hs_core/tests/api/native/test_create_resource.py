__author__ = 'tonycastronova'

import os
import tempfile
import zipfile
import shutil
import time

from unittest import TestCase
import datetime as dt

from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group

from hs_core.hydroshare import resource, get_resource_by_shortkey
from hs_core.hydroshare import users
from hs_core.models import GenericResource


class MyTemporaryUploadedFile(UploadedFile):
    def __init__(self, file=None, name=None, content_type=None, size=None, charset=None, content_type_extra=None):
        super(UploadedFile, self).__init__(file, name)
        self.orig_name = name
        self.size = size
        self.content_type = content_type
        self.charset = charset
        self.content_type_extra = content_type_extra

    def temporary_file_path(self):
        return self.orig_name


class TestCreateResource(TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # Make a text file
        self.txt_file_path = os.path.join(self.tmp_dir, 'text.txt')
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_path = 'hs_core/tests/data/cea.tif'

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()
        GenericResource.objects.all().delete()

    def test_create_resource(self):
        new_res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

        pid = new_res.short_id

        # get the resource by pid
        res = get_resource_by_shortkey(pid)
        self.assertEqual(res.resource_type, 'GenericResource')
        self.assertTrue(isinstance(res, GenericResource), type(res))
        self.assertTrue(res.metadata.title.value == 'My Test Resource')
        self.assertTrue(res.created.strftime('%m/%d/%Y %H:%M') == res.updated.strftime('%m/%d/%Y %H:%M') )
        self.assertTrue(res.created.strftime('%m/%d/%Y') == dt.datetime.today().strftime('%m/%d/%Y'))
        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.short_id is not None, 'Short ID has not been created!')
        self.assertTrue(res.bags.exists(), 'Bagit has not been created!')
        self.assertEqual(res.files.all().count(), 0, 'Resource has content files')

    def test_create_resource_with_metadata(self):
        # TODO: add more metadata elements to the following dict
        metadata_dict = [
            {'description': {'abstract': 'My test abstract'}},
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Lisa Molley', 'email': 'lmolley@gmail.com'}},
            {'contributor': {'name': 'Kelvin Marshal', 'email': 'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'profile_links': [{'type': 'yahooProfile', 'url': 'http://yahoo.com/LH001'}]}},
            {'coverage': {'type': 'period', 'value': {'name': 'Name for period coverage', 'start': '1/1/2000',
                                                      'end': '12/12/2012'}}},
            {'coverage': {'type': 'point', 'value': {'name': 'Name for point coverage', 'east': '56.45678',
                                                     'north': '12.6789', 'units': 'deg'}}},
            {'identifier': {'name':'someIdentifier', 'url':"http://some.org/001"}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource', 'url': 'http://rights.org/001'}},
            {'source': {'derived_from': 'http://hydroshare.org/resource/0001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
        ]

        res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Resource',
            metadata=metadata_dict
        )

        # title element is created as part of resource creation
        self.assertEqual(res.metadata.title.value, 'My Test Resource', msg='resource title did not match')

        # resource description element is created as part of resource creation
        self.assertEqual(res.metadata.description.abstract, 'My test abstract')

        # the following 2 date elements should have been created as part of resource creation
        self.assertEqual(res.metadata.dates.all().count(), 2, msg="Number of date elements not equal to 2.")
        self.assertIn('created', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

        # number of creators at this point should be 3 (2 we are creating here one is automatically
        # generated as part of the resource creation
        self.assertEqual(res.metadata.creators.all().count(), 3, msg='Number of creators not equal to 3')
        self.assertIn('John Smith', [cr.name for cr in res.metadata.creators.all()],
                      msg="Creator 'John Smith' was not found")
        self.assertIn('Lisa Molley', [cr.name for cr in res.metadata.creators.all()],
                      msg="Creator 'Lisa Molley' was not found")

        # number of contributors at this point should be 1
        self.assertEqual(res.metadata.contributors.all().count(), 1, msg='Number of contributors not equal to 1')

        # there should be now 2 coverage elements
        self.assertEqual(res.metadata.coverages.all().count(), 2, msg="Number of coverages not equal to 2.")

        # there should be now 2 format elements
        #self.assertEqual(res.metadata.formats.all().count(), 2, msg="Number of format elements not equal to 2.")

        # there should be now 2 identifier elements ( 1 we are creating here + 1 auto generated at the time of resource creation)
        self.assertEqual(res.metadata.identifiers.all().count(), 2, msg="Number of identifier elements not equal to 1.")

        self.assertEqual(res.metadata.language.code, 'eng', msg="Resource has a language that is not English.")

        self.assertEqual(res.metadata.relations.all().count(), 1,
                         msg="Number of source elements is not equal to 1")

        self.assertEqual(res.metadata.rights.statement, 'This is the rights statement for this resource',
                         msg="Statement of rights did not match.")
        self.assertEqual(res.metadata.rights.url, 'http://rights.org/001', msg="URL of rights did not match.")

        self.assertEqual(res.metadata.sources.all().count(), 1, msg="Number of sources is not equal to 1.")
        self.assertIn('http://hydroshare.org/resource/0001',
                      [src.derived_from for src in res.metadata.sources.all()],
                      msg="Source element with derived from value of %s does not exist."
                          % 'http://hydroshare.org/resource/0001')

        # there should be 2 subject elements for this resource
        self.assertEqual(res.metadata.subjects.all().count(), 2, msg="Number of subject elements found not be 1.")
        self.assertIn('sub-1', [sub.value for sub in res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')
        self.assertIn('sub-2', [sub.value for sub in res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')

    def test_create_resource_with_file(self):
        raster = open(self.raster_file_path)
        res = resource.create_resource('GenericResource',
                                       self.user,
                                       'My Test resource',
                                       files=(raster,))
        pid = res.short_id

        # get the resource by pid
        res = get_resource_by_shortkey(pid)
        self.assertEqual(res.resource_type, 'GenericResource')
        self.assertTrue(isinstance(res, GenericResource), type(res))
        self.assertEqual(res.metadata.title.value, 'My Test resource')
        self.assertEquals(res.files.all().count(), 1)

    def test_create_resource_with_two_files(self):
        raster = MyTemporaryUploadedFile(open(self.raster_file_path, 'rb'), name=self.raster_file_path,
                                         content_type='image/tiff',
                                         size=os.stat(self.raster_file_path).st_size)
        text = MyTemporaryUploadedFile(open(self.txt_file_path, 'r'), name=self.txt_file_path,
                                       content_type='text/plain',
                                       size=os.stat(self.txt_file_path).st_size)
        res = resource.create_resource('GenericResource',
                                       self.user,
                                       'My Test resource',
                                       files=(raster, text))
        pid = res.short_id

        # get the resource by pid
        res = get_resource_by_shortkey(pid)
        self.assertEqual(res.resource_type, 'GenericResource')
        self.assertTrue(isinstance(res, GenericResource), type(res))
        self.assertEqual(res.metadata.title.value, 'My Test resource')
        self.assertEquals(res.files.all().count(), 2)

    def test_create_resource_with_zipfile(self):

        # Make a zip file
        zip_path = os.path.join(self.tmp_dir, 'test.zip')
        with zipfile.ZipFile(zip_path, 'w') as zfile:
            zfile.write(self.raster_file_path)
            zfile.write(self.txt_file_path)

        # Create a resource with zipfile, do not un-pack
        payload = MyTemporaryUploadedFile(open(zip_path, 'rb'), name=zip_path,
                                        content_type='application/zip',
                                        size=os.stat(zip_path).st_size)
        res = resource.create_resource('GenericResource',
                                       self.user,
                                       'My Test resource',
                                       files=(payload,))

        pid = res.short_id

        # get the resource by pid
        res = get_resource_by_shortkey(pid)
        for f in res.files.all():
            print f.resource_file.name
        self.assertEquals(res.files.all().count(), 1)

        # Create a resource with zipfile, un-pack
        payload2 = MyTemporaryUploadedFile(open(zip_path, 'rb'), name=zip_path,
                                        content_type='application/zip',
                                        size=os.stat(zip_path).st_size)
        res = resource.create_resource('GenericResource',
                                       self.user,
                                       'My Test resource',
                                       files=(payload2,),
                                       unpack_file=True)

        pid = res.short_id
        res_tmp = get_resource_by_shortkey(pid)
        self.assertEquals(res_tmp.files.all().count(), 2)



