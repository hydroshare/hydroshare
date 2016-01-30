from django.contrib.auth.models import User, Group
from django.test import TestCase

from mezzanine.generic.models import Rating

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestEndorseResourceAPI(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestEndorseResourceAPI, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_endorse_resource(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        user_rater_1 = hydroshare.create_account(
            'rater_1@usu.edu',
            username='rater_1',
            first_name='Rater_1_FirstName',
            last_name='Rater_1_LastName',
            superuser=False,
            groups=[]
        )

        user_rater_2 = hydroshare.create_account(
            'rater_2@usu.edu',
            username='rater_2',
            first_name='Rater_2_FirstName',
            last_name='Rater_2_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        new_resource = hydroshare.create_resource(
            'GenericResource',
            user_creator,
            'My Test Resource'
        )

        # this is the api call we are testing
        rating = hydroshare.endorse_resource(new_resource.short_id, user_rater_1)
        self.assertEqual(rating.content_object, new_resource)
        self.assertEqual(rating.user, user_rater_1)
        self.assertEqual(rating.value, 1)
        # test that we have only one rating object for the given resource and given rater
        ratings = Rating.objects.filter(object_pk=new_resource.id, user=user_rater_1)
        self.assertEqual(len(ratings), 1)

        # test that a specific user can rate/endorse a resource only once
        rating = hydroshare.endorse_resource(new_resource.short_id, user_rater_1)
        self.assertEqual(rating.value, 1)
        ratings = Rating.objects.filter(object_pk=new_resource.id, user=user_rater_1)
        self.assertEqual(len(ratings), 1)
        self.assertEqual(ratings[0].value, 1)

        # test that a 2nd user can rate the same resource
        rating = hydroshare.endorse_resource(new_resource.short_id, user_rater_2)
        self.assertEqual(rating.content_object, new_resource)
        self.assertEqual(rating.user, user_rater_2)
        self.assertEqual(rating.value, 1)

        # test that we have two rating object for the given resource
        ratings = Rating.objects.filter(object_pk=new_resource.id)
        self.assertEqual(len(ratings), 2)

        # test removing endorsement - this is the api call we are testing
        hydroshare.endorse_resource(new_resource.short_id, user_rater_1, endorse=False)
        # test that we have no rating object for the given resource and given rater
        ratings = Rating.objects.filter(object_pk=new_resource.id, user=user_rater_1)
        self.assertEqual(len(ratings), 0)
