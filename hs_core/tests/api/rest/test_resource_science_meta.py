import json
from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.hydroshare.utils import resource_post_create_actions
from .base import HSRESTTestCase


class TestResourceScienceMetadata(HSRESTTestCase):

    def setUp(self):
        super(TestResourceScienceMetadata, self).setUp()

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)
        self.resource = res
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # create another resource for testing relation metadata
        another_res = resource.create_resource('CompositeResource',
                                               self.user,
                                               'My another Test resource')
        self.pid2 = another_res.short_id
        self.resources_to_delete.append(self.pid2)

    def test_get_scimeta(self):
        # set resource public
        self.resource.raccess.public = True
        self.resource.raccess.save()
        # remove authentication to test public view
        self.client.logout()
        # Get the resource system metadata
        sysmeta_url = "/hsapi/resource/{res_id}/scimeta/elements/".format(res_id=self.pid)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # content = json.loads(response.content.decode())

    def test_put_scimeta_composite_resource(self):
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
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/002"}
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
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/001"}
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
            "relations": [
                {
                    "type": "source",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                },
                {
                    "type": "isExecutedBy",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                }
            ],
            "geospatialrelations": [
                {
                    "type": "relation",
                    "value": "https://geoconnex.us/ref/dams/1083460",
                    "text": "Bonnie Meade [dams/1083460]"
                },
                {
                    "type": "relation",
                    "value": "https://geoconnex.us/ref/dams/1083461",
                    "text": "Trenton - Auxiliary Spillway [dams/1083461]"
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
        self.assertEqual(self.resource.metadata.relations.all().count(), 2)
        self.assertEqual(self.resource.metadata.geospatialrelations.all().count(), 2)
        self.assertEqual(self.resource.metadata.funding_agencies.all().count(), 2)
        self.assertEqual(str(self.resource.metadata.rights), "CCC http://www.hydroshare.org")
        self.assertEqual(str(self.resource.metadata.language), "fre")
        self.assertEqual(self.resource.metadata.coverages.all().count(), 1)
        self.assertEqual(self.resource.metadata.creators.all().count(), 2)
        self.assertEqual(self.resource.metadata.contributors.all().count(), 2)
        self.assertEqual(self.resource.metadata.subjects.all().count(), 3)
        self.assertEqual(str(self.resource.metadata.description), "New Description")
        self.assertEqual(str(self.resource.metadata.title), "New Title")

    def test_put_scimeta_composite_resource_double_none(self):
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"}
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
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/001"}
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
            "relations": [
                {
                    "type": "source",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                },
                {
                    "type": "isExecutedBy",
                    "value": "https://www.hydroshare.org/resource/{}/".format(self.pid2)
                }
            ],
            "geospatialrelations": [
                {
                    "type": "relation",
                    "value": "https://geoconnex.us/ref/dams/1083460",
                    "text": "Bonnie Meade [dams/1083460]"
                },
                {
                    "type": "relation",
                    "value": "https://geoconnex.us/ref/dams/1083461",
                    "text": "Trenton - Auxiliary Spillway [dams/1083461]"
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
        self.assertEqual(self.resource.metadata.relations.all().count(), 2)
        self.assertEqual(self.resource.metadata.geospatialrelations.all().count(), 2)
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
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"}
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_scimeta_timeseries_resource_with_core_metadata(self):
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
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/001"}
            }],
            "dates": [
                {
                    "type": "valid",
                    "start_date": "2016-12-07T00:00:00Z",
                    "end_date": "2018-12-07T00:00:00Z"
                }
            ],
            "language": "fre",
            "rights": {"statement": "CCC", "url": "http://www.hydroshare.org"}
        }
        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.resource.delete()

    def test_put_web_app_resource_tool_metadata(self):
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
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/001"}
            }],
            "creators": [{
                "name": "Creator",
                "organization": None,
                "identifiers": {"ORCID": "https://orcid.org/0000-0003-4621-0559",
                                "ResearchGateID": "https://www.researchgate.net/profile/001"}
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
            "requesturlbase": {
                "value": "https://www.google.com"
            },
            "toolversion": {
                "value": "1.12"
            },
            "supportedrestypes": {
                "supported_res_types": ["CompositeResource", "CollectionResource"]
            },
            "supportedsharingstatuses": {
                "sharing_status": ["Public", "Discoverable"]
            },
            "toolicon": {
                "value": "https://storage.googleapis.com/hydroshare-prod-static-media/static/img/logo-sm.png"
            },
            "apphomepageurl": {
                "value": "https://mywebapp.com"
            },
            "mailing_list_url": {
                "value": "https://mywebapp.com/mailinglist"
            },
            "testing_protocol_url": {
                "value": "https://mywebapp.com/testingprotocol"
            },
            "help_page_url": {
                "value": "https://mywebapp.com/helppage"
            },
            "source_code_url": {
                "value": "https://mywebapp.com/sourcecode"
            },
            "issues_page_url": {
                "value": "https://mywebapp.com/issues"
            },
            "roadmap": {
                "value": "roadmap"
            }
        }

        response = self.client.put(sysmeta_url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        response = self.client.get(sysmeta_url, format='json')
        content = json.loads(response.content.decode())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content["app_home_page_url"]["value"], "https://mywebapp.com")
        self.assertEqual(content["mailing_list_url"]["value"], "https://mywebapp.com/mailinglist")
        self.assertEqual(content["testing_protocol_url"]["value"], "https://mywebapp.com/testingprotocol")
        self.assertEqual(content["help_page_url"]["value"], "https://mywebapp.com/helppage")
        self.assertEqual(content["source_code_url"]["value"], "https://mywebapp.com/sourcecode")
        self.assertEqual(content["issues_page_url"]["value"], "https://mywebapp.com/issues")
        self.assertEqual(content["roadmap"]["value"], "roadmap")

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
                "supported_res_types": ["CompositeResource", "CollectionResource"]
            },
            "supportedsharingstatuses": {
                "sharing_status": ["Public", "Discoverable"]
            },
            "toolicon": {
                "value": "https://storage.googleapis.com/hydroshare-prod-static-media/static/img/logo-sm.png"
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
