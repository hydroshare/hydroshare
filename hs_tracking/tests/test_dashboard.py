from django.test import TestCase
from django.contrib.auth.models import Group
from hs_tracking.models import Variable
from hs_core import hydroshare
from rest_framework import status
import socket
from django.test import Client


class TestDashboard(TestCase):

    def setUp(self):
        self.hostname = socket.gethostname()
        self.resource_url = "/resource/{res_id}/"
        self.client = Client(HTTP_USER_AGENT='Mozilla/5.0')  # fake use of a real browser

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            password='foobar',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        # set up a logged-in session
        # self.client.force_authenticate(user=self.dog)
        self.client.login(username='dog', password='foobar')

        self.resources_to_delete = []
        self.groups_to_delete = []

        self.holes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about dog holes',
            metadata=[],
        )

        self.resources_to_delete.append(self.holes.short_id)

        self.squirrels = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='where to find squirrels',
            metadata=[],
        )

        self.resources_to_delete.append(self.squirrels.short_id)

    def tearDown(self):
        for r in self.resources_to_delete:
            hydroshare.delete_resource(r)
        for g in self.groups_to_delete:
            g.delete()
        self.dog.delete()

    def test_blank(self):
        """ nothing in tracking database at beginning """

        stuff = Variable.recent_resources(self.dog)
        self.assertEqual(stuff.count(), 0)

    def test_view(self):
        """ a view gets recorded """

        response = self.client.get(self.resource_url.format(res_id=self.holes.short_id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stuff = Variable.recent_resources(self.dog)
        self.assertEqual(stuff.count(), 1)
        r = stuff[0]
        self.assertEqual(r.short_id, self.holes.short_id)
        self.assertEqual(r.public, False)
        self.assertEqual(r.published, False)
        self.assertEqual(r.discoverable, False)

        # there's only one record!
        stuff = Variable.objects.filter(resource=self.holes)
        one = stuff[0]
        # the record describes the request above
        self.assertEqual(one.last_resource_id, self.holes.short_id)
        self.assertEqual(one.landing, True)
        self.assertEqual(one.rest, False)
