from django.test import TestCase
from hs_core.hydroshare import utils
from hs_core.models import BaseResource


class TestGetResourceTypesAPI(TestCase):
    def test_get_resource_types(self):
        # this is the api call we are testing
        res_types = utils.get_resource_types()

        # test that each resource type is a subclass of BaseResource type
        for res_type in res_types:
            self.assertEqual(issubclass(res_type, BaseResource), True)
