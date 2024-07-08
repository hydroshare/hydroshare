# run with: python manage.py test hs_core.tests.serialization.test_generic_resource_meta
import unittest

from django.conf import settings


class TestGenericResourceMeta(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_yaml_into_settings(self):
        typeof = type(settings.EXTERNAL_CONFIG)
        return self.assertEqual(typeof, dict)

    def test_read_yaml_into_settings_select_values(self):
        # Testing local configuration and
        self.assertEqual(type(settings.EXTERNAL_CONFIG["HS_PATH"]), str)
        self.assertEqual(type(settings.EXTERNAL_CONFIG["HS_DATABASE"]), str)
        self.assertEqual(type(settings.EXTERNAL_CONFIG["HS_LOG_FILES"]), str)
        self.assertEqual(type(settings.EXTERNAL_CONFIG["HS_SERVICE_UID"]), int)
        self.assertEqual(type(settings.EXTERNAL_CONFIG["HS_SERVICE_GID"]), int)

        # Testing deployment options
        self.assertEqual(type(settings.EXTERNAL_CONFIG["USE_SECURITY"]), bool)
        self.assertEqual(type(settings.EXTERNAL_CONFIG["USE_HTTP_AUTH"]), bool)

        # Testing one that doesnt exist
        self.assertEqual(type(settings.EXTERNAL_CONFIG.get("NONEXISTANT")), type(None))
