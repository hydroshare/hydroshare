__author__ = 'Tian Gan'

# unit test for get_endorsement() from social.py

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestGetEndorsements(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetEndorsements, self).setUp()
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

        # create comment from user 2
        self.comment = hydroshare.comment_on_resource(self.res.short_id, "comment by user2", user=self.user2)

        # endorse resource
        self.endorse1_res = hydroshare.endorse_resource(self.res.short_id, self.user2)
        self.endorse2_res = hydroshare.endorse_resource(self.res.short_id, self.user1)

        # endorse comment
        self.endorse1_com = hydroshare.endorse_comment(self.comment.id, self.res.short_id, self.user1)
        self.endorse2_com = hydroshare.endorse_comment(self.comment.id, self.res.short_id, self.user2)

    def test_get_endorsements(self):
        # test get the endorsement of resource
        self.assertEqual(
            len(hydroshare.get_endorsements(self.res)), 2,
            'Rating number for resource is not correct'
        )

        # test the user endorse on resource
        self.assertListEqual(
            [hydroshare.get_endorsements(self.res)[0].user, hydroshare.get_endorsements(self.res)[1].user],
            [self.user2, self.user1],
            'Resource Rating user is not correct'
        )

        # test the endorsement points to the correct resource
        self.assertEqual(
            hydroshare.get_endorsements(self.res)[0].content_object,
            self.res,
            'The endorsement are not pointing to the correct resource'
        )

        # test get the endorsement of comment
        self.assertEqual(
            len(hydroshare.get_endorsements(self.comment)), 2,
            'Rating number for comment is not correct')

        # test the user endorse on comment
        self.assertListEqual(
            [hydroshare.get_endorsements(self.comment)[0].user, hydroshare.get_endorsements(self.comment)[1].user],
            [self.user1, self.user2],
            'Comment Rating user is not correct'
        )

        # test the endorsement points to the correct comment
        self.assertEqual(
            hydroshare.get_endorsements(self.comment)[0].content_object,
            self.comment,
            'The endorsement are not pointing to the correct comment'
        )