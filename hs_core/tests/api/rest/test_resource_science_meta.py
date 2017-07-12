from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.hydroshare.utils import resource_post_create_actions
from .base import HSRESTTestCase


class TestResourceScienceMetadata(HSRESTTestCase):

    def setUp(self):
        super(TestResourceScienceMetadata, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_get_scimeta(self):
        # Get the resource system metadata
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(res_id=self.pid)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # content = json.loads(response.content)

    def test_put_scimeta(self):
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(res_id=self.pid)
        put_data = {
            "title": "New Title",
            "description": "New Description",
            "subjects": [
                {"value": "subject1"},
                {"value": "subject2"},
                {"value": "subject3"}
            ],
            "contributors": [{
                "name": "Test Name 1",
                "organization": "Org 1"
            }, {
                "name": None,
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None
            }],
            "coverages": [{
                "type": "box",
                "value": {
                    "northlimit": 43.19716728247476,
                    "projection": "WGS 84 EPSG:4326",
                    "name": "A whole bunch of the atlantic ocean",
                    "units": "Decimal degrees",
                    "southlimit": 23.8858376999,
                    "eastlimit": -19.16015625,
                    "westlimit": -62.75390625
                }
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": "CCC",
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_put_scimeta_double_none(self):
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(res_id=self.pid)
        put_data = {
            "title": "New Title",
            "description": "New Description",
            "subjects": [
                {"value": "subject1"},
                {"value": "subject2"},
                {"value": "subject3"}
            ],
            "contributors": [{
                "name": "Test Name 1",
                "organization": "Org 1"
            }, {
                "name": None,
                "organization": "Org 2"
            }],
            "creators": [
                {
                    "name": "Creator",
                    "organization": None
                },
                {
                    "name": None,
                    "organization": None
                }
            ],
            "coverages": [{
                "type": "box",
                "value": {
                    "northlimit": 43.19716728247476,
                    "projection": "WGS 84 EPSG:4326",
                    "name": "A whole bunch of the atlantic ocean",
                    "units": "Decimal degrees",
                    "southlimit": 23.8858376999,
                    "eastlimit": -19.16015625,
                    "westlimit": -62.75390625
                }
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": "CCC",
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_scimeta_netcdf_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a netcdf resource
        netcdf_file = 'hs_core/tests/data/netcdf_valid.nc'
        file_to_upload = open(netcdf_file, "r")
        self._create_resource(resource_type="NetcdfResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "title": "New Title",
            "description": "New Description",
            "subjects": [
                {"value": "subject1"},
                {"value": "subject2"},
                {"value": "subject3"}
            ],
            "contributors": [{
                "name": "Test Name 1",
                "organization": "Org 1"
            }, {
                "name": "Test Name 2",
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None
            }],
            "coverages": [{
                "type": "box",
                "value": {
                    "northlimit": 43.19716728247476,
                    "projection": "WGS 84 EPSG:4326",
                    "name": "A whole bunch of the atlantic ocean",
                    "units": "Decimal degrees",
                    "southlimit": 23.8858376999,
                    "eastlimit": -19.16015625,
                    "westlimit": -62.75390625
                }
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": "CCC",
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "originalcoverage": {
                "value": {
                    "northlimit": '12', "projection": "transverse_mercator",
                    "units": "meter", "southlimit": '10',
                    "eastlimit": '23', "westlimit": '2'
                },
                "projection_string_text": '+proj=tmerc +lon_0=-111.0 +lat_0=0.0 +x_0=500000.0 '
                                          '+y_0=0.0 +k_0=0.9996',
                "projection_string_type": 'Proj4 String'
            },
            "variables": [
                {
                    "name": "SWE",
                    "type": "Float",
                    "shape": "y,x,time",
                    "unit": "m",
                    "missing_value": "-9999",
                    "descriptive_name": "Snow water equivalent",
                    "method": "model simulation of UEB"
                },
                {
                    "name": "x",
                    "unit": "Centimeter"
                }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_netcdf_resource_without_core_metadata(self):
        # testing bulk metadata update that only updates resource specific metadata

        # create a netcdf resource
        netcdf_file = 'hs_core/tests/data/netcdf_valid.nc'
        file_to_upload = open(netcdf_file, "r")
        self._create_resource(resource_type="NetcdfResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "originalcoverage": {
                "value": {
                    "northlimit": '12', "projection": "transverse_mercator",
                    "units": "meter", "southlimit": '10',
                    "eastlimit": '23', "westlimit": '2'
                },
                "projection_string_text": '+proj=tmerc +lon_0=-111.0 +lat_0=0.0 +x_0=500000.0 '
                                          '+y_0=0.0 +k_0=0.9996',
                "projection_string_type": 'Proj4 String'
            },
            "variables": [
                {
                    "name": "SWE",
                    "type": "Float",
                    "shape": "y,x,time",
                    "unit": "m",
                    "missing_value": "-9999",
                    "descriptive_name": "Snow water equivalent",
                    "method": "model simulation of UEB"
                },
                {
                    "name": "x",
                    "unit": "Centimeter"
                }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_raster_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update (Note: the only resource specific metadata element that can be updated
        # is BandInformation)

        # create a raster resource
        raster_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(raster_file, "r")
        self._create_resource(resource_type="RasterResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "title": "New Title",
            "description": "New Description",
            "subjects": [
                {"value": "subject1"},
                {"value": "subject2"},
                {"value": "subject3"}
            ],
            "contributors": [{
                "name": "Test Name 1",
                "organization": "Org 1"
            }, {
                "name": "Test Name 2",
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None
            }],
            "coverages": [{
                "type": "box",
                "value": {
                    "northlimit": 43.19716728247476,
                    "projection": "WGS 84 EPSG:4326",
                    "name": "A whole bunch of the atlantic ocean",
                    "units": "Decimal degrees",
                    "southlimit": 23.8858376999,
                    "eastlimit": -19.16015625,
                    "westlimit": -62.75390625
                }
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": "CCC",
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "bandinformations": [
                {'original_band_name': 'Band_1',
                 'name': 'Band_2',
                 'variableName': 'digital elevation',
                 'variableUnit': 'meter',
                 'method': 'this is method',
                 'comment': 'this is comment',
                 'maximumValue': 1000,
                 'minimumValue': 0,
                 'noDataValue': -9999
                 }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_raster_resource_without_core_metadata(self):
        # testing bulk metadata update that includes only resource specific
        # metadata update (Note: the only resource specific metadata element that can be updated
        # is BandInformation)

        # create a raster resource
        raster_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(raster_file, "r")
        self._create_resource(resource_type="RasterResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "bandinformations": [
                {'original_band_name': 'Band_1',
                 'name': 'Band_2',
                 'variableName': 'digital elevation',
                 'variableUnit': 'meter',
                 'method': 'this is method',
                 'comment': 'this is comment',
                 'maximumValue': 1000,
                 'minimumValue': 0,
                 'noDataValue': -9999
                 }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_modelprogram_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a model program resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="ModelProgramResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "title": "New Title",
            "description": "New Description",
            "subjects": [
                {"value": "subject1"},
                {"value": "subject2"},
                {"value": "subject3"}
            ],
            "contributors": [{
                "name": "Test Name 1",
                "organization": "Org 1"
            }, {
                "name": "Test Name 2",
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None
            }],
            "coverages": [{
                "type": "box",
                "value": {
                    "northlimit": 43.19716728247476,
                    "projection": "WGS 84 EPSG:4326",
                    "name": "A whole bunch of the atlantic ocean",
                    "units": "Decimal degrees",
                    "southlimit": 23.8858376999,
                    "eastlimit": -19.16015625,
                    "westlimit": -62.75390625
                }
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": "CCC",
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "mpmetadata": {
                 "modelVersion": "5.1.011",
                 "modelProgramLanguage": "Fortran",
                 "modelOperatingSystem": "Windows",
                 "modelReleaseDate": "2016-10-24T21:05:00.315907+00:00",
                 "modelWebsite": "http://www.hydroshare.org",
                 "modelCodeRepository": "http://www.github.com",
                 "modelReleaseNotes": "releaseNote.pdf",
                 "modelDocumentation": "manual.pdf",
                 "modelSoftware": "utilities.exe",
                 "modelEngine": "sourceCode.zip"
                 }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_modelprogram_resource_without_core_metadata(self):
        # testing bulk metadata update that only updates resource specific
        # metadata

        # create a model program resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="ModelProgramResource", file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "mpmetadata": {
                 "modelVersion": "5.1.011",
                 "modelProgramLanguage": "Fortran",
                 "modelOperatingSystem": "Windows",
                 "modelReleaseDate": "2016-10-24T21:05:00.315907+00:00",
                 "modelWebsite": "http://www.hydroshare.org",
                 "modelCodeRepository": "http://www.github.com",
                 "modelReleaseNotes": "releaseNote.pdf",
                 "modelDocumentation": "manual.pdf",
                 "modelSoftware": "utilities.exe",
                 "modelEngine": "sourceCode.zip"
                 }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def _create_resource(self, resource_type, file_to_upload):
        self.resource = resource.create_resource(
            resource_type=resource_type,
            owner=self.user,
            title="Testing bulk metadata update for resource type - {}".format(resource_type),
            files=(file_to_upload,)
            )
        resource_post_create_actions(resource=self.resource, user=self.user,
                                     metadata=self.resource.metadata)
