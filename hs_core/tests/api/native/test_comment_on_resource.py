from django.contrib.auth.models import Group
from django.test import TestCase

from mezzanine.generic.models import ThreadedComment

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestCommentOnResourceAPI(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCommentOnResourceAPI, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def test_comment_on_resource(self):
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
        user_commenter_2 = hydroshare.create_account(
            'commenter_2@usu.edu',
            username='commenter_2',
            first_name='Commenter_2_FirstName',
            last_name='Commenter_2_LastName',
            superuser=False,
            groups=[]
        )

        user_commenter_3 = hydroshare.create_account(
            'commenter_3@usu.edu',
            username='commenter_3',
            first_name='Commenter_3_FirstName',
            last_name='Commenter_3_LastName',
            superuser=False,
            groups=[]
        )
        # create a resource
        new_resource = hydroshare.create_resource(
            'GenericResource',
            user_creator,
            'My Test Resource'
        )

        new_resource_2 = hydroshare.create_resource(
            'GenericResource',
            user_creator,
            'My Test Resource 2'
        )

        # test at this point we have no comments
        comments_count = ThreadedComment.objects.all().count()
        self.assertEqual(comments_count, 0)

        comment_text = "comment by commenter_1"

        # this is the api we are testing
        comment = hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_1)

        # test at this point we have one comment
        comments_count = ThreadedComment.objects.all().count()
        self.assertEqual(comments_count, 1)
        self.assertEqual(comment.content_object, new_resource)
        self.assertEqual(comment.user, user_commenter_1)
        self.assertEqual(comment.comment, comment_text)

        # test this the lead comment
        self.assertEqual(comment.replied_to, None)

        # let the commenter-2 reply to the comment by commenter-1
        comment_text = "reply comment by commenter_2"

        # this is the api we are testing
        reply_comment = hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_2,
                                                       in_reply_to=comment.id)

        # test at this point we have 2 comment
        comments_count = ThreadedComment.objects.all().count()
        self.assertEqual(comments_count, 2)
        self.assertEqual(reply_comment.content_object, new_resource)
        self.assertEqual(reply_comment.user, user_commenter_2)
        self.assertEqual(reply_comment.comment, comment_text)
        self.assertEqual(reply_comment.replied_to, comment)
        self.assertTrue( reply_comment.submit_date > comment.submit_date)

        # test this the lead comment
        self.assertEqual(comment.replied_to, None)

        # test that we can reply to the same comment twice
        comment_text = "reply comment by commenter_3"
        reply_comment = hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_3,
                                                       in_reply_to=comment.id)
        # test at this point we have 3 comment
        comments_count = ThreadedComment.objects.all().count()
        self.assertEqual(comments_count, 3)
        self.assertEqual(reply_comment.content_object, new_resource)
        self.assertEqual(reply_comment.user, user_commenter_3)
        self.assertEqual(reply_comment.comment, comment_text)
        self.assertEqual(reply_comment.replied_to, comment)
        self.assertTrue(reply_comment.submit_date > comment.submit_date)

        # test this the lead comment
        self.assertEqual(comment.replied_to, None)

        # test that the same user can comment on the same resource more than once
        comment_text = "another comment by commenter_1"
        comment = hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_1)
        # test at this point we have 4 comment
        comments_count = ThreadedComment.objects.all().count()
        self.assertEqual(comments_count, 4)
        self.assertEqual(comment.content_object, new_resource)
        self.assertEqual(comment.user, user_commenter_1)
        self.assertEqual(comment.comment, comment_text)
        # test this the lead comment
        self.assertEqual(comment.replied_to, None)

        # test that one can't reply to his/her own comment
        comment_text = "reply to my own comment by commenter_1"
        with self.assertRaises(ValueError):
            hydroshare.comment_on_resource(new_resource.short_id, comment_text, user=user_commenter_1,
                                           in_reply_to=comment.id)

        # test that reply_to comment must exists for the given resource otherwise it raises value error
        with self.assertRaises(ValueError):
            hydroshare.comment_on_resource(new_resource_2.short_id, comment_text, user=user_commenter_2,
                                           in_reply_to=comment.id)
