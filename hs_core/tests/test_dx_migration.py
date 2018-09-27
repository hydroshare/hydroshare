from django.apps import apps
from django.test import TestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from hs_core import hydroshare
from hs_core.models import Identifier, Group


class TestMigrations(TestCase):

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(
                type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class TestDelimiterMigration(TestMigrations):
    migrate_from = '0038_auto_20180831_2201'
    migrate_to = '0039_doi_url'

    def setUpBeforeMigration(self, apps):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )
        user.save()
        resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=user,
            title='My Test Raster Resource',
        )
        resource.save()
        id = Identifier.objects.all().first()
        id.url = "http://dx.doi.org/123"
        id.save()


    def test_delimiter_migration(self):
        id = Identifier.objects.all().first()
        self.assertEqual('https://doi.org/123', id.url)
