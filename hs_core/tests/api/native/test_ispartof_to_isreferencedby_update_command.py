from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.management import call_command

from hs_collection_resource.models import CollectionResource
from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.enums import RelationTypes
from hs_core.testing import MockS3TestCaseMixin


class TestRelationTypeUpdateCommand(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(TestRelationTypeUpdateCommand, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'mp_resource_migration@email.com',
            username='mp_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.update_command = "migrate_ispartof_not_collection_related"

        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        CollectionResource.objects.all().delete()

    def tearDown(self):
        super(TestRelationTypeUpdateCommand, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        CollectionResource.objects.all().delete()

    def test_update_is_part_of_relation_1(self):
        """
        Testing user edited relation type 'isPartOf' is updated to 'isReferencedBy' when we run the command.
        """

        # create a composite resource
        comp_res = self._create_resource()
        # check no 'isPartOf' relation exists
        metadata = comp_res.metadata
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isPartOf).exists())
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isReferencedBy).exists())
        # add 'isPartOf' relation that is not related to collection
        metadata.create_element('relation', type=RelationTypes.isPartOf, value="testing")
        self.assertTrue(metadata.relations.filter(type=RelationTypes.isPartOf).exists())

        # run  update command to update the type 'isPartOf' to 'isReferencedBy'
        call_command(self.update_command)
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isPartOf).exists())
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isReferencedBy).count(), 1)

    def test_update_is_part_of_relation_2(self):
        """
        Testing user edited multiple relation type 'isPartOf' is updated to 'isReferencedBy' when we run the command.
        """

        # create a composite resource
        comp_res = self._create_resource()
        comp_res_2 = self._create_resource()
        # check no 'isPartOf' relation exists
        metadata = comp_res.metadata
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isPartOf).exists())
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isReferencedBy).exists())
        # add 2 'isPartOf' relation that is not related to collection
        metadata.create_element('relation', type=RelationTypes.isPartOf, value="testing-1")
        metadata.create_element('relation', type=RelationTypes.isPartOf, value=comp_res_2.get_citation())
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isPartOf).count(), 2)

        # run  update command to update the type 'isPartOf' to 'isReferencedBy'
        call_command(self.update_command)
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isPartOf).exists())
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isReferencedBy).count(), 2)

    def test_update_is_part_of_relation_3(self):
        """
        Testing user edited relation type 'isPartOf' is updated to 'isReferencedBy' when we run the command. However,
        'isPartOf' relation type that is related to collection resource is not updated by the command.
        """

        # create a composite resource and a collection resource
        comp_res = self._create_resource()
        col_res = self._create_resource(res_type='CollectionResource')
        # make the res part of the collection resource
        col_res.resources.add(comp_res)
        # check no 'isPartOf' relation exists
        metadata = comp_res.metadata
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isPartOf).exists())
        self.assertFalse(metadata.relations.filter(type=RelationTypes.isReferencedBy).exists())
        # add collection related 'isPartOf' relation - this won't be updated when we run the command
        metadata.create_element('relation', type=RelationTypes.isPartOf, value=col_res.get_citation())

        # add 2 'isPartOf' relation that is not related to collection
        metadata.create_element('relation', type=RelationTypes.isPartOf, value="testing-1")
        metadata.create_element('relation', type=RelationTypes.isPartOf, value="testing-2")
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isPartOf).count(), 3)

        # run  update command to update the type 'isPartOf' to 'isReferencedBy'
        call_command(self.update_command)
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isPartOf).count(), 1)
        self.assertEqual(metadata.relations.filter(type=RelationTypes.isReferencedBy).count(), 2)

    def _create_resource(self, res_type='CompositeResource', add_keywords=False):
        res = hydroshare.create_resource(res_type, self.user, "Testing updating relation type isPartOf")
        if add_keywords:
            res.metadata.create_element('subject', value='kw-1')
            res.metadata.create_element('subject', value='kw-2')
        return res
