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
        self.resource = res
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # create another resource for testing relation metadata
        another_res = resource.create_resource('GenericResource',
                                               self.user,
                                               'My another Test resource')
        self.pid2 = another_res.short_id
        self.resources_to_delete.append(self.pid2)

    def test_get_scimeta(self):
        # Get the resource system metadata
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(res_id=self.pid)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # content = json.loads(response.content)

    def test_put_scimeta_generic_resource(self):
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
                "organization": "Org 1",
                "identifiers": {"ORCID": "https://orcid.org/012",
                                "ResearchGateID": "https://www.researchgate.net/002"}
            }, {
                "name": None,
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator 1",
                "organization": None
            }, {
                    "name": "Creator 2",
                    "organization": "USU",
                    "identifiers": {"ORCID": "https://orcid.org/011",
                                    "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "relations": [
                {
                    "type": "isCopiedFrom",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                },
                {
                    "type": "isExecutedBy",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                }
            ],
            "funding_agencies": [
                 {
                     "agency_name": "NSF",
                     "award_title": "Cyber Infrastructure",
                     "award_number": "NSF-101-20-6789",
                     "agency_url": "https://www.nsf.gov",
                 },
                 {
                     "agency_name": "NSF2",
                     "award_title": "Cyber Infrastructure2",
                     "award_number": "NSF-123",
                     "agency_url": "https://www.google.com",
                 }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(self.resource.metadata.dates.all().count(), 3)
        self.assertEqual(self.resource.metadata.sources.all().count(), 2)
        self.assertEqual(self.resource.metadata.relations.all().count(), 2)
        self.assertEqual(self.resource.metadata.funding_agencies.all().count(), 2)
        self.assertEqual(str(self.resource.metadata.rights), "CCC http://www.hydroshare.org")
        self.assertEqual(str(self.resource.metadata.language), "fre")
        self.assertEqual(self.resource.metadata.coverages.all().count(), 1)
        self.assertEqual(self.resource.metadata.creators.all().count(), 2)
        self.assertEqual(self.resource.metadata.contributors.all().count(), 2)
        self.assertEqual(self.resource.metadata.subjects.all().count(), 3)
        self.assertEqual(str(self.resource.metadata.description), "New Description")
        self.assertEqual(str(self.resource.metadata.title), "New Title")

    def test_put_scimeta_generic_resource_double_none(self):
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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

    def test_put_scimeta_composite_resource_with_core_metadata(self):
        # testing bulk metadata update that includes only core metadata

        # create a composite resource
        self._create_resource(resource_type="CompositeResource")
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
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "relations": [
                {
                    "type": "isCopiedFrom",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                },
                {
                    "type": "isExecutedBy",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                }
            ],
            "funding_agencies": [
                 {
                     "agency_name": "NSF",
                     "award_title": "Cyber Infrastructure",
                     "award_number": "NSF-101-20-6789",
                     "agency_url": "https://www.nsf.gov",
                 },
                 {
                     "agency_name": "NSF2",
                     "award_title": "Cyber Infrastructure2",
                     "award_number": "NSF-123",
                     "agency_url": "https://www.google.com",
                 }
            ]
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(self.resource.metadata.dates.all().count(), 3)
        self.assertEqual(self.resource.metadata.sources.all().count(), 2)
        self.assertEqual(self.resource.metadata.relations.all().count(), 2)
        self.assertEqual(self.resource.metadata.funding_agencies.all().count(), 2)
        self.assertEqual(str(self.resource.metadata.rights), "CCC http://www.hydroshare.org")
        self.assertEqual(str(self.resource.metadata.language), "fre")
        self.assertEqual(self.resource.metadata.creators.all().count(), 1)
        self.assertEqual(self.resource.metadata.contributors.all().count(), 2)
        self.assertEqual(self.resource.metadata.subjects.all().count(), 3)
        self.assertEqual(str(self.resource.metadata.description), "New Description")
        self.assertEqual(str(self.resource.metadata.title), "New Title")
        self.resource.delete()

    def test_put_scimeta_composite_resource_with_core_metadata_and_coverage(self):
        # testing bulk metadata update with only core metadata that includes coverage metadata

        # create a composite resource
        self._create_resource(resource_type="CompositeResource")
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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
        self.resource.delete()

    def test_put_scimeta_timeseries_resource_with_core_metadata(self):
        # testing bulk metadata update that includes only core metadata

        # create a composite resource
        self._create_resource(resource_type="TimeSeriesResource")
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
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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
        self.resource.delete()

    def test_put_scimeta_timeseries_resource_with_core_metadata_failure(self):
        # testing bulk metadata update with only core metadata that includes coverage metadata
        # coverage metadata can't be updated for time series resource - this bulk update should fail

        # create a composite resource
        self._create_resource(resource_type="TimeSeriesResource")
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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
        self.resource.delete()

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
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
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

    def test_put_scimeta_modelinstance_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a model instance resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="ModelInstanceResource", file_to_upload=file_to_upload)
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
                "organization": "Org 2",
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "modeloutput": {"includes_output": False},
            "executedby": {"model_name": "id of a an existing model program resource"}
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_modelinstance_resource_without_core_metadata(self):
        # testing bulk metadata update updates only resource specific metadata

        # create a model instance resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="ModelInstanceResource", file_to_upload=file_to_upload)
        # create a model program resource to link as executed by
        model_program_resource = resource.create_resource(
            resource_type="ModelProgramResource",
            owner=self.user,
            title="A model program resource",
            files=(file_to_upload,)
            )
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "modeloutput": {"includes_output": True},
            "executedby": {"model_name": model_program_resource.short_id}
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()
        model_program_resource.delete()

    def test_put_scimeta_modflowinstance_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a MODFLOW model instance resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="MODFLOWModelInstanceResource",
                              file_to_upload=file_to_upload)
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
                "organization": "Org 1",
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }, {
                "name": "Test Name 2",
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "modeloutput": {"includes_output": False},
            "executedby": {"model_name": "id of a an existing model program resource"},
            "studyarea": {
                "totalLength": 1111,
                "totalWidth": 2222,
                "maximumElevation": 3333,
                "minimumElevation": 4444
            },
            "griddimensions": {
                "numberOfLayers": 5555,
                "typeOfRows": "Irregular",
                "numberOfRows": 6666,
                "typeOfColumns": "Regular",
                "numberOfColumns": 7777
            },
            "stressperiod": {
                "stressPeriodType":  "Steady and Transient",
                "steadyStateValue": 8888,
                "transientStateValueType": "Monthly",
                "transientStateValue": 9999
            },
            "groundwaterflow": {
                "flowPackage": "LPF",
                "flowParameter": "Hydraulic Conductivity"
            },
            "boundarycondition": {
                "specified_head_boundary_packages":  ["CHD", "FHB"],
                "specified_flux_boundary_packages": ["FHB", "WEL"],
                "head_dependent_flux_boundary_packages": ["RIV", "MNW1"]
            },
            "modelcalibration": {
                "calibratedParameter": "test parameter",
                "observationType": "test observation type",
                "observationProcessPackage": "GBOB",
                "calibrationMethod": "test calibration method"
            },
            "modelinputs": [
                {
                    "inputType": "test input type",
                    "inputSourceName": "test source name",
                    "inputSourceURL": "http://www.test.com"
                }
            ],
            "generalelements": {
                "modelParameter": "test model parameter",
                "modelSolver": "SIP",
                "output_control_package": ["HYD", "OC"],
                "subsidencePackage": "SWT"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_modflowinstance_resource_without_core_metadata(self):
        # testing bulk metadata update that updates onlt the resource specific
        # metadata

        # create a MODFLOW model instance resource
        some_file = 'hs_core/tests/data/cea.tif'
        file_to_upload = open(some_file, "r")
        self._create_resource(resource_type="MODFLOWModelInstanceResource",
                              file_to_upload=file_to_upload)
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "modeloutput": {"includes_output": False},
            "executedby": {"model_name": "id of a an existing model program resource"},
            "studyarea": {
                "totalLength": 1111,
                "totalWidth": 2222,
                "maximumElevation": 3333,
                "minimumElevation": 4444
            },
            "griddimensions": {
                "numberOfLayers": 5555,
                "typeOfRows": "Irregular",
                "numberOfRows": 6666,
                "typeOfColumns": "Regular",
                "numberOfColumns": 7777
            },
            "stressperiod": {
                "stressPeriodType":  "Steady and Transient",
                "steadyStateValue": 8888,
                "transientStateValueType": "Monthly",
                "transientStateValue": 9999
            },
            "groundwaterflow": {
                "flowPackage": "LPF",
                "flowParameter": "Hydraulic Conductivity"
            },
            "boundarycondition": {
                "specified_head_boundary_packages":  ["CHD", "FHB"],
                "specified_flux_boundary_packages": ["FHB", "WEL"],
                "head_dependent_flux_boundary_packages": ["RIV", "MNW1"]
            },
            "modelcalibration": {
                "calibratedParameter": "test parameter",
                "observationType": "test observation type",
                "observationProcessPackage": "GBOB",
                "calibrationMethod": "test calibration method"
            },
            "modelinputs": [
                {
                    "inputType": "test input type-1",
                    "inputSourceName": "test source name-1",
                    "inputSourceURL": "http://www.test-1.com"
                },
                {
                    "inputType": "test input type-2",
                    "inputSourceName": "test source name-2",
                    "inputSourceURL": "http://www.test-2.com"
                }
            ],
            "generalelements": {
                "modelParameter": "test model parameter",
                "modelSolver": "SIP",
                "output_control_package": ["HYD", "OC"],
                "subsidencePackage": "SWT"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_script_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a script resource
        self._create_resource(resource_type="ScriptResource")
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
                "organization": "Org 1",
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }, {
                "name": "Test Name 2",
                "organization": "Org 2"
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "scriptspecificmetadata": {
                    "scriptLanguage": "R",
                    "languageVersion": "3.5",
                    "scriptVersion": "1.0",
                    "scriptDependencies": "None",
                    "scriptReleaseDate": "2015-12-01 00:00",
                    "scriptCodeRepository": "http://www.google.com"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_script_resource_without_core_metadata(self):
        # testing bulk metadata update for resource specific
        # metadata only

        # create a script resource
        self._create_resource(resource_type="ScriptResource")
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "scriptspecificmetadata": {
                    "scriptLanguage": "R",
                    "languageVersion": "3.5",
                    "scriptVersion": "1.0",
                    "scriptDependencies": "None",
                    "scriptReleaseDate": "2015-12-01 00:00",
                    "scriptCodeRepository": "http://www.google.com"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_SWATModelInstance_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a SWAT model resource
        self._create_resource(resource_type="SWATModelInstanceResource")
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
                "organization": "Org 2",
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "modeloutput": {"includes_output": False},
            "executedby": {"model_name": "id of a an existing model program resource"},
            "modelobjective": {
                "swat_model_objectives": ["BMPs", "Hydrology", "Water quality"],
                "other_objectives": "some other objectives"
            },
            "simulationtype": {
                "simulation_type_name": "Normal Simulation"
            },
            "modelmethod": {
                "runoffCalculationMethod": "A test calculation method",
                "flowRoutingMethod": "A test flow routing method",
                "petEstimationMethod": "A test estimation method"
            },
            "modelparameter": {
                "model_parameters": ["Crop rotation", "Tillage operation"],
                "other_parameters": "some other model parameters"
            },
            "modelinput": {
                "warmupPeriodValue": 10,
                "rainfallTimeStepType": "Daily",
                "rainfallTimeStepValue": 5,
                "routingTimeStepType": "Daily",
                "routingTimeStepValue": 2,
                "simulationTimeStepType": "Hourly",
                "simulationTimeStepValue": 1,
                "watershedArea": 1000,
                "numberOfSubbasins": 200,
                "numberOfHRUs": 10000,
                "demResolution": 30,
                "demSourceName": "Unknown",
                "demSourceURL": "http://dem-source.org",
                "landUseDataSourceName": "Unknown",
                "landUseDataSourceURL": "http://land-data.org",
                "soilDataSourceName": "Unknown",
                "soilDataSourceURL": "http://soil-data.org"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_SWATModelInstance_resource_without_core_metadata(self):
        # testing bulk metadata update that includes only resource specific
        # metadata update

        # create a SWAT model resource
        self._create_resource(resource_type="SWATModelInstanceResource")
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "modeloutput": {"includes_output": False},
            "executedby": {"model_name": "id of a an existing model program resource"},
            "modelobjective": {
                "swat_model_objectives": ["BMPs", "Hydrology", "Water quality"],
                "other_objectives": "some other objectives"
            },
            "simulationtype": {
                "simulation_type_name": "Normal Simulation"
            },
            "modelmethod": {
                "runoffCalculationMethod": "A test calculation method",
                "flowRoutingMethod": "A test flow routing method",
                "petEstimationMethod": "A test estimation method"
            },
            "modelparameter": {
                "model_parameters": ["Crop rotation", "Tillage operation"],
                "other_parameters": "some other model parameters"
            },
            "modelinput": {
                "warmupPeriodValue": 10,
                "rainfallTimeStepType": "Daily",
                "rainfallTimeStepValue": 5,
                "routingTimeStepType": "Daily",
                "routingTimeStepValue": 2,
                "simulationTimeStepType": "Hourly",
                "simulationTimeStepValue": 1,
                "watershedArea": 1000,
                "numberOfSubbasins": 200,
                "numberOfHRUs": 10000,
                "demResolution": 30,
                "demSourceName": "Unknown",
                "demSourceURL": "http://dem-source.org",
                "landUseDataSourceName": "Unknown",
                "landUseDataSourceURL": "http://land-data.org",
                "soilDataSourceName": "Unknown",
                "soilDataSourceURL": "http://soil-data.org"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_web_app_resource_with_core_metadata(self):
        # testing bulk metadata update that includes both core metadata and resource specific
        # metadata update

        # create a web app resource
        self._create_resource(resource_type="ToolResource")
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
                "organization": "Org 2",
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/011",
                                "ResearchGateID": "https://www.researchgate.net/001"}
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"},
            "sources": [
                {
                    "derived_from": "Source 3"
                },
                {
                    "derived_from": "Source 2"
                }
            ],
            "requesturlbase": {
                "value": "https://www.google.com"
            },
            "toolversion": {
                "value": "1.12"
            },
            "supportedrestypes": {
                "supported_res_types": ["NetcdfResource", "TimeSeriesResource"]
            },
            "supportedsharingstatuses": {
                "sharing_status": ["Public", "Discoverable"]
            },
            "toolicon": {
                "value": "https://www.hydroshare.org/static/img/logo-sm.png"
            },
            "apphomepageurl": {
                "value": "https://mywebapp.com"
            }
        }

        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_web_app_resource_without_core_metadata(self):
        # testing bulk metadata update that includes only resource specific
        # metadata update

        # create a web app resource
        self._create_resource(resource_type="ToolResource")
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(
            res_id=self.resource.short_id)
        put_data = {
            "requesturlbase": {
                "value": "https://www.google.com"
            },
            "toolversion": {
                "value": "1.12"
            },
            "supportedrestypes": {
                "supported_res_types": ["NetcdfResource", "TimeSeriesResource"]
            },
            "supportedsharingstatuses": {
                "sharing_status": ["Public", "Discoverable"]
            },
            "toolicon": {
                "value": "https://www.hydroshare.org/static/img/logo-sm.png"
            },
            "apphomepageurl": {
                "value": "https://mywebapp.com"
            }
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def _create_resource(self, resource_type, file_to_upload=None):
        files = ()
        if file_to_upload is not None:
            files = (file_to_upload,)
        self.resource = resource.create_resource(
            resource_type=resource_type,
            owner=self.user,
            title="Testing bulk metadata update for resource type - {}".format(resource_type),
            files=files
            )
        resource_post_create_actions(resource=self.resource, user=self.user,
                                     metadata=self.resource.metadata)
