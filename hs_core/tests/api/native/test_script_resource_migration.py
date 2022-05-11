from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_script_resource.models import ScriptResource


class TestScriptResourceMigration(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestScriptResourceMigration, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'script_resource_migration@email.com',
            username='script_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.migration_command = "migrate_script_resources"

        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ScriptResource.objects.all().delete()

    def tearDown(self):
        super(TestScriptResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        ScriptResource.objects.all().delete()

    def test_migrate_script_resource_1(self):
        """
        Migrate a script resource that has no resource specific metadata.
        """

        # create a script resource
        script_res = self._create_script_resource()
        self.assertEqual(ScriptResource.objects.count(), 1)
        self.assertEqual(script_res.metadata.program, None)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ScriptResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(len(list(cmp_res.logical_files)), 0)
        self.assertEqual(script_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata['Type'], 'Script')
        self.assertEqual(len(cmp_res.extra_metadata), 1)

    def test_migrate_script_resource_2(self):
        """
        Migrate a script resource that has partial resource specific metadata.
        """

        # create a script resource
        script_res = self._create_script_resource()
        self.assertEqual(ScriptResource.objects.count(), 1)
        # create script resource specific metadata
        script_res.metadata.create_element(element_model_name='ScriptSpecificMetadata')
        self.assertNotEqual(script_res.metadata.program, None)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ScriptResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(len(list(cmp_res.logical_files)), 0)
        self.assertEqual(script_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata['Type'], 'Script')
        self.assertEqual(cmp_res.extra_metadata['Programming Language'], 'R')
        self.assertEqual(cmp_res.extra_metadata['Script Version'], '1.0')
        self.assertEqual(len(cmp_res.extra_metadata), 3)

    def test_migrate_script_resource_3(self):
        """
        Migrate a script resource that has all resource specific metadata.
        """

        # create a script resource
        script_res = self._create_script_resource()
        self.assertEqual(ScriptResource.objects.count(), 1)
        # create script resource specific metadata
        script_res.metadata.create_element(element_model_name='ScriptSpecificMetadata', scriptLanguage='Python',
                                           languageVersion='3.5', scriptVersion='2.0',
                                           scriptDependencies='None', scriptReleaseDate='2022-12-01 00:00',
                                           scriptCodeRepository='http://www.google.com')
        self.assertNotEqual(script_res.metadata.program, None)
        # run  migration command
        call_command(self.migration_command)
        self.assertEqual(ScriptResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(len(list(cmp_res.logical_files)), 0)
        self.assertEqual(script_res.short_id, cmp_res.short_id)
        self.assertEqual(cmp_res.extra_metadata['Type'], 'Script')
        self.assertEqual(cmp_res.extra_metadata['Programming Language'], 'Python')
        self.assertEqual(cmp_res.extra_metadata['Programming Language Version'], '3.5')
        self.assertEqual(cmp_res.extra_metadata['Script Version'], '2.0')
        self.assertEqual(cmp_res.extra_metadata['Script Dependencies'], 'None')
        self.assertEqual(cmp_res.extra_metadata['Release Date'], '12-01-2022')
        self.assertEqual(cmp_res.extra_metadata['Script Repository'], 'http://www.google.com')
        self.assertEqual(len(cmp_res.extra_metadata), 7)

    def _create_script_resource(self, add_keywords=False):
        script_res = hydroshare.create_resource("ScriptResource", self.user, "Testing migrating to composite resource")
        if add_keywords:
            script_res.metadata.create_element('subject', value='kw-1')
            script_res.metadata.create_element('subject', value='kw-2')
        return script_res
