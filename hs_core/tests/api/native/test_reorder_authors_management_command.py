from unittest import TestCase

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError

from hs_core.models import BaseResource, Creator
from hs_core import hydroshare
from hs_core.hydroshare import resource

from dateutil import parser


class TestReorderAuthorsCommand(TestCase):
    def setUp(self):
        super(TestReorderAuthorsCommand, self).setUp()

        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")
        self.user = hydroshare.create_account(
            "user1@nowhere.com",
            username="user1",
            first_name="Creator_FirstName",
            last_name="Creator_LastName",
            superuser=False,
            groups=[],
        )

        self.res = hydroshare.create_resource(
            resource_type="CompositeResource",
            owner=self.user,
            title="A resource",
            keywords=["kw1", "kw2"],
        )

        # add 4 creators element (so in total we will have 5 creators)
        resource.create_metadata_element(
            self.res.short_id, "creator", name="John Smith"
        )
        resource.create_metadata_element(
            self.res.short_id, "creator", name="Lisa McWill"
        )
        resource.create_metadata_element(
            self.res.short_id, "creator", name="Kelly Anderson"
        )
        resource.create_metadata_element(
            self.res.short_id, "creator", name="Mark Miller"
        )

    def run_management_command(self):
        call_command("reorder_authors", f"--resource_id={self.res.short_id}")

    def tearDown(self):
        super(TestReorderAuthorsCommand, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        Creator.objects.all().delete()

    def test_command_doesnt_alter_if_aready_correct(self):
        """
        Testing author order is maintained if they were already correct
        """
        citation_original = self.res.get_citation()

        self.assertEqual(self.res.get_citation(), citation_original)
        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

        # run  update command to fix author order
        self.run_management_command()

        self.assertEqual(self.res.get_citation(), citation_original)
        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

    def test_command_alters_if_incorrect(self):
        """
        Testing author order is updated if it was incorrect
        """

        # Intentionally make a creator list with duplicate orders
        john = self.res.metadata.creators.filter(name="John Smith").first()
        lisa = self.res.metadata.creators.filter(name="Lisa McWill").first()
        self.assertEqual(john.order, 2)
        john.order = 3
        john.save()
        self.assertEqual(john.order, lisa.order)

        # run  update command to fix author order
        self.run_management_command()

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

    def test_command_alters_missing_first_author(self):
        """
        Testing author order is updated if there was a missing first author
        """

        # Intentionally make a creator list with duplicate orders
        john = self.res.metadata.creators.filter(name="John Smith").first()
        hs_author = self.res.metadata.creators.filter(
            name="Creator_LastName, Creator_FirstName"
        ).first()
        self.assertEqual(hs_author.order, 1)
        hs_author.order = 2
        hs_author.save()
        self.assertEqual(john.order, hs_author.order)
        self.assertIsNone(self.res.metadata.creators.filter(order=1).first())

        # run  update command to fix author order
        self.run_management_command()

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

        # query for first author no longer raises exception
        first_author = self.res.metadata.creators.filter(order=1).first()
        self.assertIsNotNone(first_author)

        john = self.res.metadata.creators.filter(name="John Smith").first()
        hs_author = self.res.metadata.creators.filter(
            name="Creator_LastName, Creator_FirstName"
        ).first()
        self.assertNotEqual(john.order, hs_author.order)

        # Demonstrate that we don't actually know which author became "first" author
        self.assertIn(john.order, [1, 2])
        self.assertIn(hs_author.order, [1, 2])

    def test_command_fixes_multiple_authors(self):
        """
        Testing author order is updated if there were multiple duplicate author orders
        """

        # Intentionally make a creator list with duplicate orders
        lisa = self.res.metadata.creators.filter(name="Lisa McWill").first()
        last_author = self.res.metadata.creators.last()
        self.assertEqual(lisa.order, 3)
        self.assertEqual(last_author.order, 5)
        lisa.order = 2
        last_author.order = 4
        lisa.save()
        last_author.save()

        # run  update command to fix author order
        self.run_management_command()

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

    def test_command_fixes_triplicate_authors(self):
        """
        Testing author order is updated if there were 3 authors with the same order

        This tests the case where two authors had faulty orders due to being moved,
        resulting in a triplicate of author.order.
        """

        # Intentionally make a creator list with duplicate orders
        lisa = self.res.metadata.creators.filter(name="Lisa McWill").first()
        last_author = self.res.metadata.creators.last()
        self.assertEqual(lisa.order, 3)
        self.assertEqual(last_author.order, 5)
        lisa.order = 4
        last_author.order = 4
        lisa.save()
        last_author.save()

        # run  update command to fix author order
        self.run_management_command()

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

    def test_command_maintains_citations(self):
        """
        Testing citation is maintained after author_order management command
        """

        # Intentionally make a creator list with duplicate orders
        second_author = self.res.metadata.creators.filter(order=2).first()
        fourth_author = self.res.metadata.creators.filter(order=4).first()
        second_author.order = 3
        fourth_author.order = 5
        second_author.save()
        fourth_author.save()

        cit_original = self.res.get_citation()

        # run  update command to fix author order
        self.run_management_command()

        self.assertEqual(self.res.get_citation(), cit_original)

    def test_author_order_command_doesnt_touch_published(self):
        """
        Testing author_order management command does not alter published resources
        """

        # Intentionally make a creator list with duplicate orders
        second_author = self.res.metadata.creators.filter(order=2).first()
        fourth_author = self.res.metadata.creators.filter(order=4).first()
        second_author.order = 3
        fourth_author.order = 5
        second_author.save()
        fourth_author.save()

        self.assertFalse(self.res.metadata.dates.filter(type="published").exists())
        self.res.raccess.published = True
        self.res.raccess.save()
        resource.create_metadata_element(
            self.res.short_id,
            "date",
            type="published",
            start_date=parser.parse("8/10/2014"),
        )
        cit_pub = self.res.get_citation()

        # run  update command to fix author order
        with self.assertRaises(CommandError):
            self.run_management_command()

        self.assertEqual(self.res.get_citation(), cit_pub)

        self.assertEqual(self.res.metadata.creators.filter(order=3).count(), 2)
        self.assertEqual(self.res.metadata.creators.filter(order=5).count(), 2)
