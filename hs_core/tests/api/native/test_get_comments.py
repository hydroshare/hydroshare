__author__ = 'Tian Gan'

# unit test for get_comments() from social.py

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetComments(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetComments, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create 2 users
        self.user1 = hydroshare.create_account(
            'user1@gmail.com',
            username='user1',
            first_name='user1_first',
            last_name='user1_last',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'user2@gmail.com',
            username='user2',
            first_name='user2_first',
            last_name='user2_last',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user1,
            'My Test Resource'
        )

        # create comment1 from user 2
        self.comment_1 = hydroshare.comment_on_resource(self.res.short_id,
                                                        "comment1 by user2",
                                                        user=self.user2)

        # create comment2 to reply comment 1 from user 1
        self.comment_2 = hydroshare.comment_on_resource(self.res.short_id,
                                                        "comment2 to reply comment1 by user1",
                                                        user=self.user1,
                                                        in_reply_to=self.comment_1.pk)

        # create comment3 from user 2 to reply comment 2 from user 2
        self.comment_3 = hydroshare.comment_on_resource(self.res.short_id,
                                                        "comment3 to reply comment 2 by user2",
                                                        user=self.user2,
                                                        in_reply_to=self.comment_2.pk)

    def test_get_comments(self):
        # this is the api call we are testing
        res_comments = hydroshare.get_comments(self.res.short_id)

        # test the length of the comments
        self.assertEqual(len(res_comments), 3, 'Do not get all the comments')

        # test if the comments has the corresponding user
        self.assertEqual(res_comments[0].user, self.user2, 'The user info of the comment is not correct')

        # test if the comment text match
        self.assertEqual(res_comments[0].comment, self.comment_1.comment, 'The comment text is not correct')

        # test comment relationship
        self.assertEqual(res_comments[0].id, res_comments[1].replied_to_id, 'The comment relationship is not correct')

        # test comment is pointing to the correct resource
        self.assertEqual(res_comments[2].content_object, self.res, 'The comment does not point to the right resource')

