# coding=utf-8
import os
import tempfile
import shutil

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.signals import post_add_files_to_resource
from hs_core.hydroshare.utils import resource_file_add_process, resource_post_create_actions

from hs_file_types.models import GenericLogicalFile
from hs_file_types.utils import set_file_to_geo_raster_file_type

class CompositeResourceTest(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.temp_dir = tempfile.mkdtemp()
        self.raster_file_name = 'small_logan.tif'
        self.raster_file = 'hs_composite_resource/tests/data/{}'.format(self.raster_file_name)
        self.generic_file_name = 'generic_file.txt'
        self.generic_file = 'hs_composite_resource/tests/data/{}'.format(self.generic_file_name)

        target_temp_raster_file = os.path.join(self.temp_dir, self.raster_file_name)
        shutil.copy(self.raster_file, target_temp_raster_file)
        self.raster_file_obj = open(target_temp_raster_file, 'r')

        target_temp_generic_file = os.path.join(self.temp_dir, self.generic_file_name)
        shutil.copy(self.generic_file, target_temp_generic_file)
        self.generic_file_obj = open(target_temp_generic_file, 'r')

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_composite_resource(self):
        # test that we can create a composite resource

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata'
        )

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

    def test_create_composite_resource_with_file_upload(self):
        # test that when we create composite resource with an uploaded file, then the uploaded file
        # is automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)
        self.raster_file_obj = open(self.raster_file, 'r')

        self.composite_resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Raster File Metadata',
            files=(self.raster_file_obj,)
        )

        # there should not be aby GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # set the logical file
        resource_post_create_actions(resource=self.composite_resource, user=self.user,
                                     metadata=self.composite_resource.metadata)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_file_add_to_composite_resource(self):
        # test that when we add file to an existing composite resource, the added file
        # automatically set to genericlogicalfile type
        self.assertEqual(BaseResource.objects.count(), 0)
        self.raster_file_obj = open(self.raster_file, 'r')

        self._create_composite_resource()

        # there should not be aby GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # add a file to the resource
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is associated with GenericLogicalFile
        self.assertEqual(res_file.has_logical_file, True)
        self.assertEqual(res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_core_metadata_CRUD(self):
        """test that all core metadata elements work for this resource type"""
        self._create_composite_resource()
        # test current metadata status of the composite resource

        # there should be title element
        self.assertEqual(self.composite_resource.metadata.title.value, "Test Composite Resource")
        # there shouldn't be abstract element
        self.assertEqual(self.composite_resource.metadata.description, None)
        # there shouldn't be any format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 0)
        # there should be date element - 2 elements
        self.assertEqual(self.composite_resource.metadata.dates.count(), 2)
        # there should be 1 creator element
        self.assertEqual(self.composite_resource.metadata.creators.count(), 1)
        # there should not be any contributor element
        self.assertEqual(self.composite_resource.metadata.contributors.count(), 0)
        # there should not be any coverage element
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # there should not be any funding agency element
        self.assertEqual(self.composite_resource.metadata.funding_agencies.count(), 0)
        # there should be 1 identifier element
        self.assertEqual(self.composite_resource.metadata.identifiers.count(), 1)
        # there should be 1 language element
        self.assertNotEqual(self.composite_resource.metadata.language, None)
        # there should not be any publisher element
        self.assertEqual(self.composite_resource.metadata.publisher, None)
        # there should not be any format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 0)
        # there should not be any relation element
        self.assertEqual(self.composite_resource.metadata.relations.count(), 0)
        # there should be 1 rights element
        self.assertNotEqual(self.composite_resource.metadata.rights, None)
        # there shouldn't be any source element
        self.assertEqual(self.composite_resource.metadata.sources.count(), 0)
        # there should not be any subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 0)
        # there should be 1 type element
        self.assertNotEqual(self.composite_resource.metadata.type, None)
        # there should not be any key/value metadata
        self.assertEqual(self.composite_resource.extra_metadata, {})

        # test create metadata

        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element('description', abstract='new abstract for the resource')
        # there should be abstract element
        self.assertNotEqual(self.composite_resource.metadata.description, None)
        # add a file to the resource to auto create format element
        self.raster_file_obj = open(self.raster_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # now there should be 1 format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 1)
        # add another creator
        metadata.create_element('creator', name='John Smith')
        # there should be 2 creators now
        self.assertEqual(self.composite_resource.metadata.creators.count(), 2)
        # add a contributor
        metadata.create_element('contributor', name='Lisa Smith')
        # there should be 1 contributor now
        self.assertEqual(self.composite_resource.metadata.contributors.count(), 1)
        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        metadata.create_element('coverage', type='period', value=value_dict)
        # add a point type coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'decimal deg'}
        metadata.create_element('coverage', type='point', value=value_dict)
        # there should be 2 coverage elements now
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        self.assertNotEqual(cov_pt, None)
        cov_period = self.composite_resource.metadata.coverages.all().filter(type='period').first()
        self.assertNotEqual(cov_period, None)

        # add a funding agency element with only the required name value type
        metadata.create_element('fundingagency', agency_name='NSF')
        # there should be 1 funding agency element now
        self.assertEqual(self.composite_resource.metadata.funding_agencies.count(), 1)
        # add another identifier
        metadata.create_element('identifier', name='someIdentifier', url="http://some.org/001")
        # there should be 2 identifier elements
        self.assertEqual(self.composite_resource.metadata.identifiers.count(), 2)
        # add publisher element
        publisher_CUAHSI = "Consortium of Universities for the Advancement of " \
                           "Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'
        # publisher element can be added when the resource is published
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        # user can't set CUASHI as the publisher - when the resource has no content file
        # first delete the content file
        res_file = self.composite_resource.files.first()
        hydroshare.delete_resource_file(self.composite_resource.short_id,
                                        res_file.id,
                                        self.user)
        with self.assertRaises(Exception):
            metadata.create_element('publisher', name=publisher_CUAHSI, url=url_CUAHSI)

        metadata.create_element('publisher', name='USGS', url="http://usgs.gov")
        # there should a publisher element now
        self.assertNotEqual(self.composite_resource.metadata.publisher, None)
        # add a relation element of uri type
        metadata.create_element('relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')
        # there should be 1 relation element
        self.assertEqual(self.composite_resource.metadata.relations.count(), 1)
        # add a source element of uri type
        metadata.create_element('source', derived_from='http://hydroshare.org/resource/0001')
        # there should be 1 source element
        self.assertEqual(self.composite_resource.metadata.sources.count(), 1)
        # add 2 subject elements
        metadata.create_element('subject', value='sub-1')
        metadata.create_element('subject', value='sub-2')
        # there should be 2 subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 2)
        # add key/value metadata
        self.composite_resource.extra_metadata = {'key-1': 'value-1', 'key-2': 'value-2'}
        self.composite_resource.save()
        self.assertEqual(self.composite_resource.extra_metadata,
                         {'key-1': 'value-1', 'key-2': 'value-2'})

        # test update metadata

        # test update title
        metadata.update_element('title', self.composite_resource.metadata.title.id,
                                value="New Title")
        self.assertEqual(self.composite_resource.metadata.title.value, 'New Title')
        # test update abstract
        metadata.update_element('description',
                                self.composite_resource.metadata.description.id,
                                abstract='Updated composite resource')
        self.assertEqual(self.composite_resource.metadata.description.abstract,
                         'Updated composite resource')
        # test updating funding agency
        agency_element = self.composite_resource.metadata.funding_agencies.all().filter(
            agency_name='NSF').first()
        metadata.update_element('fundingagency', agency_element.id,
                                award_title="Cyber Infrastructure",
                                award_number="NSF-101-20-6789",
                                agency_url="http://www.nsf.gov")
        agency_element = self.composite_resource.metadata.funding_agencies.all().filter(
            agency_name='NSF').first()
        self.assertEquals(agency_element.agency_name, 'NSF')
        self.assertEquals(agency_element.award_title, 'Cyber Infrastructure')
        self.assertEquals(agency_element.award_number, 'NSF-101-20-6789')
        self.assertEquals(agency_element.agency_url, 'http://www.nsf.gov')
        some_idf = self.composite_resource.metadata.identifiers.all().filter(
            name='someIdentifier').first()
        metadata.update_element('identifier', some_idf.id,  name='someOtherIdentifier')
        some_idf = self.composite_resource.metadata.identifiers.all().filter(
            name='someOtherIdentifier').first()
        self.assertNotEqual(some_idf, None)
        # update language
        self.assertEqual(self.composite_resource.metadata.language.code, 'eng')
        metadata.update_element('language',
                                self.composite_resource.metadata.language.id, code='fre')
        self.assertEqual(self.composite_resource.metadata.language.code, 'fre')
        # test that updating publisher element raises exception
        with self.assertRaises(Exception):
            metadata.update_element('publisher',
                                    self.composite_resource.metadata.publisher.id,
                                    name='USU', url="http://usu.edu")
        # test update relation type
        rel_to_update = self.composite_resource.metadata.relations.all().filter(
            type='isPartOf').first()
        metadata.update_element('relation', rel_to_update.id,
                                type='isVersionOf', value="dummy value 2")
        rel_to_update = self.composite_resource.metadata.relations.all().filter(
            type='isVersionOf').first()
        self.assertEqual(rel_to_update.value, "dummy value 2")
        src_1 = self.composite_resource.metadata.sources.all().filter(
            derived_from='http://hydroshare.org/resource/0001').first()
        metadata.update_element('source', src_1.id,
                                derived_from='http://hydroshare.org/resource/0002')
        src_1 = self.composite_resource.metadata.sources.first()
        self.assertEqual(src_1.derived_from, 'http://hydroshare.org/resource/0002')
        # change the point coverage to type box
        # since we deleted the content file, there should not be any coverage element
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # add a point type coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'decimal deg'}
        metadata.create_element('coverage', type='point', value=value_dict)
        value_dict = {'northlimit': '56.45678', 'eastlimit': '120.6789', 'southlimit': '16.45678',
                      'westlimit': '16.6789',
                      'units': 'decimal deg'}
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        metadata.update_element('coverage', cov_pt.id, type='box',  value=value_dict)
        cov_pt = self.composite_resource.metadata.coverages.all().filter(type='point').first()
        self.assertEqual(cov_pt, None)
        cov_box = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        self.assertNotEqual(cov_box, None)

        # update creator
        creator = self.composite_resource.metadata.creators.all().filter(name='John Smith').first()
        self.assertEqual(creator.email, None)
        metadata.update_element('creator', creator.id, email='JSmith@gmail.com')
        creator = self.composite_resource.metadata.creators.all().filter(name='John Smith').first()
        self.assertEqual(creator.email, 'JSmith@gmail.com')
        # update contributor
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, None)
        metadata.update_element('contributor', contributor.id, email='LSmith@gmail.com')
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, 'LSmith@gmail.com')

    def test_metadata_xml(self):
        """test that the call to resource.get_metadata_xml() doesn't raise exception
        for composite resource type get_metadata_xml() includes both resource
        level metadata and file type metadata for each logical file objects within the resource
        """

        # 1. create core metadata elements
        # 2. create genericlogicalfile type metadata
        # 3. create georasterlogicalfile type metadata

        self._create_composite_resource()
        # add a file to the resource to auto create format element
        # as well as be able to add generic file type metadata
        self.generic_file_obj = open(self.generic_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.generic_file_obj,), user=self.user)

        # add a raster file to the resource to auto create format element
        # as well as be able to add raster file type metadata
        self.raster_file_obj = open(self.raster_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)
        # add some core metadata
        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element('description', abstract='new abstract for the resource')
        # add a contributor
        metadata.create_element('contributor', name='Lisa Smith')
        # add a funding agency element with only the required name value type
        metadata.create_element('fundingagency', agency_name='NSF')
        # add a relation element of uri type
        metadata.create_element('relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')
        # add a source element of uri type
        metadata.create_element('source', derived_from='http://hydroshare.org/resource/0001')
        # add 2 subject elements
        metadata.create_element('subject', value='sub-1')
        metadata.create_element('subject', value='sub-2')
        # add key/value metadata
        self.composite_resource.extra_metadata = {'key-1': 'value-1', 'key-2': 'value-2'}
        self.composite_resource.save()
        # add a publisher element
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        publisher_CUAHSI = "Consortium of Universities for the Advancement of " \
                           "Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'
        metadata.create_element('publisher', name=publisher_CUAHSI, url=url_CUAHSI)

        # add generic logical file type metadata
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GenericLogicalFile"][0]

        gen_logical_file = res_file.logical_file
        # add dataset name
        self.assertEqual(gen_logical_file.dataset_name, None)
        gen_logical_file.dataset_name = "This is a generic dataset"
        gen_logical_file.save()
        # add key/value metadata
        gen_logical_file.metadata.extra_metadata = {'key1': 'value 1', 'key2': 'value 2'}
        gen_logical_file.metadata.save()
        # add temporal coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        gen_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        # add spatial coverage
        value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'decimal deg'}
        gen_logical_file.metadata.create_element('coverage', type='point', value=value_dict)

        set_file_to_geo_raster_file_type(self.composite_resource, res_file.id, self.user)
        # add generic logical file type metadata
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GeoRasterLogicalFile"][0]

        raster_logical_file = res_file.logical_file
        # check we have dataset name
        self.assertEqual(raster_logical_file.dataset_name, "small_logan")
        # add key/value metadata
        raster_logical_file.metadata.extra_metadata = {'keyA': 'value A', 'keyB': 'value B'}
        raster_logical_file.metadata.save()
        # add temporal coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2010', 'end': '12/12/2016'}
        raster_logical_file.metadata.create_element('coverage', type='period', value=value_dict)

        # test no exception raised when generating the metadata xml for this resource type
        self.composite_resource.get_metadata_xml()

    def test_resource_coverage_auto_update(self):
        # this is to test that the spatial coverage and temporal coverage
        # for composite resource get updated by the system based on the
        # coverage metadata that all logical file objects of the resource have at anytime
        # TODO: implement this test
        # 1. test that resource coverages get updated on LFO level metadata creation
        # 2. test that resource coverages get updated on LFO level metadata update
        # 3. test that resource coverages get updated on content file delete
        pass

    def test_can_be_public_or_discoverable(self):
        self._create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a text file
        self.generic_file_obj = open(self.generic_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.generic_file_obj,), user=self.user)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a raster file to the resource to auto create format element
        self.raster_file_obj = open(self.raster_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = self.composite_resource.metadata.get_required_missing_elements()
        self.assertEqual(len(missing_elements), 2)
        self.assertIn('Abstract', missing_elements)
        self.assertIn('Keywords', missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element('description', abstract='new abstract for the resource')
        # add keywords (element name is subject)
        metadata.create_element('subject', value='sub-1')
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
             resource_type='CompositeResource',
             owner=self.user,
             title='Test Composite Resource'
         )
