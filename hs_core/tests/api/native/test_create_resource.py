__author__ = 'tonycastronova'

import os
import tempfile
import zipfile
import shutil
from dateutil import parser
from unittest import TestCase
import datetime as dtime

from django.contrib.auth.models import Group, User
from django.utils import timezone

from hs_core.hydroshare import resource, get_resource_by_shortkey
from hs_core.tests.api.utils import MyTemporaryUploadedFile
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare


class TestCreateResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCreateResource, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        # create files
        file_one = "test1.txt"
        file_two = "test2.tif"

        open(file_one, "w").close()
        open(file_two, "w").close()

        # open files for read and upload
        self.file_one = open(file_one, "r")
        self.file_two = open(file_two, "r")

        # Make a text file
        self.txt_file_path = os.path.join(self.tmp_dir, 'text.txt')
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_path = 'hs_core/tests/data/cea.tif'

    def tearDown(self):
        super(TestCreateResource, self).tearDown()

        shutil.rmtree(self.tmp_dir)

        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()

        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        self.file_one.close()
        os.remove(self.file_one.name)
        self.file_two.close()
        os.remove(self.file_two.name)

    def test_create_resource_without_content_files(self):
        res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

        self.assertEqual(res.resource_type, 'GenericResource')
        self.assertTrue(isinstance(res, GenericResource))
        self.assertTrue(res.metadata.title.value == 'My Test Resource')
        self.assertTrue(res.created.strftime('%m/%d/%Y %H:%M') == res.updated.strftime('%m/%d/%Y %H:%M') )
        self.assertTrue(res.created.strftime('%m/%d/%Y') == dtime.datetime.today().strftime('%m/%d/%Y'))
        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.short_id is not None, 'Short ID has not been created!')
        self.assertEqual(res.files.all().count(), 0, 'Resource has content files')

    def test_create_resource_with_content_files(self):
        new_res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource',
            files=(self.file_one,)
            )

        # test resource has one file
        self.assertEquals(new_res.files.all().count(), 1, msg="Number of content files is not equal to 1")

        self.assertEqual(new_res.resource_type, 'GenericResource')
        self.assertTrue(isinstance(new_res, GenericResource), type(new_res))
        self.assertTrue(new_res.metadata.title.value == 'My Test Resource')
        self.assertTrue(new_res.created.strftime('%m/%d/%Y %H:%M') == new_res.updated.strftime('%m/%d/%Y %H:%M') )
        self.assertTrue(new_res.created.strftime('%m/%d/%Y') == dtime.datetime.today().strftime('%m/%d/%Y'))
        self.assertTrue(new_res.creator == self.user)
        self.assertTrue(new_res.short_id is not None, 'Short ID has not been created!')
        self.assertEqual(new_res.files.all().count(), 1, msg="Number of content files is not equal to 1")

        # test creating resource with multiple files
        new_res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource',
            files=(self.file_one, self.file_two)
            )

        # test resource has 2 files
        self.assertEquals(new_res.files.all().count(), 2, msg="Number of content files is not equal to 2")

    def test_create_resource_with_metadata(self):
        # Note: if element 'type' or 'format' is added to the following dictionary, they will be ignored
        # see: 'test_create_resource_with_metadata_for_type' and 'test_create_resource_with_metadata_for_format'
        # element 'publisher' can't be part of the following dictionary - resource creation will fail otherwise
        # 'publisher' element can be created only after the resource is published
        # see: 'test_create_resource_with_metadata_for_publisher'
        # only date element of type 'valid' is honored. Other date types metadata is ignored
        # see: 'test_create_resource_with_metadata_for_date'
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
            {'identifier': {'name': 'someIdentifier', 'url':"http://some.org/001"}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource',
                        'url': 'http://rights.org/001'}},
            {'source': {'derived_from': 'http://hydroshare.org/resource/0001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
            {'language': {'code': 'fre'}},
            {'date': {'type': 'valid', 'start_date': parser.parse('01/20/2016'),
                      'end_date': parser.parse('02/20/2016')}},
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

        # the following 3 date elements should have been created as part of resource creation
        self.assertEqual(res.metadata.dates.all().count(), 3, msg="Number of date elements not equal to 3.")
        self.assertIn('created', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")
        self.assertIn('valid', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

        # number of creators at this point should be 3 (2 are created based on supplied metadata and one is
        # automatically generated as part of the resource creation
        self.assertEqual(res.metadata.creators.all().count(), 3, msg='Number of creators not equal to 3')
        self.assertIn('John Smith', [cr.name for cr in res.metadata.creators.all()],
                      msg="Creator 'John Smith' was not found")
        self.assertIn('Lisa Molley', [cr.name for cr in res.metadata.creators.all()],
                      msg="Creator 'Lisa Molley' was not found")

        # number of contributors at this point should be 1
        self.assertEqual(res.metadata.contributors.all().count(), 1, msg='Number of contributors not equal to 1')

        # there should be now 2 coverage elements as per the supplied metadata
        self.assertEqual(res.metadata.coverages.all().count(), 2, msg="Number of coverages not equal to 2.")

        # there should be no format elements
        self.assertEqual(res.metadata.formats.all().count(), 0, msg="Number of format elements not equal to 0.")

        # there should be now 2 identifier elements (one was created from the supplied metadat and the
        # other one was auto generated at the time of resource creation)
        self.assertEqual(res.metadata.identifiers.all().count(), 2, msg="Number of identifier elements not equal to 1.")

        # Language element created based on supplied metadata
        self.assertEqual(res.metadata.language.code, 'fre', msg="Resource has a language that is not French.")

        self.assertEqual(res.metadata.relations.all().count(), 1,
                         msg="Number of relation elements is not equal to 1")

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

        # valid date should have been created
        self.assertEquals(res.metadata.dates.filter(type='valid').count(), 1)
        valid_date_element = res.metadata.dates.filter(type='valid').first()
        valid_start_date = timezone.make_aware(dtime.datetime.strptime('01/20/2016', "%m/%d/%Y"),
                                               timezone.get_default_timezone())
        valid_end_date = timezone.make_aware(dtime.datetime.strptime('02/20/2016', "%m/%d/%Y"),
                                             timezone.get_default_timezone())
        self.assertEquals(valid_date_element.start_date, valid_start_date)
        self.assertEquals(valid_date_element.end_date, valid_end_date)

    def test_create_resource_with_metadata_for_publisher(self):
        # trying to create a resource with metadata for publisher should fail due to the fact that the
        # resource is not yet published
        metadata_dict = [{'publisher': {'name': 'HydroShare', 'url': 'https://hydroshare.org'}}, ]
        with self.assertRaises(Exception):
            resource.create_resource(resource_type='GenericResource',
                                     owner=self.user,
                                     title='My Test Resource',
                                     metadata=metadata_dict
                                    )

    def test_create_resource_with_metadata_for_type(self):
        # trying to create a resource with metadata for type element should ignore the provided type element data
        # and create the system generated type element
        metadata_dict = [{'type': {'url': 'https://hydroshare.org/GenericResource'}}, ]
        res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Resource',
            metadata=metadata_dict
        )

        type_url = '{0}/terms/{1}'.format(hydroshare.utils.current_site_url(), 'GenericResource')
        self.assertEqual(res.metadata.type.url, type_url, msg='type element url is wrong')

    def test_create_resource_with_metadata_for_format(self):
        # trying to create a resource with metadata for format element should ignore the provided format element data
        # as format elements are system generated based on resource content files
        metadata_dict = [{'format': {'value': 'plain/text'}}, {'format': {'value': 'image/tiff'}}]
        res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Resource',
            metadata=metadata_dict
        )
        self.assertEqual(res.metadata.formats.all().count(), 0, msg="Number of format elements not equal to 0.")

    def test_create_resource_with_metadata_for_date(self):
        # trying to create a resource with metadata for 'date' element of type 'created' or 'modified' should ignore
        # the provided date metadata as date of type created and modified are system generated based on resource
        # creation time.
        # trying to create a resource with metadata for 'date' element of type 'published' should ignore the provided
        # metadata as date of type published is created when the resource is published
        # trying to create a resource with metadata for 'date' element of type 'available' should ignore the provided
        # metadata as date of type available is created when the resource is made public.
        # the only date element that can be created at the time of resource creation by specifying necessary data is
        # of the type 'valid'
        metadata_dict = [{'date': {'type': 'created', 'start_date': parser.parse('01/16/2016')}},
                         {'date': {'type': 'modified', 'start_date': parser.parse('01/16/2016')}},
                         {'date': {'type': 'published', 'start_date': parser.parse('01/16/2016')}},
                         {'date': {'type': 'available', 'start_date': parser.parse('01/16/2016')}},
                         {'date': {'type': 'valid', 'start_date': parser.parse('01/20/2016'),
                                   'end_date': parser.parse('02/20/2016')}}]
        res = resource.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='My Test Resource',
            metadata=metadata_dict
        )

        self.assertIn('created', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

        # skipped dates are created, modified, published, and available
        skipped_date = timezone.make_aware(dtime.datetime.strptime('01/16/2016', "%m/%d/%Y"),
                                           timezone.get_default_timezone())

        self.assertNotIn(skipped_date, [dat.start_date for dat in res.metadata.dates.all()],
                         msg="Matching date value was found")

        self.assertEquals(res.metadata.dates.filter(type='publisher').count(), 0, msg="Publisher date was found.")
        self.assertEquals(res.metadata.dates.filter(type='available').count(), 0, msg="Available date was found.")

        # valid date should have been created
        self.assertEquals(res.metadata.dates.filter(type='valid').count(), 1)
        valid_start_date = timezone.make_aware(dtime.datetime.strptime('01/20/2016', "%m/%d/%Y"),
                                               timezone.get_default_timezone())
        valid_end_date = timezone.make_aware(dtime.datetime.strptime('02/20/2016', "%m/%d/%Y"),
                                             timezone.get_default_timezone())

        self.assertIn(valid_start_date, [dt.start_date for dt in res.metadata.dates.all()],
                      msg="Matching date value was not found")

        self.assertIn(valid_end_date, [dt.end_date for dt in res.metadata.dates.all()],
                      msg="Matching date value was not found")

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
        res = get_resource_by_shortkey(pid)
        self.assertEquals(res.files.all().count(), 2)

