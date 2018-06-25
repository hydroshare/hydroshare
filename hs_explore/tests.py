from django.test import TransactionTestCase

# Create your tests here.
from hs_core.testing import TestCaseCommonUtilities
from hs_core import hydroshare
from django.contrib.auth.models import Group
from hs_explore import RecommendedResource, RecommendedUser, RecommendedGroup, \
    KeyValuePair


class TestkeyValuePair(TestCaseCommonUtilities, TransactionTestCase):

    def testkv(self):
        kv = KeyValuePair.create(key='foo', value='bar')
        self.assertEqual(kv.key, 'foo')
        self.assertEqual(kv.value, 'bar')
        kv2 = KeyValuePair.create(key='foo', value='bar')
        self.assertEqual(kv, kv2)


class TestCreateRecommendedResource(TestCaseCommonUtilities, TransactionTestCase):

    def setUp(self):
        super(TestCreateRecommendedResource, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user to be used for creating the resource
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
        )

    def tearDown(self):
        super(TestCreateRecommendedResource, self).tearDown()

    def test_create_resource_recommendation(self):
        rec = RecommendedResource.recommend(self.user, self.res, relevance=0.5)
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_resource, self.res)
        self.assertEqual(rec.relevance, 0.5)
        self.assertFalse(rec.keywords)


class TestCreateRecommendedUser(TestCaseCommonUtilities, TransactionTestCase):
    pass


class TestCreateRecommendedGroup(TestCaseCommonUtilities, TransactionTestCase):
    pass
