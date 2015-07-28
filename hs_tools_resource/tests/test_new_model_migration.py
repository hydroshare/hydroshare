import urllib
import logging

from django.test import Client, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

from hs_core import hydroshare
from hs_core.models import GenericResource

from hs_tools_resource.models import ToolResource
from decimal import Decimal


class TestMigrations(TransactionTestCase):

    @property
    def app(self):
        return __name__.split('.')[1]

    migrate_from = '0003_auto_20150724_1501'
    migrate_to = '0004_auto_20150724_1423'

    def setUp(self):
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        # setUp

        # Run the migration to test
        executor.migrate(self.migrate_to)

    def test_test(self):
        assert False
        # tests
