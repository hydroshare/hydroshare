from django.contrib.auth.models import Group
from django.test import TestCase

from mezzanine.generic.models import Rating

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestEndorseCommentAPI(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestEndorseCommentAPI, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_endorse_comment(self):
        # create a user to be used for creating the resource
        user_creator = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )
        user_commenter_1 = hydroshare.create_account(
            'commenter_1@usu.edu',
            username='commenter_1',
            first_name='Commenter_1_FirstName',
            last_name='Commenter_1_LastName',
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

        resource_2 = hydroshare.create_resource(
            'GenericResource',
            user_creator,
            'My 2nd Test Resource'
        )
        # first comment on resource
        comment_text = "comment by commenter_1"
        comment = hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_1)

        # at this point there should not be any ratings for this new comment
        ratings = Rating.objects.filter(object_pk=comment.id)
        self.assertEqual(len(ratings), 0)

        # rate the comment - this is the api call we are testing
        rating = hydroshare.endorse_comment(comment.id, new_resource.short_id, user_rater_1)
        self.assertEqual(rating.content_object, comment)
        self.assertEqual(rating.user, user_rater_1)
        # test that the rating value is 1 (+1)
        self.assertEqual(rating.value, 1)

        # at this point there should be one ratings for this comment
        ratings = Rating.objects.filter(object_pk=comment.id)
        # test that the rating value is 1 (+1)
        self.assertEqual(len(ratings), 1)

        # test the user can't rate the same comment twice - no new rating object is created
        rating = hydroshare.endorse_comment(comment.id, new_resource.short_id, user_rater_1)
        self.assertEqual(rating.content_object, comment)
        self.assertEqual(rating.user, user_rater_1)
        # test that the rating value is 1 (+1)
        self.assertEqual(rating.value, 1)

        # at this point there should be one ratings for this comment
        ratings = Rating.objects.filter(object_pk=comment.id)
        self.assertEqual(len(ratings), 1)
        # test that the rating value is 1 (+1)
        self.assertEqual(ratings[0].value, 1)

        # rate the same comment by another user- this is the api call we are testing
        rating = hydroshare.endorse_comment(comment.id, new_resource.short_id, user_rater_2)
        self.assertEqual(rating.content_object, comment)
        self.assertEqual(rating.user, user_rater_2)
        # test that the rating value is 1 (+1)
        self.assertEqual(rating.value, 1)

        # at this point there should be two ratings for this comment
        ratings = Rating.objects.filter(object_pk=comment.id)
        self.assertEqual(len(ratings), 2)
        # test that the rating value is 1 (+1) for each of these ratings
        self.assertEqual(ratings[0].value, 1)
        self.assertEqual(ratings[1].value, 1)

        # test removing a rating from a comment
        hydroshare.endorse_comment(comment.id, new_resource.short_id, user_rater_2, endorse=False)

        # at this point there should be one ratings for this comment
        ratings = Rating.objects.filter(object_pk=comment.id)
        self.assertEqual(len(ratings), 1)
        # test that the rating value is 1 (+1)
        self.assertEqual(ratings[0].value, 1)

        # there should not be any ratings by user_rater_2 for this comment
        ratings = Rating.objects.filter(object_pk=comment.id, user=user_rater_2)
        self.assertEqual(len(ratings), 0)

        # test that ValueError exception raised if the comment does not exist for the specified resource
        with self.assertRaises(ValueError):
            hydroshare.endorse_comment(comment.id, resource_2.short_id, user_rater_2)
