# coding=utf-8
import datetime
import os
import shutil
from zipfile import ZipFile

from dateutil import tz
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.exceptions import ResourceVersioningException
from hs_core.hydroshare.utils import (add_file_to_resource,
                                      get_file_from_s3,
                                      get_resource_by_shortkey,
                                      resource_file_add_process)
from hs_core.models import BaseResource, ResourceFile
from hs_core.tasks import FileOverrideException
from hs_core.testing import MockS3TestCaseMixin
from hs_core.views.utils import (add_reference_url_to_resource, create_folder,
                                 delete_resource_file,
                                 edit_reference_url_in_resource,
                                 move_or_rename_file_or_folder, remove_folder,
                                 unzip_file, zip_by_aggregation_file)
from hs_file_types.models import (
    FileSetLogicalFile,
    GenericFileMetaData,
    GenericLogicalFile,
    GeoFeatureLogicalFile,
    GeoRasterLogicalFile,
    ModelInstanceLogicalFile,
    ModelProgramLogicalFile,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    CSVLogicalFile,
)
from hs_file_types.enums import AggregationMetaFilePath
from hs_file_types.tests.utils import CompositeResourceTestMixin


class CompositeResourceTest(
    MockS3TestCaseMixin, TransactionTestCase, CompositeResourceTestMixin
):
    def setUp(self):
        super(CompositeResourceTest, self).setUp()
        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "user1@nowhere.com",
            username="user1",
            password='mypassword1',
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[self.group],
        )

        self.res_title = "Testing Composite Resource"
        self.invalid_url = "http://i.am.invalid"
        self.valid_url = "https://www.google.com"
        self.raster_file_name = "small_logan.tif"
        self.raster_file = "hs_composite_resource/tests/data/{}".format(
            self.raster_file_name
        )

        self.generic_file_name = "generic_file.txt"
        self.generic_file = "hs_composite_resource/tests/data/{}".format(
            self.generic_file_name
        )

        self.generic_tar_gz_file_name = "generic_file.txt.tar.gz"
        self.generic_tar_gz_file = "hs_composite_resource/tests/data/{}".format(
            self.generic_tar_gz_file_name
        )

        self.csv_file_name = "csv_with_header_and_data.csv"
        self.csv_file = "hs_composite_resource/tests/data/{}".format(
            self.csv_file_name
        )

        self.netcdf_file_name = "netcdf_valid.nc"
        self.netcdf_file = "hs_composite_resource/tests/data/{}".format(
            self.netcdf_file_name
        )

        self.netcdf_file_name_no_coverage = "nc_no_spatial_ref.nc"
        self.netcdf_file_no_coverage = "hs_composite_resource/tests/data/{}".format(
            self.netcdf_file_name_no_coverage
        )

        self.sqlite_file_name = "ODM2.sqlite"
        self.sqlite_file = "hs_composite_resource/tests/data/{}".format(
            self.sqlite_file_name
        )

        self.watershed_dbf_file_name = "watersheds.dbf"
        self.watershed_dbf_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_dbf_file_name
        )
        self.watershed_shp_file_name = "watersheds.shp"
        self.watershed_shp_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_shp_file_name
        )
        self.watershed_shx_file_name = "watersheds.shx"
        self.watershed_shx_file = "hs_composite_resource/tests/data/{}".format(
            self.watershed_shx_file_name
        )

        self.json_file_name = "multi_sites_formatted_version1.0.refts.json"
        self.json_file = "hs_composite_resource/tests/data/{}".format(
            self.json_file_name
        )

        self.zip_file_name = "test.zip"
        self.zip_file = "hs_composite_resource/tests/data/{}".format(self.zip_file_name)

        self.zipped_aggregation_file_name = "multi_sites_formatted_version1.0.refts.zip"
        self.zipped_aggregation_file = "hs_composite_resource/tests/data/{}".format(
            self.zipped_aggregation_file_name
        )

    def tearDown(self):
        super(CompositeResourceTest, self).tearDown()
        if self.composite_resource:
            self.composite_resource.delete()

    def test_create_composite_resource(self):
        # test that we can create a composite resource

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)
        self.create_composite_resource()

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

    def test_create_composite_resource_with_file_upload(self):
        # test that when we create composite resource with an uploaded file, then the uploaded file
        # is automatically not set to genericlogicalfile type

        self.assertEqual(BaseResource.objects.count(), 0)

        self.create_composite_resource(
            self.raster_file
        )  # There should not be a GenericLogicalFile at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)

        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        self.composite_resource.delete()

        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be no GenericFileMetaData object at this point
        self.assertEqual(GenericFileMetaData.objects.count(), 0)
        # setting resource to None to avoid deleting resource again in tearDown() since we have
        # deleted the resource already
        self.composite_resource = None

    def test_add_and_edit_referenced_url(self):
        # test that referenced url can be added to composite resource as a genericlogical file
        # type single file aggregation, and can also be edited

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        # test invalid url fails to be added to an empty composite resource
        self.create_composite_resource()
        url_file_base_name = "test_url_invalid"
        ret_status, msg, _ = add_reference_url_to_resource(
            self.user,
            self.composite_resource.short_id,
            self.invalid_url,
            url_file_base_name,
            "data/contents",
        )
        self.assertEqual(
            ret_status,
            status.HTTP_400_BAD_REQUEST,
            msg="Invalid referenced URL should not be added to resource if "
            "validate_url_flag is True",
        )

        # test invalid url CAN be added to the resource if validate_url_flag is turned off
        ret_status, msg, _ = add_reference_url_to_resource(
            self.user,
            self.composite_resource.short_id,
            self.invalid_url,
            url_file_base_name,
            "data/contents",
            validate_url_flag=False,
        )
        self.assertEqual(
            ret_status,
            status.HTTP_200_OK,
            msg="Invalid referenced URL should be added to resource if "
            "validate_url_flag is False",
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # there should be one GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        res_file = self.composite_resource.files.first()
        # url singlefile aggregation should have extra_data url field created
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data["url"], self.invalid_url)

        # delete the invalid_url resource file
        hydroshare.delete_resource_file(
            self.composite_resource.short_id, res_file.id, self.user
        )
        self.assertEqual(self.composite_resource.files.count(), 0)
        # there should be no GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # test valid url can be added to an empty composite resource
        url_file_base_name = "test_url_valid"
        ret_status, msg, _ = add_reference_url_to_resource(
            self.user,
            self.composite_resource.short_id,
            self.valid_url,
            url_file_base_name,
            "data/contents",
        )
        self.assertEqual(
            ret_status, status.HTTP_200_OK, msg="Valid URL should be added to resource"
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # there should be one GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        # test valid url can be added to a subfolder of a composite resource
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        ret_status, msg, _ = add_reference_url_to_resource(
            self.user,
            self.composite_resource.short_id,
            self.valid_url,
            url_file_base_name,
            new_folder_path,
        )
        self.assertEqual(ret_status, status.HTTP_200_OK)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be two GenericLogicalFile objects at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 2)
        for res_file in self.composite_resource.files.all():
            # url singlefile aggregation should have extra_data url field created
            url_logical_file = res_file.logical_file
            self.assertEqual(url_logical_file.extra_data["url"], self.valid_url)

        # remove new_folder_path
        remove_folder(self.user, self.composite_resource.short_id, new_folder_path)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # test edit reference url
        new_ref_url = self.invalid_url
        url_filename = url_file_base_name + ".url"
        ret_status, msg = edit_reference_url_in_resource(
            self.user,
            self.composite_resource,
            new_ref_url,
            "data/contents",
            url_filename,
        )
        self.assertEqual(
            ret_status,
            status.HTTP_400_BAD_REQUEST,
            msg="Referenced URL should not "
            "be updated with invalid URL "
            "when validate_url_flag is "
            "True",
        )

        # test resource referenced URL CAN be updated with an invalid url if validate_url_flag is
        # set to False
        ret_status, msg = edit_reference_url_in_resource(
            self.user,
            self.composite_resource,
            new_ref_url,
            "data/contents",
            url_filename,
            validate_url_flag=False,
        )
        self.assertEqual(
            ret_status,
            status.HTTP_200_OK,
            msg="Referenced URL should be updated with invalid URL when "
            "validate_url_flag is False",
        )
        res_file = self.composite_resource.files.all().first()
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data["url"], new_ref_url)

        # test resource referenced URL can be updated with a valid URL
        new_ref_url = "https://www.yahoo.com"
        ret_status, msg = edit_reference_url_in_resource(
            self.user,
            self.composite_resource,
            new_ref_url,
            "data/contents",
            url_filename,
        )
        self.assertEqual(ret_status, status.HTTP_200_OK)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        res_file = self.composite_resource.files.all().first()
        url_logical_file = res_file.logical_file
        self.assertEqual(url_logical_file.extra_data["url"], new_ref_url)

    def test_add_file_to_composite_resource(self):
        # test that when we add file to an existing composite resource, the added file
        # is not automatically set to genericlogicalfile type

        self.create_composite_resource(self.raster_file)

        # there should not be any GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()

        # check that the resource file is not associated with any logical file
        self.assertEqual(res_file.has_logical_file, False)
        # there should be 0 GenericLogicalFile object at this point
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

    def test_resource_file_system_metadata(self):
        """Test when files are added/uploaded to a resource, system level metadata is retrieved from S3 and saved in
        the DB for each file.
        """
        self.create_composite_resource(self.generic_file)

        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        res_file = self.composite_resource.files.first()
        # check file level system metadata
        self.assertGreater(res_file._size, 0)
        self.assertGreater(len(res_file._checksum), 0)
        self.assertNotEqual(res_file._modified_time, None)

    def test_aggregation_folder_delete(self):
        # here we are testing that when a folder is deleted containing
        # files for a logical file type, other files in the composite resource are still associated
        # with their respective logical file types

        self.create_composite_resource()
        new_folder = "raster_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the the raster file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=new_folder
        )

        tif_res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".tif"
        ][0]

        # add a generic file type
        self.add_file_to_resource(file_to_add=self.generic_file)

        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should not be any GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # there should be 1 GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        txt_res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".txt"
        ][0]

        # set generic logical file
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, txt_res_file.id
        )
        txt_res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".txt"
        ][0]
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")

        # now delete the folder new_folder that contains files associated with raster file type
        folder_path = "data/contents/{}".format(new_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")
        # there should not be any GeoRasterLogicalFile object
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)
        # there should be 1 GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_delete_folder_1(self):
        """Here we are testing when a folder is deleted at the root level, no aggregations/files at the
        same location (root level) get deleted."""

        self.create_composite_resource()
        # create a folder that has the same name as the file that we will be uploading later for creating a single file
        # aggregation
        new_folder = self.generic_file_name.split(".")[0]
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add a generic file type
        txt_res_file = self.add_file_to_resource(file_to_add=self.generic_file)
        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # set generic logical file
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, txt_res_file.id
        )
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")

        # now delete the folder new_folder
        folder_path = "data/contents/{}".format(new_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_delete_folder_2(self):
        """Here we are testing when a sub-folder is deleted, no aggregations/files at the
        same location (as the folder being deleted) get deleted."""

        self.create_composite_resource()
        # create a folder that has the same name as the file that we will be uploading later for creating a single file
        # aggregation
        child_folder = self.generic_file_name.split(".")[0]
        parent_folder = "my-folder"
        new_folder = f"{parent_folder}/{child_folder}"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add a generic file type to parent folder
        txt_res_file = self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=parent_folder
        )
        # there should be no GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # set generic logical file
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, txt_res_file.id
        )
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")

        # now delete the folder child_folder
        folder_path = "data/contents/{}".format(new_folder)
        remove_folder(self.user, self.composite_resource.short_id, folder_path)
        txt_res_file.refresh_from_db()
        self.assertEqual(txt_res_file.logical_file_type_name, "GenericLogicalFile")
        # there should be 1 GenericLogicalFile objects
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_core_metadata_CRUD(self):
        """test that all core metadata elements work for this resource type"""

        self.create_composite_resource()
        # test current metadata status of the composite resource

        # there should be title element
        self.assertEqual(
            self.composite_resource.metadata.title.value, "Testing Composite Resource"
        )
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
        # there should not be any geospatialrelation element
        self.assertEqual(self.composite_resource.metadata.geospatialrelations.count(), 0)
        # there should be 1 rights element
        self.assertNotEqual(self.composite_resource.metadata.rights, None)
        # there should not be any subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 0)
        # there should be 1 type element
        self.assertNotEqual(self.composite_resource.metadata.type, None)
        # there should not be any key/value metadata
        self.assertEqual(self.composite_resource.extra_metadata, {})

        # test create metadata

        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element("description", abstract="new abstract for the resource")
        # there should be abstract element
        self.assertNotEqual(self.composite_resource.metadata.description, None)
        # add a file to the resource to auto create format element
        self.raster_file_obj = open(self.raster_file, "rb")
        resource_file_add_process(
            resource=self.composite_resource,
            files=(self.raster_file_obj,),
            user=self.user,
            auto_aggregate=False,
        )
        self.assertEqual(self.composite_resource.files.all().count(), 1)
        # now there should be 1 format element
        self.assertEqual(self.composite_resource.metadata.formats.count(), 1)
        # add another creator
        metadata.create_element("creator", name="John Smith")
        # there should be 2 creators now
        self.assertEqual(self.composite_resource.metadata.creators.count(), 2)
        # add a contributor
        metadata.create_element("contributor", name="Lisa Smith")
        # there should be 1 contributor now
        self.assertEqual(self.composite_resource.metadata.contributors.count(), 1)
        # add a period type coverage
        value_dict = {
            "name": "Name for period coverage",
            "start": "1/1/2000",
            "end": "12/12/2012",
        }
        metadata.create_element("coverage", type="period", value=value_dict)
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        # there should be 2 coverage elements now
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertNotEqual(cov_pt, None)
        cov_period = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        self.assertNotEqual(cov_period, None)

        # add a funding agency element with only the required name value type
        metadata.create_element("fundingagency", agency_name="NSF")
        # there should be 1 funding agency element now
        self.assertEqual(self.composite_resource.metadata.funding_agencies.count(), 1)
        # add another identifier
        metadata.create_element(
            "identifier", name="someIdentifier", url="http://some.org/001"
        )
        # there should be 2 identifier elements
        self.assertEqual(self.composite_resource.metadata.identifiers.count(), 2)
        # add publisher element
        publisher_CUAHSI = (
            "Consortium of Universities for the Advancement of "
            "Hydrologic Science, Inc. (CUAHSI)"
        )
        url_CUAHSI = "https://www.cuahsi.org"

        # user can't set CUASHI as the publisher - when the resource has no content file
        # first delete the content file
        res_file = self.composite_resource.files.first()
        hydroshare.delete_resource_file(
            self.composite_resource.short_id, res_file.id, self.user
        )
        # publisher element can be added when the resource is published
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        with self.assertRaises(Exception):
            metadata.create_element("publisher", name=publisher_CUAHSI, url=url_CUAHSI)

        metadata.create_element("publisher", name="USGS", url="http://usgs.gov")
        # there should a publisher element now
        self.assertNotEqual(self.composite_resource.metadata.publisher, None)
        # add a relation element of uri type
        metadata.create_element(
            "relation", type="isPartOf", value="http://hydroshare.org/resource/001"
        )
        # there should be 1 relation element
        self.assertEqual(self.composite_resource.metadata.relations.count(), 1)

        # add a geospatial relation element
        metadata.create_element('geospatialrelation', type='relation',
                                value='https://geoconnex.us/ref/dams/1083460')
        # there should be 1 geospatial relation element
        self.assertEqual(self.composite_resource.metadata.geospatialrelations.count(), 1)

        # add 2 subject elements
        metadata.create_element("subject", value="sub-1")
        metadata.create_element("subject", value="sub-2")
        # there should be 2 subject elements
        self.assertEqual(self.composite_resource.metadata.subjects.count(), 2)
        # add key/value metadata
        self.composite_resource.extra_metadata = {
            "key-1": "value-1",
            "key-2": "value-2",
        }
        self.composite_resource.save()
        self.assertEqual(
            self.composite_resource.extra_metadata,
            {"key-1": "value-1", "key-2": "value-2"},
        )

        # test update metadata - first unplublish resource to allow metadata update
        self.composite_resource.raccess.published = False
        self.composite_resource.raccess.save()

        # test update title
        metadata.update_element(
            "title", self.composite_resource.metadata.title.id, value="New Title"
        )
        self.assertEqual(self.composite_resource.metadata.title.value, "New Title")
        # test update abstract
        metadata.update_element(
            "description",
            self.composite_resource.metadata.description.id,
            abstract="Updated composite resource",
        )
        self.assertEqual(
            self.composite_resource.metadata.description.abstract,
            "Updated composite resource",
        )
        # test updating funding agency
        agency_element = (
            self.composite_resource.metadata.funding_agencies.all()
            .filter(agency_name="NSF")
            .first()
        )
        metadata.update_element(
            "fundingagency",
            agency_element.id,
            award_title="Cyber Infrastructure",
            award_number="NSF-101-20-6789",
            agency_url="http://www.nsf.gov",
        )
        agency_element = (
            self.composite_resource.metadata.funding_agencies.all()
            .filter(agency_name="NSF")
            .first()
        )
        self.assertEqual(agency_element.agency_name, "NSF")
        self.assertEqual(agency_element.award_title, "Cyber Infrastructure")
        self.assertEqual(agency_element.award_number, "NSF-101-20-6789")
        self.assertEqual(agency_element.agency_url, "http://www.nsf.gov")
        some_idf = (
            self.composite_resource.metadata.identifiers.all()
            .filter(name="someIdentifier")
            .first()
        )
        metadata.update_element("identifier", some_idf.id, name="someOtherIdentifier")
        some_idf = (
            self.composite_resource.metadata.identifiers.all()
            .filter(name="someOtherIdentifier")
            .first()
        )
        self.assertNotEqual(some_idf, None)
        # update language
        self.assertEqual(self.composite_resource.metadata.language.code, "eng")
        metadata.update_element(
            "language", self.composite_resource.metadata.language.id, code="fre"
        )
        self.assertEqual(self.composite_resource.metadata.language.code, "fre")

        # test update relation type
        rel_to_update = (
            self.composite_resource.metadata.relations.all()
            .filter(type="isPartOf")
            .first()
        )
        metadata.update_element(
            "relation", rel_to_update.id, type="isVersionOf", value="dummy value 2"
        )
        rel_to_update = (
            self.composite_resource.metadata.relations.all()
            .filter(type="isVersionOf")
            .first()
        )
        self.assertEqual(rel_to_update.value, "dummy value 2")

        # change the point coverage to type box
        # even if we deleted the content file, the resource should still have the 2 coverage
        # elements
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)
        # delete the resource level point type coverage
        self.composite_resource.metadata.coverages.all().filter(
            type="point"
        ).first().delete()
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        value_dict = {
            "northlimit": "56.45678",
            "eastlimit": "120.6789",
            "southlimit": "16.45678",
            "westlimit": "16.6789",
            "units": "decimal deg",
        }
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        metadata.update_element("coverage", cov_pt.id, type="box", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertEqual(cov_pt, None)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        self.assertNotEqual(cov_box, None)

        # update creator
        creator = (
            self.composite_resource.metadata.creators.all()
            .filter(name="John Smith")
            .first()
        )
        self.assertEqual(creator.email, None)
        metadata.update_element("creator", creator.id, email="JSmith@gmail.com")
        creator = (
            self.composite_resource.metadata.creators.all()
            .filter(name="John Smith")
            .first()
        )
        self.assertEqual(creator.email, "JSmith@gmail.com")
        # update contributor
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, None)
        metadata.update_element("contributor", contributor.id, email="LSmith@gmail.com")
        contributor = self.composite_resource.metadata.contributors.first()
        self.assertEqual(contributor.email, "LSmith@gmail.com")

        # test that updating publisher element raises exception when the resource is published
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        with self.assertRaises(Exception):
            metadata.update_element(
                "publisher",
                self.composite_resource.metadata.publisher.id,
                name="USU",
                url="http://usu.edu",
            )

        # test that updating/creating creator element raises exception when the resource is published
        with self.assertRaises(Exception):
            metadata.update_element("creator", creator.id, email="JSmith@hotmail.com")
        with self.assertRaises(Exception):
            metadata.create_element("creator", name="Allen Smith")
        # test that updating title element raises exception when the resource is published
        with self.assertRaises(Exception):
            metadata.update_element(
                "title",
                self.composite_resource.metadata.title.id,
                value="Updated Title",
            )

    def test_spatial_coverage_update_long_extent(self):
        """
        Here we are testing updating spatial coverage with longitude that crosses dateline
        """
        self.create_composite_resource()
        metadata = self.composite_resource.metadata
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertEqual(cov_pt.value["east"], 56.45678)
        value_dict = {"east": "-181.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.update_element("coverage", cov_pt.id, type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_east_value = -181.45678 + 360
        self.assertEqual(cov_pt.value["east"], expected_east_value)
        value_dict = {"east": "200.1122", "north": "12.6789", "units": "decimal deg"}
        metadata.update_element("coverage", cov_pt.id, type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_east_value = 200.1122 - 360
        self.assertEqual(cov_pt.value["east"], expected_east_value)

        # using invalid east value (>360)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "361.0", "north": "12.6789", "units": "decimal deg"}
            metadata.update_element(
                "coverage", cov_pt.id, type="point", value=value_dict
            )

        # using invalid east value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "-361.0", "north": "12.6789", "units": "decimal deg"}
            metadata.update_element(
                "coverage", cov_pt.id, type="point", value=value_dict
            )

        value_dict = {
            "northlimit": "56.45678",
            "eastlimit": "120.6789",
            "southlimit": "16.45678",
            "westlimit": "16.6789",
            "units": "decimal deg",
        }

        metadata.update_element("coverage", cov_pt.id, type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_east_value = 120.6789
        self.assertEqual(cov_box.value["eastlimit"], expected_east_value)
        expected_west_value = 16.6789
        self.assertEqual(cov_box.value["westlimit"], expected_west_value)

        value_dict = {
            "northlimit": "56.45678",
            "eastlimit": "-181.6789",
            "southlimit": "16.45678",
            "westlimit": "181.6789",
            "units": "decimal deg",
        }

        metadata.update_element("coverage", cov_box.id, type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_east_value = -181.6789 + 360
        self.assertEqual(cov_box.value["eastlimit"], expected_east_value)
        expected_west_value = 181.6789 - 360
        self.assertEqual(cov_box.value["westlimit"], expected_west_value)

        # using invalid eastlimt value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-361.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid eastlimit value (> 360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "361.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid westlimit value (> 360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-180.6789",
                "southlimit": "16.45678",
                "westlimit": "361.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid westlimit value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "181.6789",
                "southlimit": "16.45678",
                "westlimit": "-361.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

    def test_spatial_coverage_create_long_extent(self):
        """
        Here we are testing creating spatial coverage with longitude that crosses dateline
        """
        self.create_composite_resource()
        metadata = self.composite_resource.metadata
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertEqual(cov_pt.value["east"], 56.45678)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )
        value_dict = {"east": "-181.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_east_value = -181.45678 + 360
        self.assertEqual(cov_pt.value["east"], expected_east_value)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )

        value_dict = {"east": "200.1122", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_east_value = 200.1122 - 360
        self.assertEqual(cov_pt.value["east"], expected_east_value)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )
        # using invalid east value (>360)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "361.0", "north": "12.6789", "units": "decimal deg"}
            metadata.create_element("coverage", type="point", value=value_dict)

        # using invalid east value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "-361.0", "north": "12.6789", "units": "decimal deg"}
            metadata.create_element("coverage", type="point", value=value_dict)

        value_dict = {
            "northlimit": "56.45678",
            "eastlimit": "120.6789",
            "southlimit": "16.45678",
            "westlimit": "16.6789",
            "units": "decimal deg",
        }

        metadata.create_element("coverage", type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_east_value = 120.6789
        self.assertEqual(cov_box.value["eastlimit"], expected_east_value)
        expected_west_value = 16.6789
        self.assertEqual(cov_box.value["westlimit"], expected_west_value)
        cov_box.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all().filter(type="box").exists()
        )
        value_dict = {
            "northlimit": "56.45678",
            "eastlimit": "-181.6789",
            "southlimit": "16.45678",
            "westlimit": "181.6789",
            "units": "decimal deg",
        }

        metadata.create_element("coverage", type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_east_value = -181.6789 + 360
        self.assertEqual(cov_box.value["eastlimit"], expected_east_value)
        expected_west_value = 181.6789 - 360
        self.assertEqual(cov_box.value["westlimit"], expected_west_value)
        cov_box.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all().filter(type="box").exists()
        )
        # using invalid eastlimt value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-361.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid eastlimit value (> 360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "361.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid westlimit value (> 360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-180.6789",
                "southlimit": "16.45678",
                "westlimit": "361.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid westlimit value (< -360)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "181.6789",
                "southlimit": "16.45678",
                "westlimit": "-361.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

    def test_spatial_coverage_update_lat_extent(self):
        """
        Here we are testing updating spatial coverage with latitude
        """
        self.create_composite_resource()
        metadata = self.composite_resource.metadata
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertEqual(cov_pt.value["east"], 56.45678)
        value_dict = {"east": "-181.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.update_element("coverage", cov_pt.id, type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_north_value = 12.6789
        self.assertEqual(cov_pt.value["north"], expected_north_value)
        value_dict = {"east": "200.1122", "north": "89.6789", "units": "decimal deg"}
        metadata.update_element("coverage", cov_pt.id, type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_north_value = 89.6789
        self.assertEqual(cov_pt.value["north"], expected_north_value)
        value_dict = {"east": "200.1122", "north": "-89.6789", "units": "decimal deg"}
        metadata.update_element("coverage", cov_pt.id, type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_north_value = -89.6789
        self.assertEqual(cov_pt.value["north"], expected_north_value)

        # using invalid north value (>90)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "61.0", "north": "90.6789", "units": "decimal deg"}
            metadata.update_element(
                "coverage", cov_pt.id, type="point", value=value_dict
            )

        # using invalid noth value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "-61.0", "north": "-90.6789", "units": "decimal deg"}
            metadata.update_element(
                "coverage", cov_pt.id, type="point", value=value_dict
            )

        value_dict = {
            "northlimit": "89.45678",
            "eastlimit": "120.6789",
            "southlimit": "-89.45678",
            "westlimit": "16.6789",
            "units": "decimal deg",
        }

        metadata.update_element("coverage", cov_pt.id, type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_north_value = 89.45678
        self.assertEqual(cov_box.value["northlimit"], expected_north_value)
        expected_south_value = -89.45678
        self.assertEqual(cov_box.value["southlimit"], expected_south_value)

        value_dict = {
            "northlimit": "-89.45678",
            "eastlimit": "-181.6789",
            "southlimit": "89.45678",
            "westlimit": "181.6789",
            "units": "decimal deg",
        }

        metadata.update_element("coverage", cov_box.id, type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_north_value = -89.45678
        self.assertEqual(cov_box.value["northlimit"], expected_north_value)
        expected_south_value = 89.45678
        self.assertEqual(cov_box.value["southlimit"], expected_south_value)

        # using invalid northlimit value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "-90.45678",
                "eastlimit": "-61.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid northlimit value (> 90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "90.45678",
                "eastlimit": "61.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid southlimit value (> 90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-180.6789",
                "southlimit": "90.45678",
                "westlimit": "61.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

        # using invalid southlimit value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "181.6789",
                "southlimit": "-90.45678",
                "westlimit": "-61.6789",
                "units": "decimal deg",
            }
            metadata.update_element(
                "coverage", cov_box.id, type="box", value=value_dict
            )

    def test_spatial_coverage_create_lat_extent(self):
        """
        Here we are testing creating spatial coverage with latitude
        """
        self.create_composite_resource()
        metadata = self.composite_resource.metadata
        # add a point type coverage
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        self.assertEqual(cov_pt.value["east"], 56.45678)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )
        value_dict = {"east": "-181.45678", "north": "89.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_north_value = 89.6789
        self.assertEqual(cov_pt.value["north"], expected_north_value)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )

        value_dict = {"east": "200.1122", "north": "-89.6789", "units": "decimal deg"}
        metadata.create_element("coverage", type="point", value=value_dict)
        cov_pt = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .first()
        )
        expected_north_value = -89.6789
        self.assertEqual(cov_pt.value["north"], expected_north_value)
        cov_pt.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all()
            .filter(type="point")
            .exists()
        )

        # using invalid north value (>90)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "61.0", "north": "90.6789", "units": "decimal deg"}
            metadata.create_element("coverage", type="point", value=value_dict)

        # using invalid north value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {"east": "-61.0", "north": "-90.6789", "units": "decimal deg"}
            metadata.create_element("coverage", type="point", value=value_dict)

        value_dict = {
            "northlimit": "89.45678",
            "eastlimit": "120.6789",
            "southlimit": "-89.45678",
            "westlimit": "16.6789",
            "units": "decimal deg",
        }

        metadata.create_element("coverage", type="box", value=value_dict)
        cov_box = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        expected_north_value = 89.45678
        self.assertEqual(cov_box.value["northlimit"], expected_north_value)
        expected_south_value = -89.45678
        self.assertEqual(cov_box.value["southlimit"], expected_south_value)
        cov_box.delete()
        self.assertFalse(
            self.composite_resource.metadata.coverages.all().filter(type="box").exists()
        )

        # using invalid northlimt value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "-90.45678",
                "eastlimit": "-61.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid northlimit value (> 90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "90.45678",
                "eastlimit": "61.6789",
                "southlimit": "16.45678",
                "westlimit": "181.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid southlimit value (> 90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "-180.6789",
                "southlimit": "90.45678",
                "westlimit": "61.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

        # using invalid southlimit value (< -90)
        with self.assertRaises(ValidationError):
            value_dict = {
                "northlimit": "56.45678",
                "eastlimit": "181.6789",
                "southlimit": "-90.45678",
                "westlimit": "-61.6789",
                "units": "decimal deg",
            }
            metadata.create_element("coverage", type="box", value=value_dict)

    def test_delete_coverage(self):
        """Here we are testing deleting of temporal and coverage metadata for composite resource"""

        self.create_composite_resource()
        # test deleting spatial coverage
        self.assertEqual(self.composite_resource.metadata.spatial_coverage, None)
        value_dict = {"east": "56.45678", "north": "12.6789", "units": "Decimal degree"}
        self.composite_resource.metadata.create_element(
            "coverage", type="point", value=value_dict
        )
        self.assertNotEqual(self.composite_resource.metadata.spatial_coverage, None)
        self.composite_resource.delete_coverage(coverage_type="spatial")
        self.assertEqual(self.composite_resource.metadata.spatial_coverage, None)

        # test deleting temporal coverage
        self.assertEqual(self.composite_resource.metadata.temporal_coverage, None)
        value_dict = {
            "name": "Name for period coverage",
            "start": "1/1/2000",
            "end": "12/12/2012",
        }
        self.composite_resource.metadata.create_element(
            "coverage", type="period", value=value_dict
        )
        self.assertNotEqual(self.composite_resource.metadata.temporal_coverage, None)
        self.composite_resource.delete_coverage(coverage_type="temporal")
        self.assertEqual(self.composite_resource.metadata.temporal_coverage, None)

    def test_metadata_xml(self):
        """Test that the call to resource.get_metadata_xml() doesn't raise exception
        for composite resource type get_metadata_xml()
        """

        # 1. create core metadata elements
        # 2. create genericlogicalfile type metadata
        # 3. create georasterlogicalfile type metadata

        self.create_composite_resource()
        # add a file to the resource to auto create format element
        self.add_file_to_resource(file_to_add=self.generic_file)

        # add a raster file to the resource to auto create format element
        self.add_file_to_resource(file_to_add=self.raster_file)

        self.assertEqual(self.composite_resource.files.all().count(), 2)
        # add some core metadata
        # create abstract
        metadata = self.composite_resource.metadata
        metadata.create_element("description", abstract="new abstract for the resource")
        # add a contributor
        metadata.create_element("contributor", name="Lisa Smith")
        # add a funding agency element with only the required name value type
        metadata.create_element("fundingagency", agency_name="NSF")
        # add a relation element of uri type
        metadata.create_element('relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')
        # add a geospatial relation element
        metadata.create_element('geospatialrelation', type='relation',
                                value='https://geoconnex.us/ref/dams/1083460')

        # add 2 subject elements
        metadata.create_element("subject", value="sub-1")
        metadata.create_element("subject", value="sub-2")
        # add key/value metadata
        self.composite_resource.extra_metadata = {
            "key-1": "value-1",
            "key-2": "value-2",
        }
        self.composite_resource.save()
        # add a publisher element
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        publisher_CUAHSI = (
            "Consortium of Universities for the Advancement of "
            "Hydrologic Science, Inc. (CUAHSI)"
        )
        url_CUAHSI = "https://www.cuahsi.org"
        metadata.create_element("publisher", name=publisher_CUAHSI, url=url_CUAHSI)

        # test no exception raised when generating the metadata xml for this resource type
        try:
            self.composite_resource.get_metadata_xml()
        except Exception as ex:
            self.fail(
                "Failed to generate metadata in xml format. Error:{}".format(str(ex))
            )

    def test_resource_coverage_auto_update(self):
        # this is to test that the spatial coverage and temporal coverage
        # for composite resource get updated by the system based on the
        # coverage metadata that all logical file objects of the resource have at anytime

        # 1. test that resource coverages get updated on LFO level metadata creation if the
        # resource level coverage data is missing
        # 2. test that resource coverages get updated on LFO level metadata update only if the
        # update resource level coverage metadata function is called
        # 3. test that resource coverages get updated on content file delete only if the
        # update resource level coverage metadata function is called

        # create a composite resource with no content file
        self.create_composite_resource()
        typed_resource = get_resource_by_shortkey(self.composite_resource.short_id)
        # at this point the there should not be any resource level coverage metadata
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 0)
        # now add the raster tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        res_file = self.composite_resource.files.all().first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, res_file.id
        )
        self.assertEqual(self.composite_resource.files.count(), 2)
        # raster logical file should have a coverage element of type box
        res_file = [
            f
            for f in self.composite_resource.files.all()
            if f.logical_file_type_name == "GeoRasterLogicalFile"
        ][0]

        raster_logical_file = res_file.logical_file
        self.assertEqual(raster_logical_file.metadata.coverages.count(), 1)
        self.assertEqual(
            raster_logical_file.metadata.coverages.all().filter(type="box").count(), 1
        )
        # now the resource should have a coverage metadata element of type box
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 1)
        self.assertEqual(
            self.composite_resource.metadata.coverages.all().filter(type="box").count(),
            1,
        )

        # the spatial coverage at the file type level should be exactly the same as the
        # resource level - due to auto update feature in composite resource. Note: auto update
        # occurs only if the coverage is missing at the resource level
        res_coverage = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="box").first()
        )
        self.assertEqual(
            res_coverage.value["projection"], raster_lfo_coverage.value["projection"]
        )
        self.assertEqual(
            res_coverage.value["units"], raster_lfo_coverage.value["units"]
        )
        self.assertEqual(
            res_coverage.value["northlimit"], raster_lfo_coverage.value["northlimit"]
        )
        self.assertEqual(
            res_coverage.value["southlimit"], raster_lfo_coverage.value["southlimit"]
        )
        self.assertEqual(
            res_coverage.value["eastlimit"], raster_lfo_coverage.value["eastlimit"]
        )
        self.assertEqual(
            res_coverage.value["westlimit"], raster_lfo_coverage.value["westlimit"]
        )

        # At this point there is not temporal coverage either at the file type level or resource
        # level
        self.assertEqual(
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .count(),
            0,
        )
        self.assertEqual(
            raster_logical_file.metadata.coverages.all().filter(type="period").count(),
            0,
        )

        # adding temporal coverage to the logical file should add the temporal coverage to the
        # resource - auto update action as the resource is missing temporal coverage data
        value_dict = {"start": "1/1/2010", "end": "12/12/2015"}
        raster_logical_file.metadata.create_element(
            "coverage", type="period", value=value_dict
        )
        self.assertEqual(
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .count(),
            1,
        )
        self.assertEqual(
            raster_logical_file.metadata.coverages.all().filter(type="period").count(),
            1,
        )
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="period").first()
        )
        self.assertEqual(
            res_coverage.value["start"], raster_lfo_coverage.value["start"]
        )
        self.assertEqual(res_coverage.value["end"], raster_lfo_coverage.value["end"])
        self.assertEqual(res_coverage.value["start"], "1/1/2010")
        self.assertEqual(res_coverage.value["end"], "12/12/2015")

        # test updating the temporal coverage for file type should not update the temporal coverage
        # for the resource automatically since the resource already has temporal data
        value_dict = {"start": "12/1/2010", "end": "12/1/2015"}
        raster_logical_file.metadata.update_element(
            "coverage", raster_lfo_coverage.id, type="period", value=value_dict
        )
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="period").first()
        )
        self.assertNotEqual(
            res_coverage.value["start"], raster_lfo_coverage.value["start"]
        )
        self.assertNotEqual(res_coverage.value["end"], raster_lfo_coverage.value["end"])

        # test aggregation/logical file temporal coverage has changed
        self.assertEqual(raster_lfo_coverage.value["start"], "12/1/2010")
        self.assertEqual(raster_lfo_coverage.value["end"], "12/1/2015")

        # test resource temporal coverage has not changed
        self.assertEqual(res_coverage.value["start"], "1/1/2010")
        self.assertEqual(res_coverage.value["end"], "12/12/2015")

        # test updating the resource coverage by user action - which should update the resource
        # coverage as a superset of all coverages of all the contained aggregations/logical files
        typed_resource.update_temporal_coverage()
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="period").first()
        )
        self.assertEqual(
            res_coverage.value["start"], raster_lfo_coverage.value["start"]
        )
        self.assertEqual(res_coverage.value["end"], raster_lfo_coverage.value["end"])

        # test aggregation/logical file temporal coverage has changed
        self.assertEqual(raster_lfo_coverage.value["start"], "12/1/2010")
        self.assertEqual(raster_lfo_coverage.value["end"], "12/1/2015")

        # test that the resource coverage is superset of file type (aggregation) coverages
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 3)
        res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".txt"
        ][0]

        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, res_file.id
        )

        res_file = [
            f
            for f in self.composite_resource.files.all()
            if f.logical_file_type_name == "GenericLogicalFile"
        ][0]

        generic_logical_file = res_file.logical_file
        # there should not be any coverage for the generic LFO at this point
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 0)
        # create temporal coverage for generic LFO
        value_dict = {"start": "1/1/2009", "end": "1/1/2015"}
        generic_logical_file.metadata.create_element(
            "coverage", type="period", value=value_dict
        )
        self.assertEqual(generic_logical_file.metadata.coverages.count(), 1)
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        self.assertNotEqual(res_coverage, None)

        # test updating the resource coverage by user action - which should update the resource
        # coverage as a superset of all coverages of all the contained aggregations/logical files
        typed_resource.update_temporal_coverage()
        typed_resource.update_spatial_coverage()
        # resource temporal coverage is now super set of the 2 temporal coverages
        # in 2 LFOs
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        self.assertEqual(res_coverage.value["start"], "1/1/2009")
        self.assertEqual(res_coverage.value["end"], "12/1/2015")
        # test resource superset spatial coverage
        res_coverage = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        self.assertEqual(res_coverage.value["projection"], "WGS 84 EPSG:4326")
        self.assertEqual(res_coverage.value["units"], "Decimal degrees")
        self.assertAlmostEqual(res_coverage.value["northlimit"], 42.050026959773426, places=14)
        self.assertAlmostEqual(res_coverage.value["eastlimit"], -111.577737181062, places=14)
        self.assertAlmostEqual(res_coverage.value["southlimit"], 41.98722286030319, places=14)
        self.assertAlmostEqual(res_coverage.value["westlimit"], -111.69756293084063, places=14)
        value_dict = {
            "east": "-110.88845678",
            "north": "43.6789",
            "units": "Decimal deg",
        }
        generic_logical_file.metadata.create_element(
            "coverage", type="point", value=value_dict
        )

        # update resource spatial coverage from aggregations spatial coverages
        typed_resource.update_spatial_coverage()
        res_coverage = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        self.assertEqual(res_coverage.value["projection"], "WGS 84 EPSG:4326")
        self.assertEqual(res_coverage.value["units"], "Decimal degrees")
        self.assertEqual(res_coverage.value["northlimit"], 43.6789)
        self.assertEqual(res_coverage.value["eastlimit"], -110.88845678)
        self.assertEqual(res_coverage.value["southlimit"], 41.98722286030319)
        self.assertEqual(res_coverage.value["westlimit"], -111.69756293084063)
        # update the LFO coverage to box type
        value_dict = {
            "eastlimit": "-110.88845678",
            "northlimit": "43.6789",
            "westlimit": "-112.78967",
            "southlimit": "40.12345",
            "units": "Decimal deg",
        }
        lfo_spatial_coverage = generic_logical_file.metadata.spatial_coverage
        generic_logical_file.metadata.update_element(
            "coverage", lfo_spatial_coverage.id, type="box", value=value_dict
        )

        # update resource spatial coverage from aggregations spatial coverages
        typed_resource.update_spatial_coverage()

        res_coverage = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        self.assertEqual(res_coverage.value["projection"], "WGS 84 EPSG:4326")
        self.assertEqual(res_coverage.value["units"], "Decimal degrees")
        self.assertEqual(res_coverage.value["northlimit"], 43.6789)
        self.assertEqual(res_coverage.value["eastlimit"], -110.88845678)
        self.assertEqual(res_coverage.value["southlimit"], 40.12345)
        self.assertEqual(res_coverage.value["westlimit"], -112.78967)

        # deleting the generic file (aggregation) should NOT reset the coverage of the resource to
        # that of the raster LFO (aggregation)
        res_file = [
            f
            for f in self.composite_resource.files.all()
            if f.logical_file_type_name == "GenericLogicalFile"
        ][0]
        hydroshare.delete_resource_file(
            self.composite_resource.short_id, res_file.id, self.user
        )
        res_coverage = (
            self.composite_resource.metadata.coverages.all().filter(type="box").first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="box").first()
        )
        self.assertEqual(
            res_coverage.value["projection"], raster_lfo_coverage.value["projection"]
        )
        self.assertEqual(
            res_coverage.value["units"], raster_lfo_coverage.value["units"]
        )
        self.assertNotEqual(
            res_coverage.value["northlimit"], raster_lfo_coverage.value["northlimit"]
        )
        self.assertNotEqual(
            res_coverage.value["southlimit"], raster_lfo_coverage.value["southlimit"]
        )
        self.assertNotEqual(
            res_coverage.value["eastlimit"], raster_lfo_coverage.value["eastlimit"]
        )
        self.assertNotEqual(
            res_coverage.value["westlimit"], raster_lfo_coverage.value["westlimit"]
        )
        res_coverage = (
            self.composite_resource.metadata.coverages.all()
            .filter(type="period")
            .first()
        )
        raster_lfo_coverage = (
            raster_logical_file.metadata.coverages.all().filter(type="period").first()
        )
        self.assertNotEqual(
            res_coverage.value["start"], raster_lfo_coverage.value["start"]
        )
        self.assertEqual(res_coverage.value["end"], raster_lfo_coverage.value["end"])
        self.assertNotEqual(res_coverage.value["start"], "12/1/2010")
        self.assertEqual(res_coverage.value["end"], "12/1/2015")

        # deleting the remaining content file from resource should leave the resource
        # coverage element unchanged
        res_file = [
            f
            for f in self.composite_resource.files.all()
            if f.logical_file_type_name == "GeoRasterLogicalFile"
        ][0]
        hydroshare.delete_resource_file(
            self.composite_resource.short_id, res_file.id, self.user
        )
        self.assertEqual(self.composite_resource.files.count(), 0)
        self.assertEqual(self.composite_resource.metadata.coverages.count(), 2)

    def test_get_aggregations(self):
        """Here wre are testing the function 'get_logical_files()'
        Test for single file aggregation and multi-file aggregation (logical file)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(
            len(self.composite_resource.get_logical_files("GenericLogicalFile")), 0
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # now create a generic aggregation - single-file aggregation
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        self.assertEqual(
            len(self.composite_resource.get_logical_files("GenericLogicalFile")), 1
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

        self.assertEqual(
            len(self.composite_resource.get_logical_files("GeoRasterLogicalFile")), 0
        )
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 0)

        # add a tif file
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile - multi-file aggregation
        tif_res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".tif"
        ][0]
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )

        self.assertEqual(
            len(self.composite_resource.get_logical_files("GeoRasterLogicalFile")), 1
        )
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)

        self.assertEqual(
            len(self.composite_resource.get_logical_files("GenericLogicalFile")), 1
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 1)

    def test_aggregation_types(self):
        """Here wre are testing the 'aggregation_types' property of the resource
        Test for single file, raster, csv, and netcdf
        """

        self.create_composite_resource()

        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(
            len(self.composite_resource.get_logical_files("GenericLogicalFile")), 0
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        # now create a generic aggregation - single-file aggregation
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )

        # now test the aggregation_types property
        self.assertEqual(self.composite_resource.aggregation_types, ["Single File Content"])

        # add a tif file
        self.add_file_to_resource(file_to_add=self.raster_file)
        # make the tif as part of the GeoRasterLogicalFile - multi-file aggregation
        tif_res_file = [
            f for f in self.composite_resource.files.all() if f.extension == ".tif"
        ][0]
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )

        self.assertEqual(self.composite_resource.aggregation_types,
                         ["Single File Content", "Geographic Raster Content"])

        # add a csv file to the resource
        self.add_file_to_resource(file_to_add=self.csv_file)

        csv_res_file = self.composite_resource.files.last()
        # set the csv file to CSV file aggregation
        CSVLogicalFile.set_file_type(
            self.composite_resource, self.user, csv_res_file.id
        )

        self.assertEqual(self.composite_resource.aggregation_types,
                         ["Single File Content", "Geographic Raster Content", "CSV Content"])

        self.add_file_to_resource(file_to_add=self.netcdf_file_no_coverage)
        # create NetCDF aggregation using the netcdf file
        nc_res_file = self.composite_resource.files.last()
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, nc_res_file.id
        )
        self.assertEqual(self.composite_resource.aggregation_types,
                         ["Single File Content", "Multidimensional Content", "Geographic Raster Content",
                          "CSV Content"])

    def test_can_be_public_or_discoverable_with_no_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains no aggregation (logical file)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = (
            self.composite_resource.metadata.get_required_missing_elements()
        )
        self.assertEqual(len(missing_elements), 2)
        self.assertIn("Abstract (at least 150 characters)", missing_elements)
        self.assertIn("Keywords (at least 3)", missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_cannot_be_published_with_refenced_url_single_file_aggregation(self):
        """
        test a composite resource that includes referenced url single file aggregation cannot be
        published
        """
        self.create_composite_resource()
        url_file_base_name = "test_url"
        ret_status, msg, _ = add_reference_url_to_resource(
            self.user,
            self.composite_resource.short_id,
            self.valid_url,
            url_file_base_name,
            "data/contents",
        )
        self.assertEqual(ret_status, status.HTTP_200_OK)
        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertFalse(self.composite_resource.can_be_public_or_discoverable)
        missing_elements = (
            self.composite_resource.metadata.get_required_missing_elements()
        )
        self.assertEqual(len(missing_elements), 2)
        self.assertIn("Abstract (at least 150 characters)", missing_elements)
        self.assertIn("Keywords (at least 3)", missing_elements)
        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        # at this point resource can be public or discoverable, but cannot be published
        self.assertTrue(self.composite_resource.can_be_public_or_discoverable)
        self.assertFalse(self.composite_resource.can_be_submitted_for_metadata_review)

    def test_can_be_public_or_discoverable_with_single_file_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains a single file aggregation (e.g., generic aggregation).
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        gen_aggr = GenericLogicalFile.objects.first()
        # check that there are no missing required metadata for the generic single file aggregation
        self.assertEqual(len(gen_aggr.metadata.get_required_missing_elements()), 0)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = (
            self.composite_resource.metadata.get_required_missing_elements()
        )
        self.assertEqual(len(missing_elements), 2)
        self.assertIn("Abstract (at least 150 characters)", missing_elements)
        self.assertIn("Keywords (at least 3)", missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_can_be_public_or_discoverable_with_multi_file_aggregation(self):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains a multi-file aggregation (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add a tif file
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        raster_aggr = GeoRasterLogicalFile.objects.first()
        # check that there are no missing required metadata for the raster aggregation
        self.assertEqual(len(raster_aggr.metadata.get_required_missing_elements()), 0)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 3 required core metadata elements missing at this point
        missing_elements = (
            self.composite_resource.metadata.get_required_missing_elements()
        )
        self.assertEqual(len(missing_elements), 2)
        self.assertIn("Abstract (at least 150 characters)", missing_elements)
        self.assertIn("Keywords (at least 3)", missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_can_be_public_or_discoverable_with_netcdf_aggregation_no_spatial_coverage(
        self,
    ):
        """Here we are testing the function 'can_be_public_or_discoverable()'
        This function should return False unless we have the required metadata at the resource level
        when the resource contains a netcdf aggregation that doesn't have spatial coverage
        """

        self.create_composite_resource()

        # at this point resource can't be public or discoverable as some core metadata missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)
        # add the netcdf file that doesn't have spatial reference
        self.add_file_to_resource(file_to_add=self.netcdf_file_no_coverage)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # create NetCDF aggregation using the netcdf file
        nc_res_file = self.composite_resource.files.first()
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, nc_res_file.id
        )
        nc_aggr = NetCDFLogicalFile.objects.first()

        # check the nc aggregation doesn't have spatial coverage
        self.assertEqual(nc_aggr.metadata.originalCoverage, None)
        self.assertEqual(nc_aggr.metadata.coverages.exists(), False)
        # check that there are no missing required metadata for the nc aggregation
        self.assertEqual(len(nc_aggr.metadata.get_required_missing_elements()), 0)

        # at this point still resource can't be public or discoverable - as some core metadata
        # is missing
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, False)

        # there should be 2 required core metadata elements missing at this point
        missing_elements = (
            self.composite_resource.metadata.get_required_missing_elements()
        )
        self.assertEqual(len(missing_elements), 2)
        self.assertIn("Abstract (at least 150 characters)", missing_elements)
        self.assertIn("Keywords (at least 3)", missing_elements)

        # add the above missing elements
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        # at this point resource can be public or discoverable
        self.assertEqual(self.composite_resource.can_be_public_or_discoverable, True)

    def test_can_be_submitted_for_metadata_review_with_model_aggregation(self):
        """Here we are testing the function 'can_be_submitted_for_metadata_review()'
        We are testing the following scenarios:
        - when the resource contains a model instance aggregation and not linked to any model program aggregation
          In this case resource can be published
        - when the resource contains one model instance aggregation and is linked to a model program aggregation
        within the same resource
          In this case resource can be published
        """

        self.create_composite_resource()
        resource = self.composite_resource
        # create a model instance aggregation
        upload_folder = ""
        file_to_upload = UploadedFile(
            file=open(self.generic_file, "rb"), name=os.path.basename(self.generic_file)
        )

        res_file = add_file_to_resource(
            resource, file_to_upload, folder=upload_folder, check_target_folder=True
        )

        # set file to model instance aggregation type
        ModelInstanceLogicalFile.set_file_type(resource, self.user, res_file.id)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        self.assertFalse(resource.can_be_submitted_for_metadata_review)
        # create abstract
        metadata = self.composite_resource.metadata
        # add Abstract (element name is description)
        metadata.create_element("description", abstract="new abstract for the resource")
        # add keywords (element name is subject)
        metadata.create_element("subject", value="sub-1")
        self.assertTrue(resource.can_be_submitted_for_metadata_review)

        # create a model program aggregation within the same resource and link it to model instance
        file_to_upload = UploadedFile(
            file=open(self.zip_file, "rb"), name=os.path.basename(self.zip_file)
        )

        res_file = add_file_to_resource(
            resource, file_to_upload, folder=upload_folder, check_target_folder=True
        )

        # set file to model program aggregation type
        ModelProgramLogicalFile.set_file_type(resource, self.user, res_file.id)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        # link model instance to model program
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        mi_aggr.metadata.executed_by = ModelProgramLogicalFile.objects.first()
        mi_aggr.metadata.save()
        # since the 2 linked model aggregations are in the same resource it should be possible
        # to publish this resource
        self.assertTrue(resource.can_be_submitted_for_metadata_review)

    def test_supports_folder_creation_non_aggregation_folder(self):
        """Here we are testing the function supports_folder_creation()
        Test that this function returns True when we check for creating a folder inside a folder
        that contains a resource file that is not part of any aggregation
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(gen_res_file.file_folder, "")
        # we should be able to create this new folder
        new_folder_full_path = os.path.join(
            self.composite_resource.file_path, "my-new-folder"
        )
        self.assertEqual(
            self.composite_resource.supports_folder_creation(new_folder_full_path), True
        )
        # create the folder
        new_folder_path = os.path.join("data", "contents", "my-new-folder")
        create_folder(self.composite_resource.short_id, new_folder_path)
        old_file_path = self.composite_resource.files.get().short_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(
            self.user,
            self.composite_resource.short_id,
            os.path.join("data", "contents", old_file_path),
            os.path.join(new_folder_path, self.generic_file_name),
        )

        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(gen_res_file.file_folder, "my-new-folder")
        # test that we should be able to create a folder inside the folder that contains
        # a resource file that is part of a Generic Logical file
        new_folder_full_path = os.path.join(new_folder_full_path, "another-folder")
        self.assertTrue(
            self.composite_resource.supports_folder_creation(new_folder_full_path)
        )

    def test_supports_folder_creation_single_file_aggregation_folder(self):
        """Here we are testing the function supports_folder_creation()
        Test that this function returns True when we check for creating a folder inside a folder
        that contains a single-file aggregation (e.g., generic aggregation)
        """
        self.create_composite_resource()
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        # we should be able to create this new folder
        new_folder = "my-new-folder"
        new_folder_full_path = os.path.join(
            self.composite_resource.file_path, new_folder
        )
        self.assertEqual(
            self.composite_resource.supports_folder_creation(new_folder_full_path), True
        )
        # create the folder
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        old_file_path = self.composite_resource.files.get().short_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(
            self.user,
            self.composite_resource.short_id,
            os.path.join("data", "contents", old_file_path),
            os.path.join(new_folder_path, self.generic_file_name),
        )

        # test that we should be able to create a folder inside the folder that contains
        # a resource file that is part of a Generic Logical file
        new_folder_full_path = os.path.join(new_folder_full_path, "another-folder")
        self.assertTrue(
            self.composite_resource.supports_folder_creation(new_folder_full_path)
        )

    def test_supports_rename_single_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a file that is part of a single-file aggregation
        (e.g., generic aggregation)
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        self.assertEqual(self.generic_file_name, gen_res_file.file_name)
        # rename file
        file_rename = "renamed_file.txt"
        self.assertNotEqual(gen_res_file.file_name, file_rename)
        src_full_path = os.path.join(
            self.composite_resource.file_path, self.generic_file_name
        )
        tgt_full_path = os.path.join(self.composite_resource.file_path, file_rename)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            True,
        )

    def test_supports_rename_multi_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it shouldn't be possible to rename a file that is part of a multi-file
        aggregation (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        tif_res_file = self.composite_resource.files.first()
        # test renaming of any files that are part of GeoRasterLogicalFile is not allowed
        new_file_rename = "small_logan_1.tif"
        self.assertNotEqual(tif_res_file.file_name, new_file_rename)
        src_full_path = os.path.join(
            self.composite_resource.file_path, self.raster_file_name
        )
        tgt_full_path = os.path.join(self.composite_resource.file_path, new_file_rename)

        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            False,
        )

    def test_supports_move_single_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to move a single file aggregation
        (e.g., generic aggregation) to a folder that doesn't represent an aggregation
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type - single file aggregation
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        src_full_path = os.path.join(
            self.composite_resource.file_path, self.generic_file_name
        )

        # create a new folder so that we can test if the generic file can be moved there or not
        new_folder = "my-new-folder"
        new_folder_full_path = os.path.join(
            self.composite_resource.file_path, new_folder
        )
        new_folder_path = os.path.join("data", "contents", new_folder)
        self.assertTrue(
            self.composite_resource.supports_folder_creation(new_folder_full_path)
        )
        # create the folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # set the target path for the file to be moved to
        tgt_full_path = os.path.join(new_folder_full_path, self.generic_file_name)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            True,
        )

    def test_supports_rename_single_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a folder that contains a single file aggregation
        (e.g., generic aggregation)
        """

        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # test that we can rename the resource file that's part of the GenericLogical File
        gen_res_file = self.composite_resource.files.first()
        # crate a generic logical file type
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        gen_res_file_basename = hydroshare.utils.get_resource_file_name_and_extension(
            gen_res_file
        )[1]
        self.assertEqual(self.generic_file_name, gen_res_file_basename)

        # create a new folder and move the generic aggregation file there
        new_folder = "my-new-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        src_path = os.path.join("data", "contents", self.generic_file_name)
        tgt_path = new_folder_path
        # now move the file to this new folder
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        # test rename folder
        folder_rename = "{}-1".format(new_folder)
        src_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        tgt_full_path = os.path.join(self.composite_resource.file_path, folder_rename)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            True,
        )

    def test_supports_rename_multi_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to rename a folder that contains a multi-file aggregation
        (e.g., raster aggregation)
        """

        self.create_composite_resource()
        raster_folder = "raster-folder"
        raster_folder_path = "data/contents/{}".format(raster_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, raster_folder_path)
        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=raster_folder
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, raster_folder)

        # test renaming a folder that contains resource files that are part of the
        # GeoRasterLogicalFile is allowed
        folder_rename = "{}_1".format(res_file.file_folder)
        src_full_path = os.path.join(
            self.composite_resource.file_path, res_file.file_folder
        )
        tgt_full_path = os.path.join(self.composite_resource.file_path, folder_rename)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            True,
        )

    def test_supports_move_multi_file_aggregation_file(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should not be possible to move a file that is part of a multi-file aggregation
        (e.g., raster aggregation)
        """

        self.create_composite_resource()

        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(file_to_add=self.raster_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )

        # create a new folder where to move the multi-file aggregation file - the tif file
        new_folder = "my-new-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # test that we can't  move a file to a folder that contains resource files that are part
        # of GeoRasterLogicalFile object
        tif_res_file = self.composite_resource.files.first()
        src_full_path = tif_res_file.storage_path
        tgt_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            False,
        )

    def test_supports_move_multi_file_aggregation_folder(self):
        """here we are testing the function supports_move_or_rename_file_or_folder() of the
        composite resource class
        Test that it should be possible to move a folder that represents a multi-file aggregation
        (e.g., raster aggregation) to a folder that does not represent any multi-file aggregation
        """

        self.create_composite_resource()
        raster_folder = "raster-folder"
        raster_folder_path = "data/contents/{}".format(raster_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, raster_folder_path)
        # add a raster tif file to the resource which will be part of
        # a GoeRasterLogicalFile object
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=raster_folder
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, raster_folder)

        # create a new folder
        new_folder = "some-other-folder"
        new_folder_path = os.path.join("data", "contents", new_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)

        # test it should be possible to move the 'raster-folder' folder that
        # contains the raster aggregation to the 'some-other-folder' that we created above
        src_full_path = os.path.join(
            self.composite_resource.file_path, res_file.file_folder
        )
        tgt_full_path = os.path.join(self.composite_resource.file_path, new_folder)
        # this is the function we are testing
        self.assertEqual(
            self.composite_resource.supports_rename_path(src_full_path, tgt_full_path),
            True,
        )

    def test_supports_zip_non_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that contains file(s) that is not part of any aggregation
        is allowed
        """

        self.create_composite_resource()

        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = "my-new-folder"
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a new folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join("data", "contents", self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        # test that we can zip the folder my_new_folder as this folder has no aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_zip_single_file_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that contains a single file aggregation
        (e.g., generic aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a file to the resource which will be part of  a GenericLogicalFile object later
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = "my-new-folder"
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join("data", "contents", self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        gen_res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        # test that we can zip the folder my_new_folder which contains an aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_zip_single_file_aggregation_parent_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a parent folder of a folder that contains a single file aggregation
        (e.g., generic aggregation) is not allowed
        """

        self.create_composite_resource()

        # add a file to the resource which will be part of  a GenericLogicalFile object later
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = "generic-folder"
        new_folder_path = "data/contents/{}".format(new_folder)

        # create a folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = os.path.join("data", "contents", self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        gen_res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )

        # create a folder
        parent_folder = "parent-folder"
        new_folder_path = "data/contents/{}".format(parent_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the generic-folder to this new folder
        gen_res_file = self.composite_resource.files.first()
        src_path = os.path.join("data", "contents", gen_res_file.file_folder)
        tgt_path = os.path.join(new_folder_path, gen_res_file.file_folder)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        gen_res_file = self.composite_resource.files.first()
        self.assertEqual(
            gen_res_file.file_folder, "{0}/{1}".format(parent_folder, new_folder)
        )
        # test that we can zip the folder parent_folder which contains a
        # folder (generic-folder) that has an aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, parent_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_zip_multi_file_aggregation_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a folder that contains a multi-file aggregation
        (e.g., raster aggregation) is not allowed
        """

        self.create_composite_resource()
        raster_folder = "raster-folder"
        raster_folder_path = "data/contents/{}".format(raster_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, raster_folder_path)
        # add a tif file to the resource
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=raster_folder
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = self.composite_resource.files.first()
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        res_file = self.composite_resource.files.first()
        base_file_name, _ = os.path.splitext(self.raster_file_name)

        # resource file exists in a folder
        self.assertEqual(res_file.file_folder, raster_folder)

        # test that we can zip the folder that represents the aggregation
        folder_to_zip = os.path.join(
            self.composite_resource.file_path, res_file.file_folder
        )
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_zip_multi_file_aggregation_parent_folder(self):
        """Here we are testing the function supports_zip()
        Test that zipping a parent folder of a folder that contains a multi file aggregation
        (e.g., raster aggregation) is not allowed
        """

        self.create_composite_resource()
        raster_folder = "raster-folder"
        raster_folder_path = "data/contents/{}".format(raster_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, raster_folder_path)
        # add a file to the resource which will be part of  a raster aggregation later
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=raster_folder
        )
        self.assertEqual(self.composite_resource.files.count(), 1)

        tif_res_file = self.composite_resource.files.first()
        self.assertEqual(tif_res_file.file_folder, raster_folder)
        # create the raster aggregation
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        res_file = self.composite_resource.files.first()
        self.assertEqual(res_file.file_folder, raster_folder)

        # create a folder
        parent_folder = "parent-folder"
        new_folder_path = "data/contents/{}".format(parent_folder)
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the aggregation folder to this new folder
        src_path = os.path.join("data", "contents", res_file.file_folder)
        tgt_path = os.path.join(new_folder_path, res_file.file_folder)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )

        tif_res_file = self.composite_resource.files.first()
        self.assertEqual(
            tif_res_file.file_folder,
            "{0}/{1}".format(parent_folder, res_file.file_folder),
        )
        # test that we can zip the folder parent_folder which contains a
        # a folder that represents an aggregation
        folder_to_zip = os.path.join(self.composite_resource.file_path, parent_folder)
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)

    def test_supports_delete_original_folder_on_zip(self):
        """Here we are testing the function supports_delete_original_folder_on_zip() of the
        composite resource class"""

        self.create_composite_resource()

        # test that a folder containing a resource file that's part of the GenericLogicalFile
        # can be deleted after that folder gets zipped
        # add a file to the resource which will be part of  a GenericLogicalFile object
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        new_folder = "my-new-folder"
        new_folder_path = "data/contents/{}".format(new_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, new_folder_path)
        # now move the file to this new folder
        src_path = "data/contents/{}".format(self.generic_file_name)
        tgt_path = os.path.join(new_folder_path, self.generic_file_name)
        move_or_rename_file_or_folder(
            self.user, self.composite_resource.short_id, src_path, tgt_path
        )
        # folder_to_zip = self.composite_resource.short_id + '/data/contents/my-new-folder'
        folder_to_zip = os.path.join(self.composite_resource.file_path, new_folder)
        # test that we can zip the folder my_new_folder
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)
        # this is the function we are testing - my-new-folder can be deleted
        self.assertEqual(
            self.composite_resource.supports_delete_folder_on_zip(folder_to_zip), True
        )

        # test that a folder containing a resource file that's part of the GeoRasterLogicalFile
        # can't be deleted after that folder gets zipped

        raster_folder = "raster-folder"
        raster_folder_path = "data/contents/{}".format(raster_folder)
        # create the folder
        create_folder(self.composite_resource.short_id, raster_folder_path)
        # add a file to the resource which will be part of  a GeoRasterLogicalFile object
        self.add_file_to_resource(
            file_to_add=self.raster_file, upload_folder=raster_folder
        )
        self.assertEqual(self.composite_resource.files.count(), 2)
        # make the tif as part of the GeoRasterLogicalFile
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ".tif"
        )[0]
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        self.assertEqual(self.composite_resource.files.count(), 3)
        tif_res_file = hydroshare.utils.get_resource_files_by_extension(
            self.composite_resource, ".tif"
        )[0]

        # resource file exists in a folder
        self.assertEqual(tif_res_file.file_folder, raster_folder)
        folder_to_zip = os.path.join(
            self.composite_resource.file_path, tif_res_file.file_folder
        )
        # test that we can zip the folder my_new_folder which contains as raster aggregation
        self.assertEqual(self.composite_resource.supports_zip(folder_to_zip), True)
        # this is the function we are testing - aggregation folder can't be deleted
        self.assertEqual(
            self.composite_resource.supports_delete_folder_on_zip(folder_to_zip), False
        )

    def test_copy_resource_with_no_aggregation(self):
        """Here we are testing that we can create a copy of a composite resource that contains no
        aggregations"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        # copy resource files and metadata
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)

    def test_copy_resource_with_tar_gz(self):
        """Here we are testing that we can create a copy of a composite resource that contains a
        tar.gz file"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_tar_gz_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        # copy resource files and metadata
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)

    def test_copy_resource_with_single_file_aggregation(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        single file aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        gen_res_file = self.composite_resource.files.first()
        # set the generic file to single file aggregation
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )

        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 2)

    def test_copy_resource_with_csv_file_aggregation(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        csv file aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add the csv file to the resource
        self.add_file_to_resource(file_to_add=self.csv_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        csv_res_file = self.composite_resource.files.first()
        # set the csv file to CSV file aggregation
        CSVLogicalFile.set_file_type(
            self.composite_resource, self.user, csv_res_file.id
        )
        self.assertEqual(CSVLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )

        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(CSVLogicalFile.objects.count(), 2)
        csv_logical_files = CSVLogicalFile.objects.all()
        self.assertEqual(csv_logical_files[0].metadata.tableSchema, csv_logical_files[1].metadata.tableSchema)
        # compare preview_data
        self.assertEqual(csv_logical_files[0].preview_data, csv_logical_files[1].preview_data)

    def test_copy_resource_with_file_set_aggregation_1(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = "fileset_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=new_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=new_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)

    def test_copy_resource_with_file_set_aggregation_2(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        file set aggregation that contains another aggregation (NetCDF aggregation)"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = "fileset_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=new_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=new_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # add the nc file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.netcdf_file, upload_folder=new_folder
        )
        nc_res_file = ResourceFile.get(
            self.composite_resource, file=self.netcdf_file_name, folder=new_folder
        )
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, file_id=nc_res_file.id
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        # there should be 3 files - 2 files that we uploaded and one text file generated for netcdf
        # aggregation
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_copy_resource_with_file_set_aggregation_3(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        nested file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        parent_fs_folder = "parent_fs_folder"
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=parent_fs_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=parent_fs_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        child_fs_folder = "{}/child_fs_folder".format(parent_fs_folder)
        ResourceFile.create_folder(self.composite_resource, child_fs_folder)
        # add the the txt file to the resource at the above child folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=child_fs_folder
        )
        # set the child folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=child_fs_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 4)

    def test_copy_resource_with_file_set_aggregation_4(self):
        """Here we are testing that we can create a copy of a composite resource that contains one
        file set aggregation where the file set aggregation has no files"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = "fileset_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=new_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=new_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 1)
        # delete the file that's part of the fileset aggregation
        res_file = FileSetLogicalFile.objects.first().files.first()
        delete_resource_file(self.composite_resource.short_id, res_file.id, self.user)
        self.assertEqual(FileSetLogicalFile.objects.first().files.count(), 0)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 0)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        for fs in FileSetLogicalFile.objects.all():
            self.assertEqual(fs.folder, new_folder)
            self.assertEqual(fs.files.count(), 0)

    def test_copy_resource_with_netcdf_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        netcdf aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a nc file to the resource
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        nc_res_file = self.composite_resource.files.first()
        # set the nc file to netcdf aggregation
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, nc_res_file.id
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_copy_resource_with_timeseries_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a sqlite file to the resource
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        sql_res_file = self.composite_resource.files.first()
        # set the sqlite file to timeseries aggregation
        TimeSeriesLogicalFile.set_file_type(
            self.composite_resource, self.user, sql_res_file.id
        )
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 2)

    def test_copy_resource_with_reftimeseries_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        ref timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a json file to the resource
        self.add_file_to_resource(file_to_add=self.json_file)
        json_res_file = self.composite_resource.files.first()
        # set the json file to ref timeseries aggregation
        RefTimeseriesLogicalFile.set_file_type(
            self.composite_resource, self.user, json_res_file.id
        )
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 2)

    def test_copy_resource_with_raster_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        raster aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        tif_res_file = self.composite_resource.files.first()
        # set the tif file to raster aggregation
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)

    def test_copy_resource_with_feature_aggregation(self):
        """Here were testing that we can create a copy of a composite resource that contains a
        geo feature aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a shp file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shp_file)
        shp_res_file = self.composite_resource.files.first()
        # add a shx file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shx_file)
        # add a dbf file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_dbf_file)

        # set the shp file to geofeature aggregation
        GeoFeatureLogicalFile.set_file_type(
            self.composite_resource, self.user, shp_res_file.id
        )
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        # create a copy of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user, action="copy"
        )
        new_composite_resource = hydroshare.copy_resource(
            self.composite_resource, new_composite_resource
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 2)

    def test_version_resource_with_no_aggregation(self):
        """Here we are testing that we can create a new version of a composite resource that contains no
        aggregations"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)

    def test_version_resource_with_single_file_aggregation(self):
        """Here we are testing that we can create a new version of a composite resource that contains one
        single file aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        gen_res_file = self.composite_resource.files.first()
        # set the generic file to single file aggregation
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )

        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(GenericLogicalFile.objects.count(), 2)

    def test_version_resource_with_csv_file_aggregation(self):
        """Here we are testing that we can create a new version of a composite resource that contains one
        CSV file aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a csv file to the resource
        self.add_file_to_resource(file_to_add=self.csv_file)
        csv_res_file = self.composite_resource.files.first()
        # set the csv file to CSV file aggregation
        CSVLogicalFile.set_file_type(
            self.composite_resource, self.user, csv_res_file.id
        )
        self.assertEqual(CSVLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )

        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(CSVLogicalFile.objects.count(), 2)
        csv_logical_files = CSVLogicalFile.objects.all()
        self.assertEqual(csv_logical_files[0].metadata.tableSchema, csv_logical_files[1].metadata.tableSchema)
        # compare preview_data
        self.assertEqual(csv_logical_files[0].preview_data, csv_logical_files[1].preview_data)

    def test_version_resource_with_file_set_aggregation_1(self):
        """Here we are testing that we can create a new version of a composite resource that contains one
        file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = "fileset_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=new_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=new_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)

    def test_version_resource_with_file_set_aggregation_2(self):
        """Here we are testing that we can create a new version of a composite resource that contains one
        file set aggregation that contains another aggregation (NetCDF aggregation)"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        new_folder = "fileset_folder"
        ResourceFile.create_folder(self.composite_resource, new_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=new_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=new_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # add the nc file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.netcdf_file, upload_folder=new_folder
        )
        nc_res_file = ResourceFile.get(
            self.composite_resource, file=self.netcdf_file_name, folder=new_folder
        )
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, file_id=nc_res_file.id
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        # there should be 3 files - 2 files that we uploaded and one text file generated for netcdf
        # aggregation
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_version_resource_with_file_set_aggregation_3(self):
        """Here we are testing that we can create a new version of a composite resource that contains one
        nested file set aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        parent_fs_folder = "parent_fs_folder"
        ResourceFile.create_folder(self.composite_resource, parent_fs_folder)
        # add the txt file to the resource at the above folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=parent_fs_folder
        )
        # set folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=parent_fs_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        child_fs_folder = "{}/child_fs_folder".format(parent_fs_folder)
        ResourceFile.create_folder(self.composite_resource, child_fs_folder)
        # add the txt file to the resource at the above child folder
        self.add_file_to_resource(
            file_to_add=self.generic_file, upload_folder=child_fs_folder
        )
        # set the child folder to fileset logical file type (aggregation)
        FileSetLogicalFile.set_file_type(
            self.composite_resource, self.user, folder_path=child_fs_folder
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 2)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(FileSetLogicalFile.objects.count(), 4)

    def test_version_resource_with_netcdf_aggregation(self):
        """Here were testing that we can create a new version of a composite resource that contains a
        netcdf aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a nc file to the resource
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        nc_res_file = self.composite_resource.files.first()
        # set the nc file to netcdf aggregation
        NetCDFLogicalFile.set_file_type(
            self.composite_resource, self.user, nc_res_file.id
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(NetCDFLogicalFile.objects.count(), 2)

    def test_version_resource_with_timeseries_aggregation(self):
        """Here were testing that we can create a new version of a composite resource that contains a
        timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a sqlite file to the resource
        self.add_file_to_resource(file_to_add=self.sqlite_file)
        sql_res_file = self.composite_resource.files.first()
        # set the sqlite file to timeseries aggregation
        TimeSeriesLogicalFile.set_file_type(
            self.composite_resource, self.user, sql_res_file.id
        )
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(TimeSeriesLogicalFile.objects.count(), 2)

    def test_version_resource_with_reftimeseries_aggregation(self):
        """Here were testing that we can create a new version of a composite resource that contains a
        ref timeseries aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a json file to the resource
        self.add_file_to_resource(file_to_add=self.json_file)
        json_res_file = self.composite_resource.files.first()
        # set the json file to ref timeseries aggregation
        RefTimeseriesLogicalFile.set_file_type(
            self.composite_resource, self.user, json_res_file.id
        )
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.count(), 2)

    def test_version_resource_with_raster_aggregation(self):
        """Here were testing that we can create a new version of a composite resource that contains a
        raster aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a tif file to the resource
        self.add_file_to_resource(file_to_add=self.raster_file)
        tif_res_file = self.composite_resource.files.first()
        # set the tif file to raster aggregation
        GeoRasterLogicalFile.set_file_type(
            self.composite_resource, self.user, tif_res_file.id
        )
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 2)
        self.assertEqual(GeoRasterLogicalFile.objects.count(), 2)

    def test_version_resource_with_feature_aggregation(self):
        """Here were testing that we can create a new version of a composite resource that contains a
        geo feature aggregation"""

        self.create_composite_resource()
        self.assertEqual(CompositeResource.objects.count(), 1)
        # add a shp file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shp_file)
        shp_res_file = self.composite_resource.files.first()
        # add a shx file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_shx_file)
        # add a dbf file to the resource
        self.add_file_to_resource(file_to_add=self.watershed_dbf_file)

        # set the shp file to geofeature aggregation
        GeoFeatureLogicalFile.set_file_type(
            self.composite_resource, self.user, shp_res_file.id
        )
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 1)
        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        self.assertEqual(CompositeResource.objects.count(), 2)
        self.assertEqual(
            self.composite_resource.metadata.title.value,
            new_composite_resource.metadata.title.value,
        )
        self.assertEqual(
            self.composite_resource.files.count(), new_composite_resource.files.count()
        )
        self.assertEqual(new_composite_resource.files.count(), 3)
        self.assertEqual(GeoFeatureLogicalFile.objects.count(), 2)

    def test_version_resource_immunity_unpublished(self):
        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        # create a new version of the composite resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        # the replaced resource should be immutable
        obsoleted_res = hydroshare.utils.get_resource_by_shortkey(
            self.composite_resource.short_id
        )
        self.assertTrue(obsoleted_res.raccess.immutable)

        # after deleting the new versioned resource, the original resource should be editable again
        hydroshare.resource.delete_resource(new_composite_resource.short_id)
        ori_res = hydroshare.utils.get_resource_by_shortkey(
            self.composite_resource.short_id
        )
        self.assertFalse(ori_res.raccess.immutable)

    def test_version_resource_published_deleted_user(self):
        """Here we are testing versioning a published resource
        when a creator's user account has been deleted.
        """
        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        # add another creator
        metadata = self.composite_resource.metadata
        author_account = hydroshare.create_account(
            "author@nowhere.com",
            username="author",
            password='mypassword1',
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[self.group],
        )
        creator = metadata.create_element("creator",
                                          name=f"{author_account.last_name}, {author_account.first_name}",
                                          email=author_account.email,
                                          hydroshare_user_id=author_account.id)

        # make the original resource published before versioning
        self.composite_resource.raccess.immutable = True
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()

        # Delete the creator's user account
        author_account.delete()

        # Version the resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        # there should be 2 creators now
        self.assertEqual(new_composite_resource.metadata.creators.count(), 2)

        creator_to_check = new_composite_resource.metadata.creators.all().filter(email=author_account.email).first()
        self.assertNotEqual(creator_to_check, None)
        self.assertEqual(creator_to_check.name, creator.name)
        self.assertEqual(creator_to_check.email, creator.email)
        self.assertIsNone(creator_to_check.hydroshare_user_id)
        self.assertFalse(creator_to_check.is_active_user)

    def test_version_resource_unpublished_deleted_user(self):
        """Here we are testing versioning an unpublished resource
        when a creator's user account has been deleted.
        """
        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        # add another creator
        metadata = self.composite_resource.metadata
        author_account = hydroshare.create_account(
            "author@nowhere.com",
            username="author",
            password='mypassword1',
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[self.group],
        )
        creator = metadata.create_element("creator",
                                          name=f"{author_account.last_name}, {author_account.first_name}",
                                          email=author_account.email,
                                          hydroshare_user_id=author_account.id)

        # Delete the creator's user account
        author_account.delete()

        # Version the resource
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        # there should be 2 creators now
        self.assertEqual(new_composite_resource.metadata.creators.count(), 2)

        creator_to_check = new_composite_resource.metadata.creators.all().filter(email=author_account.email).first()
        self.assertNotEqual(creator_to_check, None)
        self.assertEqual(creator_to_check.name, creator.name)
        self.assertEqual(creator_to_check.email, creator.email)
        self.assertIsNone(creator_to_check.hydroshare_user_id)
        self.assertFalse(creator_to_check.is_active_user)

    def test_version_resource_immunity_published(self):
        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        # make the original resource published before versioning
        self.composite_resource.raccess.immutable = True
        self.composite_resource.raccess.published = True
        self.composite_resource.raccess.save()
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        new_composite_resource = hydroshare.create_new_version_resource(
            self.composite_resource, new_composite_resource, self.user
        )
        # after deleting the new versioned resource, the original resource should stay immutable
        hydroshare.resource.delete_resource(new_composite_resource.short_id)
        ori_res = hydroshare.utils.get_resource_by_shortkey(
            self.composite_resource.short_id
        )
        self.assertTrue(ori_res.raccess.immutable)

    def test_version_resource_lock(self):
        self.create_composite_resource()
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)

        # make the original resource locked before versioning
        self.composite_resource.locked_time = datetime.datetime.now(tz.UTC)
        self.composite_resource.save()
        new_composite_resource = hydroshare.create_empty_resource(
            self.composite_resource.short_id, self.user
        )
        with self.assertRaises(ResourceVersioningException):
            hydroshare.create_new_version_resource(
                self.composite_resource, new_composite_resource, self.user
            )

    def test_unzip(self):
        """Test that when a zip file gets unzipped at data/contents/ where a single file aggregation
        exists, the single file aggregation related xml files do not get added to the resource as
        resource files"""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        # set the generic file to generic single file aggregation
        GenericLogicalFile.set_file_type(
            self.composite_resource, self.user, gen_res_file.id
        )
        self.assertEqual(self.composite_resource.files.count(), 1)
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join("data", "contents", zip_res_file.file_name)
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
        )

        # resource should have 3 files now
        self.assertEqual(self.composite_resource.files.count(), 3)
        for res_file in self.composite_resource.files.all():
            # there should not be any resource files ending with _meta.xml or _resmap.xml
            self.assertFalse(res_file.file_name.endswith(AggregationMetaFilePath.METADATA_FILE_ENDSWITH))
            self.assertFalse(res_file.file_name.endswith(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH))
            # check file level system metadata
            self.assertGreater(res_file._size, 0)
            self.assertGreater(len(res_file._checksum), 0)
            self.assertNotEqual(res_file._modified_time, None)

    def test_unzip_rename(self):
        """Test that when a zip file gets unzipped at data/contents/ and the unzipped folder may be
        renamed without error (testing bug fix renaming a folder where a file exists that starts
        with the same name."""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 1 file now
        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join("data", "contents", zip_res_file.file_name)
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
        )

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        renamed_folder = os.path.join("data", "contents", "renamed")
        try:
            move_or_rename_file_or_folder(
                self.user,
                self.composite_resource.short_id,
                zip_file_rel_path,
                renamed_folder,
            )
        except:  # noqa
            self.fail("Exception thrown while renaming a folder.")

    def test_unzip_folder_clash(self):
        """Test that when a zip file gets unzipped here or to a folder and a folder with the same
        name already exists, the existing folder is not overwritten"""

        self.create_composite_resource()
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)
        # resource should have 1 file now
        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file here in the current folder which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join("data", "contents", zip_res_file.file_name)
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
        )

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        # unzip again should raise FileOverrideException
        with self.assertRaises(FileOverrideException):
            unzip_file(
                self.user,
                self.composite_resource.short_id,
                zip_file_rel_path,
                bool_remove_original=False,
            )

        # ensure files aren't overwriting name clash
        self.assertEqual(self.composite_resource.files.count(), 2)

        # unzip the above zip file again to the sub folder this time which should add a new folder to the resource
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            unzip_to_folder=True,
        )

        # resource should have 3 files now
        self.assertEqual(self.composite_resource.files.count(), 3)

        # unzip again should not override previously unzipped file in the sub folder
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            unzip_to_folder=True,
        )
        # ensure files aren't overwritten but instead a new file is created in a different sub folder
        self.assertEqual(self.composite_resource.files.count(), 4)

    def test_unzip_folder_clash_overwrite(self):
        """Test that when a zip file gets unzipped a folder with the same
        name already exists and overwrite is True, the existing folder is overwritten"""

        self.create_composite_resource()
        # add a zip file that contains only one file
        self.add_file_to_resource(file_to_add=self.zip_file)

        self.assertEqual(self.composite_resource.files.count(), 1)
        # unzip the above zip file  which should add one more file to the resource
        zip_res_file = ResourceFile.get(self.composite_resource, self.zip_file_name)
        zip_file_rel_path = os.path.join("data", "contents", zip_res_file.file_name)
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            overwrite=True,
        )

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)

        # unzip again
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            overwrite=True,
        )

        # ensure files are overwriting
        self.assertEqual(self.composite_resource.files.count(), 2)

    def test_unzip_aggregation(self):
        """Test that when a zip file gets unzipped at data/contents/ where the contents includes a
        single file aggregation.  Testing the aggregation is recognized on unzip"""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zipped_aggregation_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 0)
        # unzip the above zip file  which should add one more file to the resource
        zip_file_rel_path = os.path.join(
            "data", "contents", self.zipped_aggregation_file_name
        )
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
        )

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be a referenced time series now
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)

    def test_unzip_aggregation_overwrite(self):
        """Test that when a zip file gets unzipped at data/contents/ where the contents includes a
        single file aggregation.  Testing aggregation is overwritten when overwrite is True"""

        self.create_composite_resource()

        self.add_file_to_resource(file_to_add=self.zipped_aggregation_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 0)
        # unzip the above zip file  which should add one more file to the resource
        zip_file_rel_path = os.path.join(
            "data", "contents", self.zipped_aggregation_file_name
        )
        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            overwrite=True,
        )

        # resource should have 2 files now
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should be a referenced time series now
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)
        ref_time = RefTimeseriesLogicalFile.objects.first()
        ref_time.metadata.abstract = "overwritten"
        ref_time.metadata.save()

        self.assertEqual(
            RefTimeseriesLogicalFile.objects.first().metadata.abstract, "overwritten"
        )

        unzip_file(
            self.user,
            self.composite_resource.short_id,
            zip_file_rel_path,
            bool_remove_original=False,
            overwrite=True,
        )

        # resource should still have 2 files
        self.assertEqual(self.composite_resource.files.count(), 2)
        # there should still be a referenced time series
        self.assertEqual(RefTimeseriesLogicalFile.objects.all().count(), 1)

        # check the file exists on disk after being overwritten
        for file in self.composite_resource.files.all():
            self.assertTrue(file.exists)

        self.assertNotEqual(
            RefTimeseriesLogicalFile.objects.first().metadata.abstract, "overwritten"
        )

    def test_zip_by_aggregation_file_1(self):
        """Test that we can zip a netcdf aggregation that exists at the root of resource path in S3
        The aggregation zip file becomes a resource file
        """

        self.create_composite_resource()
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        # create a netcdf aggregation - which we will test for zipping
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        nc_res_file = self.composite_resource.files.first()
        NetCDFLogicalFile.set_file_type(
            resource=self.composite_resource, file_id=nc_res_file.id, user=self.user
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.count(), 2)
        nc_aggr = NetCDFLogicalFile.objects.first()
        zip_by_aggregation_file(
            user=self.user,
            res_id=self.composite_resource.short_id,
            aggregation_name=nc_aggr.aggregation_name,
            output_zip_fname="nc_aggr",
        )
        # new zip file should be be part of the resource
        self.assertEqual(self.composite_resource.files.count(), 3)
        zip_res_file = ResourceFile.get(
            resource=self.composite_resource, file="nc_aggr.zip"
        )
        self.assertTrue(zip_res_file.exists)
        self._test_zip_file_contents(zipfile=zip_res_file, aggregation=nc_aggr)

    def test_zip_by_aggregation_file_2(self):
        """Test that we can zip a netcdf aggregation that exists in a folder.
        The aggregation zip file becomes a resource file.
        """
        self.create_composite_resource()
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        folder = "test-folder"
        ResourceFile.create_folder(resource=self.composite_resource, folder=folder)
        # create a netcdf aggregation inside a folder- which we will test for zipping
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=folder)
        self.assertEqual(self.composite_resource.files.count(), 1)
        nc_res_file = self.composite_resource.files.first()
        NetCDFLogicalFile.set_file_type(
            resource=self.composite_resource, file_id=nc_res_file.id, user=self.user
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.count(), 2)
        nc_aggr = NetCDFLogicalFile.objects.first()
        zip_by_aggregation_file(
            user=self.user,
            res_id=self.composite_resource.short_id,
            aggregation_name=nc_aggr.aggregation_name,
            output_zip_fname="nc_aggr.zip",
        )
        self.assertEqual(nc_aggr.aggregation_name, f"{folder}/{self.netcdf_file_name}")
        # new zip file should be be part of the resource
        self.assertEqual(self.composite_resource.files.count(), 3)
        zip_res_file = ResourceFile.get(
            resource=self.composite_resource, file="nc_aggr.zip", folder=folder
        )
        self.assertTrue(zip_res_file.exists)
        self._test_zip_file_contents(zipfile=zip_res_file, aggregation=nc_aggr)

    def test_zip_by_aggregation_file_3(self):
        """Test that we can zip a netcdf aggregation that exists in a fileset folder.
        The aggregation zip file becomes a resource file and part of the fileset aggregation.
        """
        self.create_composite_resource()
        self.assertEqual(NetCDFLogicalFile.objects.count(), 0)
        self.assertEqual(FileSetLogicalFile.objects.count(), 0)
        folder = "fs-folder"
        ResourceFile.create_folder(resource=self.composite_resource, folder=folder)
        # create a netcdf aggregation inside a folder- which we will test for zipping
        self.add_file_to_resource(file_to_add=self.netcdf_file, upload_folder=folder)
        self.assertEqual(self.composite_resource.files.count(), 1)
        nc_res_file = self.composite_resource.files.first()
        NetCDFLogicalFile.set_file_type(
            resource=self.composite_resource, file_id=nc_res_file.id, user=self.user
        )
        self.assertEqual(NetCDFLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.count(), 2)
        # set the folder to fileset aggregation
        FileSetLogicalFile.set_file_type(
            resource=self.composite_resource, folder_path=folder, user=self.user
        )
        self.assertEqual(FileSetLogicalFile.objects.count(), 1)
        fs_aggr = FileSetLogicalFile.objects.first()
        self.assertEqual(fs_aggr.files.count(), 0)
        nc_aggr = NetCDFLogicalFile.objects.first()
        zip_file_name = "nc_aggr"
        zip_by_aggregation_file(
            user=self.user,
            res_id=self.composite_resource.short_id,
            aggregation_name=nc_aggr.aggregation_name,
            output_zip_fname=zip_file_name,
        )
        # new zip file should be be part of the resource
        self.assertEqual(self.composite_resource.files.count(), 3)
        zip_res_file = ResourceFile.get(
            resource=self.composite_resource, file=f"{zip_file_name}.zip", folder=folder
        )
        self.assertTrue(zip_res_file.exists)
        self.assertEqual(fs_aggr.files.count(), 1)
        # new zip file should be part of the fileset aggregation
        self.assertEqual(zip_res_file.logical_file_type_name, "FileSetLogicalFile")
        self._test_zip_file_contents(zipfile=zip_res_file, aggregation=nc_aggr)

    def test_zip_by_aggregation_file_4(self):
        """Test that we can zip a single file aggregation that exists at the root of resource path in S3
        The aggregation zip file becomes a resource file
        """

        self.create_composite_resource()
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        # create a single file aggregation - which we will test for zipping
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_res_file = self.composite_resource.files.first()
        GenericLogicalFile.set_file_type(
            resource=self.composite_resource, file_id=gen_res_file.id, user=self.user
        )
        self.assertEqual(GenericLogicalFile.objects.count(), 1)
        self.assertEqual(self.composite_resource.files.count(), 1)
        gen_aggr = GenericLogicalFile.objects.first()
        zip_by_aggregation_file(
            user=self.user,
            res_id=self.composite_resource.short_id,
            aggregation_name=gen_aggr.aggregation_name,
            output_zip_fname="gen_aggr",
        )
        # new zip file should be be part of the resource
        self.assertEqual(self.composite_resource.files.count(), 2)
        zip_res_file = ResourceFile.get(
            resource=self.composite_resource, file="gen_aggr.zip"
        )
        self.assertTrue(zip_res_file.exists)
        self._test_zip_file_contents(zipfile=zip_res_file, aggregation=gen_aggr)

    def _test_zip_file_contents(self, zipfile, aggregation):
        temp_zip_file = get_file_from_s3(
            resource=self.composite_resource, file_path=zipfile.storage_path
        )
        aggr_files = [f.file_name for f in aggregation.files.all()]
        aggr_files.append(os.path.basename(aggregation.map_file_path))
        aggr_files.append(os.path.basename(aggregation.metadata_file_path))
        with ZipFile(temp_zip_file) as zipfile:
            files = zipfile.namelist()
            self.assertEqual(len(files), len(aggr_files))
            for f in files:
                # strip out the additional folder path in the zip file
                f = os.path.basename(f)
                self.assertIn(f, aggr_files)
            shutil.rmtree(os.path.dirname(temp_zip_file))

    def test_composite_resource_my_resources_none(self):
        # test that only a fixed number of db queries (based on the number of resources) are
        # generated for "my_resources" page - this test is with no resource.

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.client.login(username='user1', password='mypassword1')
        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)

        # there should be no resources at this point
        number_of_resources = BaseResource.objects.count()
        self.assertEqual(number_of_resources, 0)
        expected_query_count = self._get_expected_query_count(number_of_resources)
        with self.assertNumQueries(expected_query_count):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

        self.composite_resource = None

    def test_composite_resource_my_resources_one(self):
        # test that only a fixed number of db queries (based on the number of resources) are
        # generated for "my_resources" page - this test is with one resource.

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.client.login(username='user1', password='mypassword1')
        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)

        # create 1 composite resource
        self.create_composite_resource()
        # there should be one resource at this point
        number_of_resources = BaseResource.objects.count()
        self.assertEqual(number_of_resources, 1)
        expected_query_count = self._get_expected_query_count(number_of_resources)
        with self.assertNumQueries(expected_query_count):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

    def test_composite_resource_my_resources_two(self):
        # test that only a fixed number of db queries (based on the number of resources) are
        # generated for "my_resources" page - this test is with two resources.

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.client.login(username='user1', password='mypassword1')
        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)

        # create 2 composite resources
        for _ in range(2):
            self.create_composite_resource()

        # there should be 2 resources at this point
        number_of_resources = BaseResource.objects.count()
        self.assertEqual(number_of_resources, 2)
        expected_query_count = self._get_expected_query_count(number_of_resources)
        with self.assertNumQueries(expected_query_count):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

    def test_composite_resource_my_resources_three(self):
        # test that only a fixed number of db queries (based on the number of resources) are
        # generated for "my_resources" page - this test is with three resources.

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        self.client.login(username='user1', password='mypassword1')
        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)

        # create 3 composite resources
        for _ in range(3):
            self.create_composite_resource()

        # there should be 3 resources at this point
        number_of_resources = BaseResource.objects.count()
        self.assertEqual(number_of_resources, 3)
        expected_query_count = self._get_expected_query_count(number_of_resources)
        with self.assertNumQueries(expected_query_count):
            response = self.client.get(reverse("my_resources"), follow=True)
            self.assertTrue(response.status_code == 200)

    def test_composite_resource_landing_scales(self):
        # test that db queries for landing page have constant time complexity

        # expected number of queries for landing page when the resource has no resource file
        _LANDING_PAGE_NO_RES_FILE_QUERY_COUNT = 179

        # expected number of queries for landing page when the resource has resource file
        _LANDING_PAGE_WITH_RES_FILE_QUERY_COUNT = _LANDING_PAGE_NO_RES_FILE_QUERY_COUNT + 16

        # user 1 login
        self.client.login(username='user1', password='mypassword1')
        # navigating to home page for initializing db queries
        response = self.client.get(reverse("home"), follow=True)
        self.assertTrue(response.status_code == 200)

        # there should not be any resource at this point
        self.assertEqual(BaseResource.objects.count(), 0)

        # create a composite resource
        self.create_composite_resource()
        # there should be one resource at this point
        self.assertEqual(BaseResource.objects.count(), 1)
        self.assertEqual(self.composite_resource.resource_type, "CompositeResource")

        with self.assertNumQueries(_LANDING_PAGE_NO_RES_FILE_QUERY_COUNT):
            response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
            self.assertTrue(response.status_code == 200)

        # create another resource
        self.create_composite_resource()
        # there should be two resources at this point
        self.assertEqual(BaseResource.objects.count(), 2)

        with self.assertNumQueries(_LANDING_PAGE_NO_RES_FILE_QUERY_COUNT):
            response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
            self.assertTrue(response.status_code == 200)

        # test resource landing page with resource files
        # add a file to the resource
        self.add_file_to_resource(file_to_add=self.generic_file)
        self.assertEqual(self.composite_resource.files.count(), 1)

        with self.assertNumQueries(_LANDING_PAGE_WITH_RES_FILE_QUERY_COUNT):
            response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
            self.assertTrue(response.status_code == 200)

        # add 3 more files to the resource
        self.add_file_to_resource(file_to_add=self.netcdf_file)
        self.add_file_to_resource(file_to_add=self.watershed_shp_file)
        self.add_file_to_resource(file_to_add=self.watershed_dbf_file)
        self.assertEqual(self.composite_resource.files.count(), 4)

        with self.assertNumQueries(_LANDING_PAGE_WITH_RES_FILE_QUERY_COUNT):
            response = self.client.get(f'/resource/{self.composite_resource.short_id}', follow=True)
            self.assertTrue(response.status_code == 200)

        # accessing the readme file should only be 3 db query
        with self.assertNumQueries(3):
            _ = self.composite_resource.readme_file

    def _get_expected_query_count(self, number_of_resources):
        # this is the expected number of queries for "my_resources" page with no resources
        base_query_count = 17

        # this is additional number of queries per resource
        # 9 are mezzanine queries (can't do much about it)
        # 3 queries are our code in template
        per_resource_query_count = 12

        # these are additional queries generated by get_my_resources_list() function
        if number_of_resources > 0:
            pre_template_query_count = 4 + number_of_resources
        else:
            pre_template_query_count = 0

        expected_query_count = base_query_count + pre_template_query_count
        expected_query_count += per_resource_query_count * number_of_resources
        return expected_query_count
