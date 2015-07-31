import urllib
import logging

from django.test import Client, TransactionTestCase
from django.contrib.auth.models import User, Group
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

from hs_core import hydroshare
from hs_core.models import GenericResource

from hs_tools_resource.models import ToolResource, OldToolResource
from decimal import Decimal


class TestMigrations(TransactionTestCase):

    @property
    def app(self):
        return self.__class__.__module__.split('.')[1]

    def setUp(self):
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_state = executor.loader.project_state(self.migrate_from)
        old_state.render()
        new_state = executor.loader.project_state(self.migrate_to)
        new_state.render()
        self.old_apps = old_state.apps
        self.new_apps = new_state.apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        # setUp
        self.setUpBetweenMigrations()

        # Run the migration to test
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)


class TestToolBaseMigrations(TestMigrations):
    migrate_from = '0003_auto_20150724_1501'
    migrate_to = '0004_auto_20150724_1423'

    def setUpBetweenMigrations(self):
        #site = self.old_apps.get_model('sites.Site').objects.first()
        owner = User.objects.create(
            username="owner",
            email="owner@example.com",
            first_name="owner",
            last_name="of things",
        )
        #ToolResource = self.old_apps.get_model('hs_tools_resource.OldToolResource')
        self.tool_res = OldToolResource.objects.create(
            # site=site,
            creator=owner,
            user=owner,
            last_changed_by=owner,
            in_menus=[],
            title="Old Tool Resource",
        )

    def test_test(self):
        #new_tool_res = self.tool_res.copy_to_new_model()
        new_tool_res = self.new_apps.get_model('hs_tools_resource', 'ToolResource').objects.all()[0]
        self.assertEqual('ToolResource', new_tool_res.resource_type)
