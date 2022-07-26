from unittest import TestCase

from django.contrib.auth.models import Group, User
from django.core.management import call_command

from hs_core.models import GenericResource, Creator
from hs_core import hydroshare
from hs_core.hydroshare import resource


class TestReorderAuthorsCommand(TestCase):

    def setUp(self):
        super(TestReorderAuthorsCommand, self).setUp()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic resource',
            keywords=['kw1', 'kw2']
        )

        self.citation_original = self.res.get_citation()

        # add 4 creators element (so in total we will have 5 creators)
        resource.create_metadata_element(self.res.short_id, 'creator', name='John Smith')
        resource.create_metadata_element(self.res.short_id, 'creator', name='Lisa McWill')
        resource.create_metadata_element(self.res.short_id, 'creator', name='Kelly Anderson')
        resource.create_metadata_element(self.res.short_id, 'creator', name='Mark Miller')

        self.update_command = "reorder_authors"

    def tearDown(self):
        super(TestReorderAuthorsCommand, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        Creator.objects.all().delete()

    def test_command_doesnt_alter_if_aready_correct(self):
        """
        Testing author order is maintained if they were already correct
        """
        citation_original = self.res.get_citation()

        # run  update command to fix author order
        call_command(self.update_command)

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
        call_command(self.update_command)

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

    def test_command_alters_missing_first_author(self):
        """
        Testing author order is updated if there was a missing first author
        """

        # Intentionally make a creator list with duplicate orders
        john = self.res.metadata.creators.filter(name="John Smith").first()
        first_author = self.res.metadata.creators.filter(order=1).first()
        self.assertEqual(first_author.order, 1)
        first_author.order = 2
        first_author.save()
        self.assertEqual(john.order, first_author.order)

        # run  update command to fix author order
        call_command(self.update_command)

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

        self.assertEqual(first_author.name, "Hydroshare Author")

    def test_command_fixes_multiple_authors(self):
        """
        Testing author order is updated if there were multiple duplicate author orders
        """

        # Intentionally make a creator list with duplicate orders
        first_author = self.res.metadata.creators.filter(order=1).first()
        last_author = self.res.metadata.creators.last()
        self.assertEqual(first_author.order, 1)
        self.assertEqual(last_author.order, 5)
        first_author.order = 2
        last_author.order = 4
        first_author.save()
        last_author.save()

        # run  update command to fix author order
        call_command(self.update_command)

        for index, creator in enumerate(self.res.metadata.creators.all(), start=1):
            self.assertEqual(index, creator.order)

        hs_author = self.res.metadata.creators.filter(name="Hydroshare Author").first()
        mark = self.res.metadata.creators.filter(name="Mark Miller").first()

        self.assertEqual(hs_author.order, 1)
        self.assertEqual(mark.order, 5)

    def test_command_maintains_citations(self):
        """
        Testing citation is maintained after author_order management command
        """

        # sanity check on existing citation
        self.assertEqual(self.res.get_citation(), self.citation_original)

        # Intentionally make a creator list with duplicate orders
        second_author = self.res.metadata.creators.filter(order=2).first()
        fourth_author = self.res.metadata.creators.filter(order=4).first()
        second_author.order = 3
        fourth_author.order = 5
        second_author.save()
        fourth_author.save()

        # run  update command to fix author order
        call_command(self.update_command)

        self.assertEqual(self.res.get_citation(), self.citation_original)