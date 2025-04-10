from dateutil import parser

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin


class TestUpdateMetadata(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestUpdateMetadata, self).setUp()
        group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "shaun@gmail.com",
            username="shaunjl",
            first_name="shaun",
            last_name="john",
            superuser=False,
        )

        self.res = hydroshare.create_resource(
            "CompositeResource", self.user, "Test Resource"
        )

    def test_update_science_metadata(self):
        # add these new metadata elements
        metadata_dict = [
            {'title': {'value': 'Updated Resource Title'}},
            {'description': {'abstract': 'Updated Resource Abstract'}},
            {'date': {'type': 'valid', 'start_date': '1/26/2016', 'end_date': '12/31/2016'}},
            {'date': {'type': 'created', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'modified', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'published', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'available', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Lisa Molley', 'email': 'lmolley@gmail.com'}},
            {'contributor': {'name': 'Kelvin Marshal', 'email': 'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'identifiers': {'ORCID': 'https://orcid.org/0000-0003-4621-0559',
                                             'ResearchGateID': 'https://www.researchgate.net/profile/john'}
                             }},
            {'coverage': {'type': 'period', 'value': {'name': 'Name for period coverage', 'start': '1/1/2000',
                                                      'end': '12/12/2012'}}},
            {'coverage': {'type': 'point', 'value': {'name': 'Name for point coverage', 'east': '56.45678',
                                                     'north': '12.6789', 'units': 'decimal deg'}}},
            {'format': {'value': 'txt/csv'}},   # will be ignored without error
            {'format': {'value': 'zip'}},   # will be ignored without error
            {'identifier': {'name': 'someIdentifier', 'url': "http://some.org/002"}},
            {'identifier': {'name': 'hydroShareIdentifier', 'url': "http://hydroshare.org/001"}},   # will be ignored
            {'language': {'code': 'fre'}},
            {'geospatialrelation': {'type': 'relation', 'value': 'https://geoconnex.us/ref/dams/1083460',
                                    'text': 'Bonnie Meade [dams/1083460]'}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource', 'url': 'http://rights.ord/001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
        ]

        hydroshare.update_science_metadata(
            pk=self.res.short_id, metadata=metadata_dict, user=self.user
        )

        # check that the title element got updated
        self.assertEqual(
            self.res.metadata.title.value,
            "Updated Resource Title",
            msg="Resource title did not match",
        )

        # check that description element (abstract) got updated
        self.assertEqual(
            self.res.metadata.description.abstract,
            "Updated Resource Abstract",
            msg="Resource abstract did not match",
        )

        # the following 3 date elements should exist
        self.assertEqual(
            self.res.metadata.dates.all().count(),
            3,
            msg="Number of date elements not equal to 3.",
        )
        self.assertIn(
            "created",
            [dt.type for dt in self.res.metadata.dates.all()],
            msg="Date element type 'Created' does not exist",
        )
        self.assertIn(
            "modified",
            [dt.type for dt in self.res.metadata.dates.all()],
            msg="Date element type 'Modified' does not exist",
        )
        self.assertIn(
            "valid",
            [dt.type for dt in self.res.metadata.dates.all()],
            msg="Date element type 'Valid' does not exist",
        )

        valid_date = self.res.metadata.dates.filter(type="valid").first()
        self.assertEqual(valid_date.start_date.date(), parser.parse("1/26/2016").date())
        self.assertEqual(valid_date.end_date.date(), parser.parse("12/31/2016").date())

        # number of creators at this point should be 2 (the original creator of the resource get deleted as part of
        # this update)
        self.assertEqual(
            self.res.metadata.creators.all().count(),
            2,
            msg="Number of creators not equal to 3",
        )
        self.assertIn(
            "John Smith",
            [cr.name for cr in self.res.metadata.creators.all()],
            msg="Creator 'John Smith' was not found",
        )
        self.assertIn(
            "Lisa Molley",
            [cr.name for cr in self.res.metadata.creators.all()],
            msg="Creator 'Lisa Molley' was not found",
        )

        self.assertIn(
            "jsmith@gmail.com",
            [cr.email for cr in self.res.metadata.creators.all()],
            msg="Creator email 'jsmith@gmail.com' was not found",
        )
        self.assertIn(
            "lmolley@gmail.com",
            [cr.email for cr in self.res.metadata.creators.all()],
            msg="Creator email 'lmolley@gmail.com' was not found",
        )

        # number of contributors at this point should be 1
        self.assertEqual(
            self.res.metadata.contributors.all().count(),
            1,
            msg="Number of contributors not equal to 1",
        )
        contributor = self.res.metadata.contributors.first()
        self.assertEqual(contributor.name, "Kelvin Marshal")
        self.assertEqual(contributor.email, "kmarshal@yahoo.com")
        self.assertEqual(contributor.organization, "Utah State University")
        for name, link in list(contributor.identifiers.items()):
            self.assertIn(name, ["ResearchGateID", "ORCID"])
            self.assertIn(
                link, ["https://orcid.org/0000-0003-4621-0559", "https://www.researchgate.net/profile/john"]
            )

        # there should be now 2 coverage elements
        self.assertEqual(
            self.res.metadata.coverages.all().count(),
            2,
            msg="Number of coverages not equal to 2.",
        )

        # there should 1 coverage element of type 'period'
        self.assertEqual(
            self.res.metadata.coverages.filter(type="period").count(),
            1,
            msg="Number of coverage elements of type 'period is not equal to 1",
        )

        # there should 1 coverage element of type 'point'
        self.assertEqual(
            self.res.metadata.coverages.filter(type="point").count(),
            1,
            msg="Number of coverage elements of type 'point' is not equal to 1",
        )

        cov_period = self.res.metadata.coverages.filter(type="period").first()
        self.assertEqual(cov_period.value["name"], "Name for period coverage")
        self.assertEqual(
            parser.parse(cov_period.value["start"]).date(),
            parser.parse("1/1/2000").date(),
        )
        self.assertEqual(
            parser.parse(cov_period.value["end"]).date(),
            parser.parse("12/12/2012").date(),
        )

        cov_point = self.res.metadata.coverages.filter(type="point").first()
        self.assertEqual(cov_point.value["name"], "Name for point coverage")
        self.assertEqual(cov_point.value["east"], 56.45678)
        self.assertEqual(cov_point.value["north"], 12.6789)
        self.assertEqual(cov_point.value["units"], "decimal deg")

        # there should be no format elements
        self.assertEqual(
            self.res.metadata.formats.all().count(),
            0,
            msg="Number of format elements not equal to 0.",
        )

        # there should be now 2 identifier elements ( 1 we are creating her + 1 auto generated at the time of
        # resource creation)
        self.assertEqual(
            self.res.metadata.identifiers.all().count(),
            2,
            msg="Number of identifier elements not equal to 1.",
        )

        # this the one we added as part of the update
        some_identifier = self.res.metadata.identifiers.filter(
            name="someIdentifier"
        ).first()
        self.assertEqual(some_identifier.url, "http://some.org/002")

        self.assertEqual(
            self.res.metadata.language.code,
            "fre",
            msg="Resource has a language that is not French.",
        )

        self.assertEqual(
            self.res.metadata.relations.all().count(),
            1,
            msg="Number of source elements is not equal to 1",
        )
        relation = self.res.metadata.relations.filter(type="isPartOf").first()
        self.assertEqual(relation.value, "http://hydroshare.org/resource/001")

        self.assertEqual(self.res.metadata.geospatialrelations.all().count(), 1,
                         msg="Number of geospatialrelation elements is not equal to 1")
        geospatialrelation = self.res.metadata.geospatialrelations.first()
        self.assertEqual(geospatialrelation.value, 'https://geoconnex.us/ref/dams/1083460')
        self.assertEqual(geospatialrelation.text, 'Bonnie Meade [dams/1083460]')

        self.assertEqual(self.res.metadata.rights.statement, 'This is the rights statement for this resource',
                         msg="Statement of rights did not match.")
        self.assertEqual(self.res.metadata.rights.url, 'http://rights.ord/001', msg="URL of rights did not match.")

        # there should be 2 subject elements for this resource
        self.assertEqual(
            self.res.metadata.subjects.all().count(),
            2,
            msg="Number of subject elements found not be 1.",
        )
        self.assertIn(
            "sub-1",
            [sub.value for sub in self.res.metadata.subjects.all()],
            msg="Subject element with value of %s does not exist." % "sub-1",
        )
        self.assertIn(
            "sub-2",
            [sub.value for sub in self.res.metadata.subjects.all()],
            msg="Subject element with value of %s does not exist." % "sub-1",
        )

    def test_update_science_metadata_coverage_type_box(self):
        metadata_dict = [
            {
                "coverage": {
                    "type": "period",
                    "value": {
                        "name": "Name for period coverage",
                        "start": "1/1/2000",
                        "end": "12/12/2012",
                    },
                }
            },
            {
                "coverage": {
                    "type": "box",
                    "value": {
                        "name": "Name for box coverage",
                        "northlimit": "56.45678",
                        "eastlimit": "130.6789",
                        "southlimit": "16.45678",
                        "westlimit": "16.6789",
                        "units": "decimal deg",
                    },
                }
            },
        ]

        # there should be 0 coverage elements
        self.assertEqual(
            self.res.metadata.coverages.all().count(),
            0,
            msg="Number of coverages not equal to 0.",
        )

        # now add the 2 coverage elements by updating metadata
        hydroshare.update_science_metadata(
            pk=self.res.short_id, metadata=metadata_dict, user=self.user
        )

        # there should be now 2 coverage elements after the update
        self.assertEqual(
            self.res.metadata.coverages.all().count(),
            2,
            msg="Number of coverages not equal to 2.",
        )
        self.assertEqual(
            self.res.metadata.coverages.filter(type="period").count(),
            1,
            msg="Number of coverage element of type period is not equal to 1.",
        )
        self.assertEqual(
            self.res.metadata.coverages.filter(type="box").count(),
            1,
            msg="Number of coverage element of type box is not equal to 1.",
        )

        cov_box = self.res.metadata.coverages.filter(type="box").first()
        self.assertEqual(cov_box.value["name"], "Name for box coverage")
        self.assertEqual(cov_box.value["northlimit"], 56.45678)
        self.assertEqual(cov_box.value["eastlimit"], 130.6789)
        self.assertEqual(cov_box.value["southlimit"], 16.45678)
        self.assertEqual(cov_box.value["westlimit"], 16.6789)
        self.assertEqual(cov_box.value["units"], "decimal deg")

    def test_update_metadata_ignored_elements(self):
        # the following elements are ignored
        _ = [
            {"date": {"type": "created", "start_date": "1/26/2015"}},
            {"date": {"type": "modified", "start_date": "1/26/2015"}},
            {"date": {"type": "published", "start_date": "1/26/2015"}},
            {"date": {"type": "available", "start_date": "1/26/2015"}},
            {"format": {"value": "txt/csv"}},
            {"format": {"value": "zip"}},
            {
                "identifier": {
                    "name": "hydroShareIdentifier",
                    "url": "http://hydroshare.org/001",
                }
            },
        ]

        # the following 2 date elements should exist
        self.assertEqual(
            self.res.metadata.dates.all().count(),
            2,
            msg="Number of date elements not equal to 2.",
        )
        # test that the created date was not updated
        created_date = self.res.metadata.dates.filter(type="created").first()
        self.assertNotEqual(
            created_date.start_date.date(), parser.parse("1/26/2015").date()
        )
        modified_date = self.res.metadata.dates.filter(type="modified").first()

        # test that the modified date was not updated
        self.assertNotEqual(
            modified_date.start_date.date(), parser.parse("1/26/2015").date()
        )

        # test the publisher date was not added
        self.assertEqual(self.res.metadata.dates.filter(type="published").count(), 0)
        # test the available date was not added
        self.assertEqual(self.res.metadata.dates.filter(type="available").count(), 0)
        # there should be no format elements
        self.assertEqual(
            self.res.metadata.formats.all().count(),
            0,
            msg="Number of format elements not equal to 0.",
        )
        # test the hydroShareIdentifier was not updated
        self.assertEqual(
            self.res.metadata.identifiers.filter(name="hydroShareIdentifier").count(), 1
        )
        hs_identifier = self.res.metadata.identifiers.filter(
            name="hydroShareIdentifier"
        ).first()
        self.assertNotEqual(hs_identifier.url, "http://hydroshare.org/001")
