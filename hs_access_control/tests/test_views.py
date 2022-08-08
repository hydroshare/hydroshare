from django.test import TestCase, Client
from django.contrib.auth.models import Group

from hs_access_control.models import Community
from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set
from hs_access_control.views import user_json
from hs_core import hydroshare
from django.urls import reverse
import json


class TestViews(TestCase):

    def setUp(self):
        super(TestViews, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )
        self.admin.set_password('passwordsarestupid')
        self.admin.save()

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )
        self.cat.set_password('adumbpassword')
        self.cat.save()

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little doggy',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )
        self.dog.set_password('anotherpassword')
        self.dog.save()

        # user 'cat' creates a new group called 'cats'
        self.cats = self.cat.uaccess.create_group(
            title='cats',
            description="This is the cats group",
            purpose="Our purpose to collaborate on acting aloof.")

        # user 'dog' creates a new group called 'dogs'
        self.dogs = self.dog.uaccess.create_group(
            title='dogs',
            description="This is the dogs group",
            purpose="Our purpose is to collaborate on digging up grass.")

        # community to use
        self.pets = self.cat.uaccess.create_community(
                'all kinds of pets',
                'collaboration on how to be a more effective pet.')

        # client connection: not authenticated yet
        self.client = Client()

    def test_community_not_authenticated(self):
        " try using the system unauthenticated "
        url = reverse('access_manage_community', kwargs={'cid': self.pets.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "You must be logged in to access this function.")

    def test_community_wrong_owner(self):
        " try accessing a community without being an owner "
        self.client.login(username='dog', password='anotherpassword')
        url = reverse('access_manage_community', kwargs={'cid': self.pets.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "user 'dog' does not own community 'all kinds of pets'")

    def test_community_list(self):
        " list a community "

        self.client.login(username='cat', password='adumbpassword')

        url = reverse('access_manage_community', kwargs={'cid': self.pets.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], '')
        self.assertEqual(json_response['community']['name'], 'all kinds of pets')
        self.assertEqual(json_response['community']['owners'], [user_json(self.cat)])
        self.assertEqual(json_response['approvals'], [])
        self.assertEqual(json_response['pending'], [])
        self.assertEqual(json_response['they_declined'], [])
        self.assertEqual(json_response['we_declined'], [])

    def test_community_add_owner(self):
        " add an owner to a community "
        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.dog.username,
                              'action': 'owner',
                              'addrem': 'add'})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        owners = [x['username'] for x in json_response['community']['owners']]
        self.assertTrue(is_equal_to_as_set(owners, ['cat', 'dog']))

    def test_community_change_owner(self):
        " add a new owner and remove self as owner "
        self.client.login(username='cat', password='adumbpassword')

        # add dog as an owner.
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.dog.username,
                              'action': 'owner',
                              'addrem': 'add'})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        owners = [x['username'] for x in json_response['community']['owners']]
        self.assertTrue(is_equal_to_as_set(owners, ['cat', 'dog']))

        # now remove self as an owner.
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': 'owner',
                              'addrem': 'remove'})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        owners = [x['username'] for x in json_response['community']['owners']]
        self.assertTrue(is_equal_to_as_set(owners, ['dog']))

    def test_community_remove_sole_owner(self):
        " prevent removing the sole owner "
        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': 'owner',
                              'addrem': 'remove'})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], "Cannot remove last owner 'cat' of community")

    def test_community_add_existing_owner(self):
        " try to add an owner who already owns the community "
        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': 'owner',
                              'addrem': 'add'})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], "user 'cat' already owns community")

    def test_community_add_group_automatically(self):
        " add a group automatically to a community "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.cats.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        members = [x['name'] for x in json_response['members']]
        self.assertTrue(is_equal_to_as_set(members, ['cats']))

    def test_community_add_group_and_remove(self):
        " add a group automatically to a community "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        members = [x['name'] for x in json_response['members']]
        self.assertTrue(is_equal_to_as_set(members, ['cats']))

        # now remove the group from the community
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "remove",
                              "gid": self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        members = [x['name'] for x in json_response['members']]
        self.assertTrue(is_equal_to_as_set(members, []))

    def test_community_invite_group_deferred(self):
        " invite a group to a community with deferral "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        pending = [x['group']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['dogs']))

    def test_community_invite_group_not_owner(self):
        " prohibit invitations from non-owners "
        self.client.login(username='dog', password='anotherpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "user 'dog' does not own community 'all kinds of pets'")

    def test_community_invite_group_and_retract(self):
        " invite a group and retract the invitation "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        pending = [x['group']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['dogs']))

        # now retract the invitation
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "retract",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        pending = [x['group']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))

    def test_community_invite_group_and_accept(self):
        " invite a group to a community and group accepts "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)

        json_response = json.loads(result.content)
        pending = [x['group']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['dogs']))

        # become the owner of dogs
        self.client.login(username='dog', password='anotherpassword')

        # check the status of the invitation:
        url = reverse("access_manage_group",
                      kwargs={'gid': self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # request is pending
        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, ['all kinds of pets']))
        # we haven't joined the community yet.
        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, []))

        # now accept the invitation
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "approve",
                              "gid": self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # nothing is pending
        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, []))
        # we joined the community
        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, ['all kinds of pets']))

    def test_community_invite_group_and_decline(self):
        " invite a group to a community and group accepts "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "invite",
                              "gid": self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)

        json_response = json.loads(result.content)
        pending = [x['group']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['dogs']))

        # become the owner of dogs
        self.client.login(username='dog', password='anotherpassword')

        # check the status of the invitation:
        url = reverse("access_manage_group",
                      kwargs={'gid': self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # request is pending
        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, ['all kinds of pets']))
        # we haven't joined the community yet.
        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, []))

        # now decline the invitation
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "decline",
                              "gid": self.dogs.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # nothing is pending
        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, []))

        # we did not join the community
        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, []))

        # we declined this invitation
        we_declined = [x['community']['name'] for x in json_response['we_declined']]
        self.assertTrue(is_equal_to_as_set(we_declined, ['all kinds of pets']))

    def test_group_not_authenticated(self):
        " try using the system unauthenticated on a group "
        url = reverse('access_manage_group', kwargs={'gid': self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "You must be logged in to access this function.")

    def test_group_wrong_owner(self):
        " try accessing a group without being an owner "
        self.client.login(username='dog', password='anotherpassword')
        url = reverse('access_manage_group', kwargs={'gid': self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 404)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "user 'dog' does not own group 'cats'")

    def test_group_list(self):
        " list a group "

        self.client.login(username='cat', password='adumbpassword')

        url = reverse('access_manage_group', kwargs={'gid': self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], '')
        self.assertEqual(json_response['group']['name'], 'cats')
        self.assertEqual(json_response['group']['owners'], [user_json(self.cat)])
        self.assertEqual(json_response['approvals'], [])
        self.assertEqual(json_response['pending'], [])
        self.assertEqual(json_response['they_declined'], [])
        self.assertEqual(json_response['we_declined'], [])

    def test_group_add_community_automatically(self):
        " add a group automatically to a community "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.cats.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, ['all kinds of pets']))

    def test_group_add_community_and_remove(self):
        " add a group automatically to a community "
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, ['all kinds of pets']))

        # now leave the community
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "leave",
                              "gid": self.cats.id})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, []))

    def test_group_join_community_deferred(self):
        " request joining a community with deferral "
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        pending = [x['community']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['all kinds of pets']))

    def test_group_join_community_deferred_and_accept(self):
        " request joining a community with deferral and accept "
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        pending = [x['community']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['all kinds of pets']))

        # login as community owner
        self.client.login(username='cat', password='adumbpassword')

        # check that a request is pending
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, ['all kinds of pets']))

        # approve that request
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "approve",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, []))

        members = [x['name'] for x in json_response['members']]
        self.assertTrue(is_equal_to_as_set(members, ['dogs']))

    def test_group_join_community_deferred_and_decline(self):
        " request joining a community with deferral and decline"
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        pending = [x['community']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['all kinds of pets']))

        # login as community owner
        self.client.login(username='cat', password='adumbpassword')

        # check that a request is pending
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, ['all kinds of pets']))

        # decline that request
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": "decline",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, []))

        we_declined = [x['community']['name'] for x in json_response['we_declined']]
        self.assertTrue(is_equal_to_as_set(we_declined, ['all kinds of pets']))

        members = [x['name'] for x in json_response['members']]
        self.assertTrue(is_equal_to_as_set(members, []))

    def test_group_join_community_deferred_and_retract(self):
        " request joining a community with deferral and retract the request "
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "join",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        pending = [x['community']['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['all kinds of pets']))

        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": "retract",
                              "gid": self.dogs.id})

        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        approvals = [x['community']['name'] for x in json_response['approvals']]
        self.assertTrue(is_equal_to_as_set(approvals, []))

        joined = [x['name'] for x in json_response['joined']]
        self.assertTrue(is_equal_to_as_set(joined, []))

    ########################
    # community creation
    ########################
    def test_community_request_not_logged_in(self):
        " catch users who are not logged in "

        url = reverse("access_manage_crequests")
        result = self.client.post(url)
        self.assertEqual(result.status_code, 404)

        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "You must be logged in to access this function.")

    def test_community_request_logged_in(self):
        " list community requests for to a regular user "
        self.client.login(username='dog', password='anotherpassword')

        url = reverse("access_manage_crequests")
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertTrue(is_equal_to_as_set(json_response['pending'], []))
        self.assertTrue(is_equal_to_as_set(json_response['approved'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))

    def test_community_request_logged_in_admin(self):
        " list community requests for to a regular user "
        self.client.login(username='admin', password='passwordsarestupid')

        url = reverse("access_manage_crequests")
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertTrue(is_equal_to_as_set(json_response['pending'], []))
        self.assertTrue(is_equal_to_as_set(json_response['approved'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))

    def test_community_request_entry(self):
        " enter a request for a regular user "
        self.client.login(username='dog', password='anotherpassword')

        url = reverse("access_manage_crequests", kwargs={"action": "request"})
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News thats fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "",
            "closed": False,
            "owner": "dog"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        self.assertTrue(is_equal_to_as_set(json_response['approved'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))
        self.assertEqual(json_response['request']['name'], "Fake news")

        pending = [x['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ["Fake news"]))

    def test_community_edit_request(self):
        " admin edits a request without approval "
        self.client.login(username='dog', password='anotherpassword')

        url = reverse("access_manage_crequests", kwargs={"action": "request"})
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News thats fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "",
            "closed": False,
            "owner": "dog"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        self.assertTrue(is_equal_to_as_set(json_response['approved'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))
        self.assertEqual(json_response['request']['name'], "Fake news")

        pending = [x['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ["Fake news"]))
        crid = json_response['request']['id']

        # now approve the request as admin
        self.client.login(username='admin', password='passwordsarestupid')

        url = reverse("access_manage_crequests", kwargs={"action": "request", "crid": crid})
        result = self.client.post(url, {
            "name": "Real news",
            "description": "News thats fit for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "",
            "closed": False,
            "owner": "dog"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        pending = [x['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ['Real news']))
        approved = [x['name'] for x in json_response['approved']]
        self.assertTrue(is_equal_to_as_set(approved, []))

    def test_community_approve_request(self):
        " approve a request for a regular user "
        self.client.login(username='dog', password='anotherpassword')

        # create a request to approve
        url = reverse("access_manage_crequests", kwargs={"action": "request"})
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News thats fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "",
            "closed": False,
            "owner": "dog"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        self.assertTrue(is_equal_to_as_set(json_response['approved'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))
        self.assertEqual(json_response['request']['name'], "Fake news")

        pending = [x['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, ["Fake news"]))
        crid = json_response['request']['id']

        # now approve the request as admin
        self.client.login(username='admin', password='passwordsarestupid')

        url = reverse("access_manage_crequests", kwargs={"action": "approve", "crid": crid})
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News thats fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "",
            "closed": False,
            "owner": "dog"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # There should be a community now.
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 1)

        pending = [x['name'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))
        approved = [x['name'] for x in json_response['approved']]
        self.assertTrue(is_equal_to_as_set(approved, ["Fake news"]))
