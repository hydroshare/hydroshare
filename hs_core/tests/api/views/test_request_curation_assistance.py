import json

from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_core.views import request_curation_assistance


class TestRequestCurationAssistance(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestRequestCurationAssistance, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.owner = hydroshare.create_account(
            'owner@example.com',
            username='curation_owner',
            first_name='Owner',
            last_name='User',
            superuser=False,
            groups=[self.group]
        )
        self.viewer = hydroshare.create_account(
            'viewer@example.com',
            username='curation_viewer',
            first_name='Viewer',
            last_name='User',
            superuser=False,
            groups=[self.group]
        )
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Curation Assistance Test'
        )
        self.owner.uaccess.share_resource_with_user(self.res, self.viewer, PrivilegeCodes.VIEW)
        self.url = reverse('request_curation_assistance', kwargs={'shortkey': self.res.short_id})

    def _post(self, user):
        request = self.factory.post(self.url)
        request.user = user
        return request_curation_assistance(request, shortkey=self.res.short_id)

    def test_owner_request_sends_email_to_support(self):
        response = self._post(self.owner)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.res.title, email.subject)
        self.assertIn(self.res.short_id, email.body)
        self.assertEqual(email.extra_headers['Reply-To'], self.owner.email)

    def test_get_not_allowed(self):
        request = self.factory.get(self.url)
        request.user = self.owner
        response = request_curation_assistance(request, shortkey=self.res.short_id)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(len(mail.outbox), 0)

    def test_non_owner_denied(self):
        with self.assertRaises(PermissionDenied):
            self._post(self.viewer)
        self.assertEqual(len(mail.outbox), 0)

    def test_review_pending_rejected(self):
        self.res.raccess.review_pending = True
        self.res.raccess.save()

        response = self._post(self.owner)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_web_app_resource_not_eligible(self):
        web_app = hydroshare.create_resource(
            resource_type='ToolResource',
            owner=self.owner,
            title='Curation Assistance Web App'
        )

        self.assertTrue(self.res.can_request_curation_assistance)
        self.assertFalse(web_app.can_request_curation_assistance)
