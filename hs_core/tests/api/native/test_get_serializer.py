__author__ = 'Luk'

from unittest import TestCase
from hs_core.hydroshare import utils
from hs_core.models import GenericResource
from django.contrib.auth.models import  User
import importlib


class TestGetSerializer(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()
        pass

    def test_get_serializer(self):
        #create a user, and a resource
        self.user = User.objects.create_user('user', email='user@test.com')
        self.res = GenericResource.objects.create(
            user=self.user,
            title='resource',
            creator=self.user
        )

        #Manually create a serializer
        tastypie_module = self.res._meta.app_label + '.api'        # the module name should follow this convention
        tastypie_name = self.res._meta.object_name + 'Resource'    # the classname of the Resource seralizer
        tastypie_api = importlib.import_module(tastypie_module)    # import the module
        serializer = getattr(tastypie_api, tastypie_name)()        # make an instance of the tastypie resource

        #Compare if they are the same
        self.assertNotEqual(utils.get_serializer(self.res), serializer)










