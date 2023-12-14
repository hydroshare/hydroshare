import json

from django.contrib.auth.models import Group
from django.test import Client, TransactionTestCase
from django.urls import reverse

from hs_access_control.models import Community, GroupCommunityRequest
from hs_access_control.models.community import RequestCommunity
from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set
from hs_core import hydroshare
from ..enums import CommunityActions, CommunityRequestActions


class TestViews(TransactionTestCase):

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

        self.pets.active = True
        self.pets.save()
        # client connection: not authenticated yet
        self.client = Client()

    #######################
    # Community management
    #######################

    def test_community_add_owner(self):
        """ add an owner to a community """
        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.dog.username,
                              'action': CommunityActions.OWNER.value,
                              'addrem': CommunityActions.ADD.value})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)

    def test_community_change_owner(self):
        """ add a new owner and remove self as owner """
        self.client.login(username='cat', password='adumbpassword')

        # add dog as an owner.
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.dog.username,
                              'action': CommunityActions.OWNER.value,
                              'addrem': CommunityActions.ADD.value})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)

        # now remove self as an owner.
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': CommunityActions.OWNER.value,
                              'addrem': CommunityActions.REMOVE.value})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)

    def test_community_remove_sole_owner(self):
        """ prevent removing the sole owner """
        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': CommunityActions.OWNER.value,
                              'addrem': CommunityActions.REMOVE.value})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 400)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], f"Cannot remove last owner '{self.cat.id}' of community")

    def test_community_add_existing_owner(self):
        """ try to add an owner who already owns the community """

        self.client.login(username='cat', password='adumbpassword')
        url = reverse('access_manage_community',
                      kwargs={'cid': self.pets.id,
                              'uid': self.cat.username,
                              'action': CommunityActions.OWNER.value,
                              'addrem': CommunityActions.ADD.value})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 400)
        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'], f"user '{self.cat.id}' already owns community")

    def test_community_add_group_automatically(self):
        """ add a group automatically to a community """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.cats.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertNotEqual(json_response['members'], {})
        self.assertNotEqual(json_response['pending'], {})
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.cats.id)
        # check request for the group to join community got approved
        self.assertEqual(gcr.approved, True)
        self.assertEqual(gcr.community.active, True)

    def test_community_add_group_and_remove(self):
        """ add a group automatically to a community """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.cats.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertNotEqual(json_response['members'], {})
        self.assertNotEqual(json_response['pending'], {})
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)

        # now remove the group from the community
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.REMOVE.value,
                              "gid": self.cats.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertNotEqual(json_response['members'], {})
        self.assertNotEqual(json_response['groups'], {})
        # check request got deleted
        self.assertEqual(GroupCommunityRequest.objects.count(), 0)

    def test_community_invite_group_deferred(self):
        """ invite a group to a community with deferral """
        self.client.login(username='cat', password='adumbpassword')

        self.assertEqual(GroupCommunityRequest.objects.count(), 0)
        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

    def test_community_invite_group_not_owner(self):
        """ prohibit invitations from non-owners """
        self.client.login(username='dog', password='anotherpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 400)
        json_response = json.loads(result.content)
        self.assertEqual(GroupCommunityRequest.objects.count(), 0)
        self.assertEqual(json_response['denied'],
                         "user 'dog' does not own community 'all kinds of pets'")

    def test_community_invite_group_and_retract(self):
        """ invite a group and retract the invitation """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

        # now retract the invitation
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.RETRACT.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 0)

    def test_community_invite_group_and_accept(self):
        """ invite a group to a community and group accepts """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.dogs.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

        # become the owner of dogs
        self.client.login(username='dog', password='anotherpassword')

        # check that the group is not yet a member of the community
        self.assertFalse(self.dogs in self.pets.member_groups.all())

        # now accept the invitation
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.APPROVE.value,
                              "gid": self.dogs.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, True)
        self.assertEqual(gcr.redeemed, True)
        community = gcr.community
        self.assertIn(self.dogs, community.member_groups.all())

    def test_community_invite_group_and_decline(self):
        """ invite a group to a community and group accepts """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns community but not group: deferred and queued.
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.INVITE.value,
                              "gid": self.dogs.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)

        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

        # become the owner of dogs
        self.client.login(username='dog', password='anotherpassword')

        # we haven't joined the community yet.
        self.assertFalse(self.dogs in self.pets.member_groups)

        # now decline the invitation
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.DECLINE.value,
                              "gid": self.dogs.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, True)
        community = gcr.community
        self.assertNotIn(self.dogs, community.member_groups.all())

    def test_group_add_community_automatically(self):
        """ add a group automatically to a community """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.cats.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.cats.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, True)
        self.assertEqual(gcr.redeemed, True)
        community = gcr.community
        self.assertIn(self.cats, community.member_groups.all())

    def test_group_add_community_and_remove(self):
        """ add a group automatically to a community """
        self.client.login(username='cat', password='adumbpassword')

        # cat owns group and community; automatically approved
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.cats.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.cats.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, True)
        self.assertEqual(gcr.redeemed, True)
        community = gcr.community
        self.assertIn(self.cats, community.member_groups.all())

        # now leave the community
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.LEAVE.value,
                              "gid": self.cats.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 0)

    def test_group_join_community_deferred(self):
        """ request joining a community with deferral """
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)
        community = gcr.community
        self.assertNotIn(self.dogs, community.member_groups.all())

    def test_group_join_community_deferred_and_accept(self):
        """ request joining a community with deferral and accept """
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        # check that a request is pending
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

        community = gcr.community
        self.assertNotIn(self.dogs, community.member_groups.all())

        # login as community owner
        self.client.login(username='cat', password='adumbpassword')

        # approve that request
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.APPROVE.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, True)
        self.assertEqual(gcr.community.active, True)

    def test_group_join_community_deferred_and_decline(self):
        """ request joining a community with deferral and decline"""
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        # check that a request is pending
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)

        community = gcr.community
        self.assertNotIn(self.dogs, community.member_groups.all())

        # login as community owner
        self.client.login(username='cat', password='adumbpassword')

        # decline that request
        url = reverse("access_manage_community",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.DECLINE.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, True)

    def test_group_join_community_deferred_and_retract(self):
        """ request joining a community with deferral and retract the request """
        self.client.login(username='dog', password='anotherpassword')

        # dog owns group but not community: deferred and queued.
        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.JOIN.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 1)
        gcr = GroupCommunityRequest.objects.first()
        self.assertEqual(gcr.group.id, self.dogs.id)
        self.assertEqual(gcr.community.id, self.pets.id)
        self.assertEqual(gcr.approved, False)
        self.assertEqual(gcr.redeemed, False)
        community = gcr.community
        self.assertNotIn(self.dogs, community.member_groups.all())

        url = reverse("access_manage_group",
                      kwargs={"cid": self.pets.id,
                              "action": CommunityActions.RETRACT.value,
                              "gid": self.dogs.id})

        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(GroupCommunityRequest.objects.count(), 0)

    #######################
    # community creation
    #######################

    def test_community_request_not_logged_in(self):
        """ catch users who are not logged in """

        url = reverse("access_manage_crequests")
        result = self.client.get(url)
        self.assertEqual(result.status_code, 401)

        json_response = json.loads(result.content)
        self.assertEqual(json_response['denied'],
                         "You must be logged in to access this functionality.")

    def test_community_request_logged_in(self):
        """ list community requests for to a regular user """
        self.client.login(username='dog', password='anotherpassword')

        url = reverse("access_manage_crequests")
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertTrue(is_equal_to_as_set(json_response['pending'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))

    def test_community_request_logged_in_admin(self):
        """ list community requests for to a regular user """
        self.client.login(username='admin', password='passwordsarestupid')

        url = reverse("access_manage_crequests")
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        self.assertTrue(is_equal_to_as_set(json_response['pending'], []))
        self.assertTrue(is_equal_to_as_set(json_response['declined'], []))

    def test_community_request_entry(self):
        """ enter a request for a regular user """
        self.client.login(username='dog', password='anotherpassword')

        # no community request object at this point
        self.assertEqual(RequestCommunity.objects.count(), 0)
        # no community object at this point apart from the pets community
        self.assertEqual(Community.objects.exclude(id=self.pets.id).count(), 0)

        url = reverse("request_new_community")
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News that fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "https://google.com/my-cummunity"
        })
        self.assertEqual(result.status_code, 302)
        # there should be one community request object at this point
        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()
        self.assertEqual(cr.approved, False)
        self.assertEqual(cr.pending_approval, True)
        self.assertEqual(cr.requested_by, self.dog)

        # there should be one community object at this point that is in active state
        self.assertEqual(Community.objects.exclude(id=self.pets.id).count(), 1)
        new_community = Community.objects.exclude(id=self.pets.id).first()
        self.assertFalse(new_community.active)
        self.assertEqual(cr.community_to_approve, new_community)

    def test_community_edit_request(self):
        """ admin edits a request without approval """
        self.client.login(username='dog', password='anotherpassword')
        url = reverse("request_new_community")
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News that fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars."
        })
        self.assertEqual(result.status_code, 302)
        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()

        # now update the request as admin
        crid = cr.id
        self.client.login(username='admin', password='passwordsarestupid')
        url = reverse("access_manage_crequests", kwargs={"action": CommunityRequestActions.UPDATE.value, "crid": crid})
        result = self.client.post(url, {
            "name": "Real news",
            "description": "News that fit for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "https://google.com"
        })
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)
        # the pending and declined requests in the response would be empty list as these requests are not
        # originally created by the admin
        pending = [x['id'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))
        declined = [x['id'] for x in json_response['declined']]
        self.assertTrue(is_equal_to_as_set(declined, []))
        cr = RequestCommunity.objects.first()
        self.assertTrue(cr.pending_approval)
        self.assertFalse(cr.declined)

    def test_community_approve_request(self):
        """ approve a request for a regular user """
        self.client.login(username='dog', password='anotherpassword')

        # create a request to approve
        url = reverse("request_new_community")
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News that fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars."
        })

        self.assertEqual(result.status_code, 302)

        # This is the request to be approved.
        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()
        self.assertEqual(cr.approved, False)
        self.assertEqual(cr.pending_approval, True)

        # There should be a community now that is not active
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 1)
        new_community = Community.objects.filter(name='Fake news').first()
        self.assertFalse(new_community.active)

        # now approve the request as admin
        self.client.login(username='admin', password='passwordsarestupid')
        url = reverse("access_manage_crequests", kwargs={"action": CommunityRequestActions.APPROVE.value,
                                                         "crid": cr.id})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # There should be a community now that is active
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 1)
        new_community = Community.objects.filter(name='Fake news').first()
        self.assertTrue(new_community.active)
        cr = RequestCommunity.objects.first()
        self.assertEqual(cr.approved, True)
        self.assertEqual(cr.pending_approval, False)
        pending = [x['id'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))
        declined = [x['id'] for x in json_response['declined']]
        self.assertTrue(is_equal_to_as_set(declined, []))

    def test_community_decline_request(self):
        """ decline a request for a regular user """
        self.client.login(username='dog', password='anotherpassword')
        self.assertEqual(RequestCommunity.objects.count(), 0)
        # create a request to approve
        url = reverse("request_new_community")
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News that fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars."

        })
        self.assertEqual(result.status_code, 302)

        # there should be one community request object at this point
        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()
        self.assertEqual(cr.approved, False)
        self.assertEqual(cr.pending_approval, True)
        self.assertEqual(cr.requested_by, self.dog)

        # There should be a community now.
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 1)

        # To act, we need this ID.
        cr_id = cr.id
        # now reject the request as admin
        self.client.login(username='admin', password='passwordsarestupid')
        decline_reason = "The community seems not relevant to hydroshare"
        url = reverse("access_manage_crequests", kwargs={"action": CommunityRequestActions.DECLINE.value,
                                                         "crid": cr_id})
        result = self.client.post(url, data={"reason": decline_reason})
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()
        self.assertEqual(cr.approved, False)
        self.assertEqual(cr.pending_approval, False)
        self.assertEqual(cr.id, cr_id)

        # There should be still the community in inactive state.
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 1)
        new_community = Community.objects.filter(name='Fake news').first()
        self.assertFalse(new_community.active)
        # the pending and declined requests in the response would be empty list as these requests are not
        # originally created by the admin
        pending = [x['id'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))
        declined = [x['id'] for x in json_response['declined']]
        self.assertTrue(is_equal_to_as_set(declined, []))
        cr = RequestCommunity.objects.first()
        self.assertTrue(cr.declined)
        self.assertFalse(cr.pending_approval)

    def test_community_delete_request(self):
        """ remove a request from a regular user """

        self.client.login(username='dog', password='anotherpassword')
        self.assertEqual(RequestCommunity.objects.count(), 0)

        # create a request to approve; if crid is not specified, it's new
        url = reverse("request_new_community")
        result = self.client.post(url, {
            "name": "Fake news",
            "description": "News that fit for liberals and not for conservatives.",
            "email": "acouch@hydroshare.org",
            "purpose": "To be the opposite of InfoWars.",
            "url": "http://usu.edu/waterlab"
        })
        self.assertEqual(result.status_code, 302)
        self.assertEqual(RequestCommunity.objects.count(), 1)
        cr = RequestCommunity.objects.first()
        crid = cr.id
        self.assertEqual(RequestCommunity.objects.count(), 1)

        # no user switching: removing a request doesn't require admin
        url = reverse("access_manage_crequests", kwargs={"action": CommunityRequestActions.REMOVE.value, "crid": crid})
        result = self.client.post(url)
        self.assertEqual(result.status_code, 200)
        json_response = json.loads(result.content)

        # request community object gets deleted
        self.assertEqual(RequestCommunity.objects.count(), 0)

        # There should be no community now.
        self.assertEqual(Community.objects.filter(name='Fake news').count(), 0)
        self.assertEqual(RequestCommunity.objects.count(), 0)

        pending = [x['id'] for x in json_response['pending']]
        self.assertTrue(is_equal_to_as_set(pending, []))
        declined = [x['id'] for x in json_response['declined']]
        self.assertTrue(is_equal_to_as_set(declined, []))
