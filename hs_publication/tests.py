from django.contrib.auth.models import Group, User

from django.core import mail
from django.test import TestCase

from hs_core.models import BaseResource

from hs_publication import tasks, utils
from hs_publication.models import PublicationQueue

class PublicationQueueNotificationEmailTestCase(TestCase):
    def setUp(self):
        group = Group.objects.create(name="Publication Review")
        user1 = User.objects.create_user(username='user1',
                                 email='user1@example.com')
        user2 = User.objects.create_user(username='user2',
                                 email='user2@example.com')
        group.user_set.add(user1)
        group.user_set.add(user2)

        resource = BaseResource.objects.create(creator_id=user1.id,
                                               user_id=user1.id)

        self.pq1 = PublicationQueue.objects.create(resource=resource, status="pending")
        pq2 = PublicationQueue.objects.create(resource=resource, status="approved")
        pq3 = PublicationQueue.objects.create(resource=resource, status="pending")
        pq4 = PublicationQueue.objects.create(resource=resource, status="denied")
        pq5 = PublicationQueue.objects.create(resource=resource, status="pending")

    def test_send_notification_email_task(self):
        tasks.send_notification_email()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 2)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, '3 Publication Queue Items Need Review')

    def test_send_update_email_task(self):
        self.pq1.status="approved"
        self.pq1.note="Looks good!"
        self.pq1.save()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].body, 'The current status is: approved\nThe reason:\nLooks good!')
