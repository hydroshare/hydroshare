import os
import json
import tempfile

from django.core.urlresolvers import reverse
from hsmodels.schemas.resource import ResourceMetadataIn
from hsmodels.schemas.aggregations import GeographicFeatureMetadataIn, GeographicRasterMetadataIn, \
    MultidimensionalMetadataIn, SingleFileMetadataIn, FileSetMetadataIn, TimeSeriesMetadataIn, \
    ReferencedTimeSeriesMetadataIn, ModelProgramMetadataIn, ModelInstanceMetadataIn
from rest_framework import status

from hs_core.hydroshare import resource, current_site_url
from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_core.tests.api.utils import prepare_resource as prepare_resource_util


def normalize_metadata(metadata_str, short_id):
    """Prepares metadata string to match resource id and hydroshare url of original"""
    return metadata_str \
        .replace("http://www.hydroshare.org", current_site_url()) \
        .replace("0fdbb27857844644bacc274882601598", short_id)


def sorting(item):
    if isinstance(item, dict):
        return sorted((key, sorting(values)) for key, values in item.items())
    if isinstance(item, list):
        return sorted(sorting(x) for x in item)
    else:
        return item


def prepare_resource(self, folder):
    prepare_resource_util(folder, self.res, self.user, self.extracted_directory, self.test_bag_path)


class TestFileBasedJSON(HSRESTTestCase):

    base_dir = 'hs_rest_api2/tests/data/json/'

    def __init__(self, methodName, param1=None, param2=None):
        super(TestFileBasedJSON, self).__init__(methodName)

        self.param1 = param1
        self.param2 = param2

    def setUp(self):
        super(TestFileBasedJSON, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()

        # create empty resource
        self.res = resource.create_resource(
            'CompositeResource',
            self.user,
            'triceratops'
            )

        self.test_bag_path = 'hs_rest_api2/tests/data/test_resource_metadata_files.zip'

        self.extracted_directory = 'hs_core/tests/data/test_resource_metadata_files/'

    def tearDown(self):
        super(TestFileBasedJSON, self).tearDown()
        os.remove(self.test_bag_path)
        self.res.delete()

    def _test_metadata_update_retrieve(self, endpoint, schema_in, json_put_file, aggregation_path=None):
        kwargs = {"pk": self.res.short_id}
        if aggregation_path:
            kwargs["aggregation_path"] = aggregation_path
        response = self.client.get(reverse(endpoint, kwargs=kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with open(os.path.join(self.base_dir, json_put_file), "r") as f:
            full_resource_json = json.loads(normalize_metadata(f.read(), self.res.short_id))
        schema_in_instance = schema_in(**full_resource_json)
        in_json = schema_in_instance.dict(exclude_defaults=True)
        self.client.put(reverse(endpoint, kwargs=kwargs),
                        data=in_json, format="json")

        response = self.client.get(reverse(endpoint, kwargs=kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())

        if aggregation_path:
            # TODO remove rights from aggregation in schema
            full_resource_json['rights'] = response_json['rights']
        else:
            self.assertGreater(response_json['modified'], full_resource_json['modified'])
            # overwrite system metadata fields for comparison
            full_resource_json['modified'] = response_json['modified']
            full_resource_json['created'] = response_json['created']
            full_resource_json['creators'][0]['description'] = response_json['creators'][0]['description']
        self.assertEqual(sorting(response_json), sorting(full_resource_json))

    def test_resource_metadata_update_retrieve(self):
        prepare_resource(self, "resource")
        self._test_metadata_update_retrieve("hsapi2:resource_metadata_json", ResourceMetadataIn, "resource.json")

    def test_reference_timerseries_metadata_update_retrieve(self):
        prepare_resource(self, "reference_timeseries")
        self._test_metadata_update_retrieve("hsapi2:referenced_time_series_metadata_json",
                                            ReferencedTimeSeriesMetadataIn, "referencedtimeseries.refts.json",
                                            "msf_version.refts.json")

    def test_netcdf_metadata_update_retrieve(self):
        prepare_resource(self, "netcdf")
        self._test_metadata_update_retrieve("hsapi2:multidimensional_metadata_json", MultidimensionalMetadataIn,
                                            "multidimensional.json", "SWE_time.nc")

    def test_file_set_metadata_update_retrieve(self):
        prepare_resource(self, "file_set")
        self._test_metadata_update_retrieve("hsapi2:file_set_metadata_json", FileSetMetadataIn, "fileset.json",
                                            "asdf/testing.xml")

    def test_timerseries_metadata_update_retrieve(self):
        prepare_resource(self, "timeseries")
        self._test_metadata_update_retrieve("hsapi2:time_series_metadata_json", TimeSeriesMetadataIn,
                                            "timeseries.json", "ODM2_Multi_Site_One_Variable.sqlite")

    def test_geographic_raster_metadata_update_retrieve(self):
        prepare_resource(self, "geographic_raster")
        self._test_metadata_update_retrieve("hsapi2:geographic_raster_metadata_json", GeographicRasterMetadataIn,
                                            "geographicraster.json", "logan.vrt")

    def test_geographic_feature_metadata_update_retrieve(self):
        prepare_resource(self, "geographic_feature")
        self._test_metadata_update_retrieve("hsapi2:geographic_feature_metadata_json", GeographicFeatureMetadataIn,
                                            "geographicfeature.json", "watersheds.shp")

    def test_single_file_metadata_update_retrieve(self):
        prepare_resource(self, "single_file")
        self._test_metadata_update_retrieve("hsapi2:single_file_metadata_json", SingleFileMetadataIn,
                                            "singlefile.json", "test.xml")

    def test_model_program_metadata_update_retrieve(self):
        prepare_resource(self, "model_program")
        self._test_metadata_update_retrieve("hsapi2:model_program_metadata_json", ModelProgramMetadataIn,
                                            "modelprogram.json", "setup.cfg")

    def test_model_instance_metadata_update_retrieve(self):
        prepare_resource(self, "model_program")
        prepare_resource(self, "model_instance")
        self._test_metadata_update_retrieve("hsapi2:model_instance_metadata_json", ModelInstanceMetadataIn,
                                            "modelinstance.json", "generic_file.txt")

    def _test_metadata_update_unknown_field(self, endpoint, aggregation_path=None):
        kwargs = {"pk": self.res.short_id}
        if aggregation_path:
            kwargs["aggregation_path"] = aggregation_path
        response = self.client.get(reverse(endpoint, kwargs=kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        in_resource_json = {'bad_title': 'this better not work!'}
        response = self.client.put(reverse(endpoint, kwargs=kwargs), data=in_resource_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resource_metadata_update_unknown_field(self):
        prepare_resource(self, "resource")
        self._test_metadata_update_unknown_field("hsapi2:resource_metadata_json")

    def test_reference_timerseries_metadata_update_unknown_field(self):
        prepare_resource(self, "reference_timeseries")
        self._test_metadata_update_unknown_field("hsapi2:referenced_time_series_metadata_json",
                                                 "msf_version.refts.json")

    def test_netcdf_metadata_update_unknown_field(self):
        prepare_resource(self, "netcdf")
        self._test_metadata_update_unknown_field("hsapi2:multidimensional_metadata_json", "SWE_time.nc")

    def test_file_set_metadata_update_unknown_field(self):
        prepare_resource(self, "file_set")
        self._test_metadata_update_unknown_field("hsapi2:file_set_metadata_json", "asdf/testing.xml")

    def test_timerseries_metadata_update_unknown_field(self):
        prepare_resource(self, "timeseries")
        self._test_metadata_update_unknown_field("hsapi2:time_series_metadata_json",
                                                 "ODM2_Multi_Site_One_Variable.sqlite")

    def test_geographic_raster_metadata_update_unknown_field(self):
        prepare_resource(self, "geographic_raster")
        self._test_metadata_update_unknown_field("hsapi2:geographic_raster_metadata_json", "logan.vrt")

    def test_geographic_feature_metadata_update_unknown_field(self):
        prepare_resource(self, "geographic_feature")
        self._test_metadata_update_unknown_field("hsapi2:geographic_feature_metadata_json", "watersheds.shp")

    def test_single_file_metadata_update_unknown_field(self):
        prepare_resource(self, "single_file")
        self._test_metadata_update_unknown_field("hsapi2:single_file_metadata_json", "test.xml")

    def test_model_program_metadata_update_unknown_field(self):
        prepare_resource(self, "model_program")
        self._test_metadata_update_unknown_field("hsapi2:model_program_metadata_json", "setup.cfg")

    def test_model_instance_metadata_update_unknown_field(self):
        prepare_resource(self, "model_program")
        prepare_resource(self, "model_instance")
        self._test_metadata_update_unknown_field("hsapi2:model_instance_metadata_json", "generic_file.txt")
