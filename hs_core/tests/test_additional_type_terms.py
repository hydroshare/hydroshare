import json
import re
from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase, Client

from hs_core import hydroshare
from hs_core.hydroshare_schemaorg_adapter import CONTENT_TYPE_TO_TERM
from hs_file_types.models import base
from hs_file_types import models as file_types


class TestAdditionalTypeTerms(TestCase):
    def _logical_file_classes(self):
        return [getattr(file_types, n) for n in dir(file_types)
                if n.endswith("LogicalFile") and n != "AbstractLogicalFile"]

    def test_mapping_covers_every_logical_file_class(self):
        classes = self._logical_file_classes()
        self.assertTrue(classes)
        for cls in classes:
            self.assertIn(cls.type_name(), CONTENT_TYPE_TO_TERM, cls.__name__)
            self.assertEqual(CONTENT_TYPE_TO_TERM[cls.type_name()], cls.get_aggregation_type_name())
        self.assertTrue(issubclass(classes[0], base.AbstractLogicalFile))

    def test_terms_page_documents_every_term(self):
        response = Client().get("/terms/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for term in set(CONTENT_TYPE_TO_TERM.values()):
            anchor = re.sub(r'^[A-Z]+(?=[A-Z][a-z])|^[A-Z]', lambda m: m.group().lower(), term)
            self.assertIn(f'name="{anchor}"', content, term)
            self.assertIn(f"hydroshare.org/terms/{term}<", content, term)


class TestUserMetadataJsonAdditionalType(TestCase):
    """The user_metadata.json written to S3 carries additionalType term URLs and unchanged content_types."""

    def setUp(self):
        group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'at_user@email.com', username='atuser', first_name='A', last_name='T',
            superuser=False, groups=[group])
        self.resource = hydroshare.create_resource(
            resource_type='CompositeResource', owner=self.user, title='additionalType test')

    def tearDown(self):
        self.resource.delete()
        self.user.delete()

    def test_written_json(self):
        written = {}

        def fake_save(path, name):
            with open(path) as f:
                written[name] = json.load(f)

        storage = mock.Mock()
        storage.saveFile.side_effect = fake_save
        with mock.patch.object(type(self.resource), 'get_s3_storage', return_value=storage):
            self.resource.write_user_metadata_json_file()
        doc = written[f"{self.resource.short_id}/.hsmetadata/user_metadata.json"]
        self.assertEqual(doc["content_types"], ["CompositeResource"])
        self.assertEqual(doc["additionalType"], ["https://www.hydroshare.org/terms/CompositeResource"])
