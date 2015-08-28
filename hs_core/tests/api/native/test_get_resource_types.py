__author__ = 'Pabitra'

import unittest

from django.test import TestCase
from hs_core import hydroshare
from hs_core.models import AbstractResource
from hs_core.hydroshare import resource, users
from django.contrib.auth.models import User, Group

class TestGetResourceTypesAPI(TestCase):

    def setUp(self):

        #fig run --rm hydroshare python manage.py test hs_core.tests.api.native.test_get_resource_types:TestGetResourceTypesAPI.test_get_resource_types

        pass

    def tearDown(self):
        pass

    def test_get_resource_types(self):


        # this is the api call we are testing
        res_types = hydroshare.get_resource_types()


        # test that each resource type is a subclass of AbstractResource type
        for res_type in res_types:
            self.assertEqual(issubclass(res_type, AbstractResource), True)

    @unittest.skip
    def test_get_resources_by_type(self):
        # This tests the ability to filter resources by type
        # Note: print statements are for debugging assertion failures only

        print '**********************\n' * 5
        print '******* STDOUT *******'
        print '**********************\n' * 5

        group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        print 'Created Group : '+str(group)

        # create a user
        user = users.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[group])

        # get the user's id
        userid = User.objects.get(username=user).pk
        print 'UserID : '+ str(userid)

        group = users.create_group('MyGroup',members=[user],owners=[user])
        print 'Assigned User To Group'

        # create a generic resource
        new_res = resource.create_resource(
            'GenericResource',user,'My Test GenericResource Resource')
        pid = new_res.short_id
        print 'Created GenericResource, PID : '+str(pid)

        # create a raster resource
        new_res = resource.create_resource(
            'RefTimeSeries',user,'My Test RefTimeSeries Resource')
        pid = new_res.short_id
        print 'Created RefTimeSeries 1, PID : '+str(pid)

        # create a raster resource
        new_res = resource.create_resource(
            'RefTimeSeries',user,'My Test RefTimeSeries Resource2')
        pid = new_res.short_id
        print 'Created RefTimeSeries 2, PID : '+str(pid)

        # create a rhyssys resource
        new_res = resource.create_resource(
            'InstResource',user,'My Test InstResource Resource')
        pid = new_res.short_id
        print 'Created InstResource, PID : '+str(pid)

        res_types_all = hydroshare.get_resource_list(user=user)

        print '\nQuery All Resources: '
        print 'Resource Type \t:\t Number of Resources Found'
        print '------------- \t:\t -------------------------'
        for k,v in res_types_all.iteritems():
            print k.__name__+ '\t:\t '+ str(len(res_types_all[k]))

        res_names = [r.__name__ for r in res_types_all]
        self.assertTrue('GenericResource' in res_names)
        self.assertTrue('RefTimeSeries' in res_names)
        self.assertTrue('InstResource' in res_names)

        res_types_one = hydroshare.get_resource_list(
            user=user,types=['GenericResource'])

        print '\nQuery One Resource: '
        print 'Resource Type \t:\t Number of Resources Found'
        print '------------- \t:\t -------------------------'
        for k,v in res_types_one.iteritems():
            print k.__name__+ '\t:\t '+ str(len(res_types_one[k]))

        res_names = [r.__name__ for r in res_types_one]
        self.assertTrue('GenericResource' in res_names)
        self.assertTrue('RefTimeSeries' not in res_names)
        self.assertTrue('InstResource' not in res_names)

        res_types_multiple = hydroshare.get_resource_list(
            user=user,types=['GenericResource','RefTimeSeries'])

        print '\nQuery Multiple Resources: '
        print 'Resource Type \t:\t Number of Resources Found'
        print '------------- \t:\t -------------------------'
        for k,v in res_types_multiple.iteritems():
            print k.__name__+ '\t:\t '+ str(len(res_types_multiple[k]))

        res_names = [r.__name__ for r in res_types_multiple]
        self.assertTrue('GenericResource' in res_names)
        self.assertTrue('RefTimeSeries' in res_names)
        self.assertTrue('InstResource' not in res_names)


        # delete the resource
        resource.delete_resource(pid)

