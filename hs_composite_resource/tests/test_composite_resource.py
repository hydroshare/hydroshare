# coding=utf-8
import os
import tempfile
import shutil

from django.core.files.uploadedfile import UploadedFile
from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import resource_file_add_process, resource_post_create_actions

from hs_file_types.models import GenericLogicalFile, GeoRasterLogicalFile


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
        self._create_composite_resource()

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

        # there should not be any GenericLogicalFile object at this point
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

        self.assertEqual(self.composite_resource.files.all().count(), 2)
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

        tif_res_file = [f for f in self.composite_resource.files.all()
                        if f.extension == ".tif"][0]

        GeoRasterLogicalFile.set_file_type(self.composite_resource, tif_res_file.id, self.user)
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
        try:
            self.composite_resource.get_metadata_xml()
        except Exception as ex:
            self.fail("Failed to generate metadata in xml format. Error:{}".format(ex.message))

    def test_resource_coverage_auto_update(self):
        # this is to test that the spatial coverage and temporal coverage
        # for composite resource get updated by the system based on the
        # coverage metadata that all logical file objects of the resource have at anytime

        # 1. test that resource coverages get updated on LFO level metadata creation
        # 2. test that resource coverages get updated on LFO level metadata update
        # 3. test that resource coverages get updated on content file delete

        # create a composite resource with no content file
        self._create_composite_resource()
        # at this point the there should not be any resource level coverage metadata
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # now add the raster tif file to the resource - which should put this file as
        # part of a GenericLogicalFile object
        self.raster_file_obj = open(self.raster_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)

        res_file = self.composite_resource.files.all().first()
        GeoRasterLogicalFile.set_file_type(self.composite_resource, res_file.id, self.user)
        # raster logical file should have a coverage element of type box
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GeoRasterLogicalFile"][0]

        raster_logical_file = res_file.logical_file
        self.assertEqual(raster_logical_file.metadata.coverages.count(), 1)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='box').count(), 1)
        # now the resource should have a coverage metadata element of type box
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 1)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='box').count(), 1)

        # the spatial coverage at the file type level should be exactly the same as the
        # resource level - due to auto update feature in composite resource
        res_coverage = self.composite_resource.metadata.coverages.all().filter(type='box').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], raster_lfo_coverage.value['projection'])
        self.assertEqual(res_coverage.value['units'], raster_lfo_coverage.value['units'])
        self.assertEqual(res_coverage.value['northlimit'], raster_lfo_coverage.value['northlimit'])
        self.assertEqual(res_coverage.value['southlimit'], raster_lfo_coverage.value['southlimit'])
        self.assertEqual(res_coverage.value['eastlimit'], raster_lfo_coverage.value['eastlimit'])
        self.assertEqual(res_coverage.value['westlimit'], raster_lfo_coverage.value['westlimit'])

        # At this point there is not temporal coverage either at the file type level or resource
        # level
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='period').count(), 0)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='period').count(), 0)

        # addding temporal coverage to the logical file should add the temporal coverage to the
        # resource
        value_dict = {'start': '1/1/2010', 'end': '12/12/2015'}
        raster_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertEqual(self.composite_resource.metadata.coverages.all().filter(
            type='period').count(), 1)
        self.assertEqual(raster_logical_file.metadata.coverages.all().filter(
            type='period').count(), 1)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])
        self.assertEqual(res_coverage.value['start'], '1/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/12/2015')

        # test updating the temporal coverage for file type should update the temporal coverage
        # for the resource
        value_dict = {'start': '12/1/2010', 'end': '12/1/2015'}
        raster_logical_file.metadata.update_element('coverage', raster_lfo_coverage.id,
                                                    type='period', value=value_dict)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])
        self.assertEqual(res_coverage.value['start'], '12/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/1/2015')

        # test that the resource coverage is superset of file type coverages
        self.generic_file_obj = open(self.generic_file, 'r')
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.generic_file_obj,), user=self.user)

        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GenericLogicalFile"][0]

        generic_logical_file = res_file.logical_file
        # there should not be any coverage for the generic LFO at this point
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 0)
        # create temporal coverage for generic LFO
        value_dict = {'start': '1/1/2009', 'end': '1/1/2015'}
        generic_logical_file.metadata.create_element('coverage', type='period', value=value_dict)
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 1)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        # resource temporal coverage is now super set of the 2 temporal coverages
        # in 2 LFOs
        self.assertEqual(res_coverage.value['start'], '1/1/2009')
        self.assertEqual(res_coverage.value['end'], '12/1/2015')
        # test resource superset spatial coverage
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 42.0500269597691)
        self.assertEqual(res_coverage.value['eastlimit'], -111.57773718106195)
        self.assertEqual(res_coverage.value['southlimit'], 41.98722286029891)
        self.assertEqual(res_coverage.value['westlimit'], -111.69756293084055)
        value_dict = {'east': '-110.88845678', 'north': '43.6789', 'units': 'Decimal deg'}
        generic_logical_file.metadata.create_element('coverage', type='point', value=value_dict)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 43.6789)
        self.assertEqual(res_coverage.value['eastlimit'], -110.88845678)
        self.assertEqual(res_coverage.value['southlimit'], 41.98722286029891)
        self.assertEqual(res_coverage.value['westlimit'], -111.69756293084055)
        # update the LFO coverage to box type
        value_dict = {'eastlimit': '-110.88845678', 'northlimit': '43.6789',
                      'westlimit': '-112.78967', 'southlimit': '40.12345',
                      'units': 'Decimal deg'}
        lfo_spatial_coverage = generic_logical_file.metadata.spatial_coverage
        generic_logical_file.metadata.update_element('coverage', lfo_spatial_coverage.id,
                                                     type='box', value=value_dict)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(res_coverage.value['units'], 'Decimal degrees')
        self.assertEqual(res_coverage.value['northlimit'], 43.6789)
        self.assertEqual(res_coverage.value['eastlimit'], -110.88845678)
        self.assertEqual(res_coverage.value['southlimit'], 40.12345)
        self.assertEqual(res_coverage.value['westlimit'], -112.78967)

        # deleting the generic file should reset the coverage of the resource to that of the
        # raster LFO
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GenericLogicalFile"][0]
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='box').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='box').first()
        self.assertEqual(res_coverage.value['projection'], raster_lfo_coverage.value['projection'])
        self.assertEqual(res_coverage.value['units'], raster_lfo_coverage.value['units'])
        self.assertEqual(res_coverage.value['northlimit'], raster_lfo_coverage.value['northlimit'])
        self.assertEqual(res_coverage.value['southlimit'], raster_lfo_coverage.value['southlimit'])
        self.assertEqual(res_coverage.value['eastlimit'], raster_lfo_coverage.value['eastlimit'])
        self.assertEqual(res_coverage.value['westlimit'], raster_lfo_coverage.value['westlimit'])
        res_coverage = self.composite_resource.metadata.coverages.all().filter(
            type='period').first()
        raster_lfo_coverage = raster_logical_file.metadata.coverages.all().filter(
            type='period').first()
        self.assertEqual(res_coverage.value['start'], raster_lfo_coverage.value['start'])
        self.assertEqual(res_coverage.value['end'], raster_lfo_coverage.value['end'])
        self.assertEqual(res_coverage.value['start'], '12/1/2010')
        self.assertEqual(res_coverage.value['end'], '12/1/2015')

        # deleting the remaining content file from resource should leave the resource
        # with no coverage element
        res_file = [f for f in self.composite_resource.files.all()
                    if f.logical_file_type_name == "GeoRasterLogicalFile"][0]
        hydroshare.delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        self.assertEqual(self.composite_resource.files.count(), 0)
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)

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

    def test_supports_folder_creation(self):
        """Here we are testing the function supports_folder_creation()
        """
        self._create_composite_resource()
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self._add_generic_file_to_resource()

        self.assertEqual(self.composite_resource.files.count(), 1)
        # we should be able to create this new folder
        new_folder_path = "my-new-folder"
        new_folder_full_path = os.path.join(self.composite_resource.file_path, new_folder_path)
        self.assertEqual(self.composite_resource.supports_folder_creation(new_folder_full_path),
                         True)
        # create the folder
        self.composite_resource.create_folder(new_folder_path)
        old_file_path = self.composite_resource.files.get().short_path
        # now move the file to this new folder
        self.composite_resource.move_or_rename_file_or_folder(self.user,
                                                              old_file_path,
                                                              os.path.join(new_folder_path,
                                                                           self.generic_file_name))
        # test that we should be able to create a folder inside the folder that contains
        # a resource file that is part of a Generic Logical file
        new_folder_full_path = os.path.join(new_folder_full_path, "another-folder")
        self.assertTrue(self.composite_resource.supports_folder_creation(new_folder_full_path))

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self._add_raster_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, tif_res_file.id, self.user)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        self.assertTrue(tif_res_file.resource_file.name.endswith(
            "/data/contents/small_logan/small_logan.tif"))
        # test that creating a folder at "/data/contents/small_logan/" is not supported
        # as that folder contains a resource file that's part of GeoRaster logical file
        new_folder_path = "{}/data/contents/small_logan/my-new-folder"
        new_folder_path = new_folder_path.format(self.composite_resource.short_id)
        self.assertEqual(self.composite_resource.supports_folder_creation(new_folder_path), False)

    def test_supports_move_or_rename_file_or_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class"""

        self._create_composite_resource()
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self._add_generic_file_to_resource()

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        gen_res_file_basename = hydroshare.utils.get_resource_file_name_and_extension(
            gen_res_file)[1]
        self.assertEqual(self.generic_file_name, gen_res_file_basename)
        src_full_path = os.path.join(self.composite_resource.file_path, self.generic_file_name)
        tgt_full_path = os.path.join(self.composite_resource.file_path, 'renamed_file.txt')
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

        # create a new folder so that we can test if the generic file can be moved there or not
        # this code is confusing because three different conventions are involved:
        # 1. Relative path
        # 2. Partially qualified path data/contents/folder
        # 3. Fully qualified path starting at root_path and containing file_path
        new_folder_path = "my-new-folder"
        new_folder_full_path = os.path.join(self.composite_resource.file_path, new_folder_path)
        self.assertTrue(self.composite_resource.supports_folder_creation(new_folder_full_path))

        # create the folder
        self.composite_resource.create_folder(new_folder_path)
        # now move the file to this new folder
        tgt_full_path = os.path.join(new_folder_full_path, self.generic_file_name)
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

        # test that if a folder contains a resource file that's part of a GenericLogicalFile
        # that folder can be renamed
        # now move the file to this new folder
        self.composite_resource.move_or_rename_file_or_folder(self.user,
                                                              self.generic_file_name,
                                                              os.path.join(new_folder_path,
                                                                           self.generic_file_name))

        # test rename folder
        src_full_path = self.composite_resource.short_id + '/data/contents/my-new-folder/'
        tgt_full_path = self.composite_resource.short_id + '/data/contents/my-new-folder-1/'
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self._add_raster_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, tif_res_file.id, self.user)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        self.assertTrue(tif_res_file.resource_file.name.endswith(
            "/data/contents/small_logan/small_logan.tif"))

        # test renaming of any files that are part of GeoRasterLogicalFile is not allowed
        src_full_path = self.composite_resource.short_id + '/data/contents/small_logan/' + \
            self.raster_file_name
        tgt_full_path = self.composite_resource.short_id + \
            '/data/contents/small_logan/small_logan_1.tif'
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), False)

        # test rename folder that contains resource files that are part of the GeoRasterLogicalFile
        # is allowed
        src_full_path = self.composite_resource.short_id + '/data/contents/small_logan'
        tgt_full_path = self.composite_resource.short_id + '/data/contents/small_logan_1'
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), True)

        # test that we can't  move a file to a folder that contains resource files that are part
        # of GeoRasterLogicalFile object
        src_full_path = self.composite_resource.short_id + '/data/contents/my-new-folder/' + \
            self.generic_file_name
        tgt_full_path = self.composite_resource.short_id + '/data/contents/small_logan/' + \
            self.generic_file_name
        # this is the function we are testing
        self.assertEqual(self.composite_resource.supports_rename_path(
            src_full_path, tgt_full_path), False)

    def test_supports_zip(self):
        """Here we are testing the function supports_zip()"""
        self._create_composite_resource()

        # test that a folder containing a resource file that's part of the GenericLogicalFile
        # can be zipped
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self._add_generic_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder_path = "my-new-folder"
        # create the folder
        self.composite_resource.create_folder(new_folder_path)
        # now move the file to this new folder
        self.composite_resource.move_or_rename_file_or_folder(self.user,
                                                              self.generic_file_name,
                                                              os.path.join(new_folder_path,
                                                                           self.generic_file_name))
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder_path)
        # test that we can zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

        # test that a folder containing resource files that are part of the GeorasterLogicalFile
        # can be zipped
        self._add_raster_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, tif_res_file.id, self.user)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        # resource file exists in a new folder 'small_logan'
        self.assertTrue(tif_res_file.resource_file.name.endswith(
            "/data/contents/small_logan/small_logan.tif"))
        folder_to_zip = self.composite_resource.short_id + '/data/contents/small_logan'
        # test that we can zip the folder small_logan
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_delete_original_folder_on_zip(self):
        """Here we are testing the function supports_delete_original_folder_on_zip() of the
        composite resource class"""

        self._create_composite_resource()

        # test that a folder containing a resource file that's part of the GenericLogicalFile
        # can be deleted after that folder gets zipped
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self._add_generic_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder_path = "my-new-folder"
        # create the folder
        self.composite_resource.create_folder(new_folder_path)
        # now move the file to this new folder
        self.composite_resource.move_or_rename_file_or_folder(self.user,
                                                              self.generic_file_name,
                                                              os.path.join(new_folder_path,
                                                                           self.generic_file_name))
        folder_to_zip = self.composite_resource.short_id + '/data/contents/my-new-folder'
        # test that we can zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)
        # this is the function we are testing - my-new-folder can be deleted
        self.assertEqual(self.composite_resource.supports_delete_folder_on_zip(
            folder_to_zip), True)

        # test that a folder containing a resource file that's part of the GeoRasterLogicalFile
        # can't be deleted after that folder gets zipped

        # add a file to the resource which will be part of  a GeoRasterLogicalFile object
        self._add_raster_file_to_resource()
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        GeoRasterLogicalFile.set_file_type(self.composite_resource, tif_res_file.id, self.user)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, '.tif')[0]
        # resource file exists in a new folder 'small_logan'
        self.assertTrue(tif_res_file.resource_file.name.endswith(
            "/data/contents/small_logan/small_logan.tif"))
        folder_to_zip = self.composite_resource.short_id + '/data/contents/small_logan'
        # test that we can zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)
        # this is the function we are testing - small_logan folder can't be deleted
        self.assertEqual(self.composite_resource.supports_delete_folder_on_zip(
            folder_to_zip), False)

    def _create_composite_resource(self):
        self.composite_resource = hydroshare.create_resource(
             resource_type='CompositeResource',
             owner=self.user,
             title='Test Composite Resource'
         )

    def _add_generic_file_to_resource(self):
        self.generic_file_obj = UploadedFile(file=open(self.generic_file, 'rb'),
                                             name=os.path.basename(self.generic_file))
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.generic_file_obj,), user=self.user)

    def _add_raster_file_to_resource(self):
        self.raster_file_obj = UploadedFile(file=open(self.raster_file, 'rb'),
                                            name=os.path.basename(self.raster_file))
        resource_file_add_process(resource=self.composite_resource,
                                  files=(self.raster_file_obj,), user=self.user)
