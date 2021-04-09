from django.test import TransactionTestCase
from hs_core.testing import TestCaseCommonUtilities
# Create your tests here.
from hs_core import hydroshare
from hs_explore.models import RecommendedResource, UserPreferences
from django.contrib.auth.models import Group
from hs_access_control.tests.utilities import global_reset
from hs_explore.utils import user_resource_matrix, get_resource_to_subjects, get_resource_to_abstract,\
    get_resource_to_published, get_users_interacted_resources, jaccard_sim, store_user_preferences,\
    store_recommended_resources, resource_owners, resource_editors
from datetime import datetime, timedelta
import socket
from django.test import Client
from rest_framework import status
from hs_access_control.models import PrivilegeCodes


class TestExploreUtils(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestExploreUtils, self).setUp()
        global_reset()
        self.hostname = socket.gethostname()
        self.resource_url = "/resource/{res_id}/"
        self.client = Client(HTTP_USER_AGENT='Mozilla/5.0')  # fake use of a real browser
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.end_date = datetime.now() + timedelta(days=2)
        self.start_date = datetime.now() - timedelta(days=2)
        self.today = datetime.now()
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )
        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            password='foobar',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.posts = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[{'description': {'abstract': "This is a great resource"}},
                      {'subject': {'value': "sample"}}]
        )
        self.posts.raccess.public = True
        self.posts.raccess.save()
        self.squirrel = hydroshare.create_account(
            'squirrel@gmail.com',
            username='squirrel',
            first_name='first_name_squirrel',
            last_name='last_name_squirrel',
            superuser=False,
            groups=[]
        )

        self.cat.uaccess.share_resource_with_user(self.posts, self.squirrel, PrivilegeCodes.CHANGE)
        self.client.login(username='cat', password='foobar')

    def test_resource_owners(self):
        owner_to_resources = resource_owners()
        test_dict = {'cat': [self.posts.short_id]}
        self.assertCountEqual(owner_to_resources['cat'], test_dict['cat'])

    def test_resource_editors(self):
        editor_to_resources = resource_editors()
        test_dict = {'squirrel': [self.posts.short_id]}
        self.assertCountEqual(editor_to_resources['squirrel'], test_dict['squirrel'])

    def test_user_resource_matrix(self):
        response = self.client.get(self.resource_url.format(res_id=self.posts.short_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = user_resource_matrix(self.start_date, self.end_date)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][0], self.cat.username)
        self.assertEqual(records[0][1], self.posts.short_id)
        self.assertEqual(records[0][2].date(), self.today.date())

    def test_get_resource_to_subjects(self):
        res_to_subs, subs_list = get_resource_to_subjects()
        test_res_to_subs = {self.posts.short_id: set(["sample"])}
        self.assertCountEqual(res_to_subs, test_res_to_subs)
        self.assertEqual(len(subs_list), 1)
        self.assertEqual(subs_list[0], "sample")

    def test_get_resource_to_abstract(self):
        res_to_abs = get_resource_to_abstract()
        abstract = "This is a great resource"
        test_res_to_abs = {self.posts.short_id: abstract}
        self.assertCountEqual(res_to_abs, test_res_to_abs)

    def test_get_resource_to_published(self):
        res_to_pub = get_resource_to_published()
        self.assertTrue(res_to_pub[self.posts.short_id])

    def test_get_users_interacted_resources(self):
        response = self.client.get(self.resource_url.format(res_id=self.posts.short_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records, usernames = get_users_interacted_resources(self.start_date, self.end_date)
        test_user_to_res = {self.cat.username: [self.posts.short_id]}
        test_usernames = set([self.cat.username])
        self.assertCountEqual(records, test_user_to_res)
        self.assertCountEqual(usernames, test_usernames)

    def test_jaccard_sim(self):
        s1 = set(["cat", "dog"])
        s2 = set(["cat", "fish", "horse"])
        jac_sim = jaccard_sim(s1, s2)
        self.assertEqual(jac_sim, 0.25)

    def test_store_user_preferences(self):
        user_to_keep_words_freq = {'cat': {'fish': 2}}
        store_user_preferences(user_to_keep_words_freq)
        self.assertEqual(UserPreferences.objects.all().count(), 1)
        stored_record = UserPreferences.objects.get(user=self.cat)
        stored_user_preferences = stored_record.preferences
        test_pref = {'fish': 2}
        self.assertCountEqual(stored_user_preferences, test_pref)

    def test_store_recommended_resources(self):
        dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            password='barfoo',
            first_name='not a cat',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        bones = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=dog,
            title='all about bones',
            metadata=[],
        )
        user_to_rec_list = {self.cat.username: [(bones.short_id, 0.5)]}
        res_to_keep_words = {bones.short_id: set(["sample"])}
        user_to_keep_words_freq = {'cat': {'sample': 2}}
        store_user_preferences(user_to_keep_words_freq)
        store_recommended_resources(user_to_rec_list, res_to_keep_words)
        self.assertEqual(RecommendedResource.objects.all().count(), 1)
        stored_record = RecommendedResource.objects.get(user=self.cat)
        rec_id = stored_record.candidate_resource.short_id
        self.assertEqual(rec_id, bones.short_id)
        self.assertEqual(stored_record.relevance, 0.5)
