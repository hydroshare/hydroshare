from django.test import TransactionTestCase

# Create your tests here.
from hs_core.testing import TestCaseCommonUtilities
from hs_core import hydroshare
from django.contrib.auth.models import Group
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup, \
    KeyValuePair, ResourceRecToPair, UserRecToPair, GroupRecToPair


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
            'foo@usu.edu',
            username='foo',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
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

        self.group = self.user.uaccess.create_group(
            title='meowers', description='We are the meowers')

    def tearDown(self):
        super(TestCreateRecommendedResource, self).tearDown()

    def test_create_rec_resource(self):
        rec = RecommendedResource.recommend(self.user, self.res, relevance=0.5)
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_resource, self.res)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 0)
        rec.relate('foo', 'bar', 0.4)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='foo')
        self.assertEqual(kv.value, 'bar')
        rel = ResourceRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 0.4)
        rec.unrelate('foo', 'bar')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedResource.clear()
        self.assertEqual(RecommendedResource.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(ResourceRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)

    def test_create_rec_resource_with_keywords(self):
        rec = RecommendedResource.recommend(self.user, self.res, relevance=0.5,
                                            keywords=(('subject', 'dogs', 1.0),))
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_resource, self.res)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='subject', value='dogs')
        rel = ResourceRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 1.0)
        rec.unrelate('subject', 'dogs')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedResource.clear()
        self.assertEqual(RecommendedResource.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(ResourceRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)

    def test_create_rec_user(self):
        rec = RecommendedUser.recommend(self.user, self.user2, relevance=0.5)
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_user, self.user2)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 0)
        rec.relate('foo', 'bar', 0.4)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='foo')
        self.assertEqual(kv.value, 'bar')
        rel = UserRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 0.4)
        rec.unrelate('foo', 'bar')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedUser.clear()
        self.assertEqual(RecommendedUser.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(UserRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)

    def test_create_rec_user_with_keywords(self):
        rec = RecommendedUser.recommend(self.user, self.user2, relevance=0.5,
                                        keywords=(('subject', 'dogs', 1.0),))
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_user, self.user2)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='subject', value='dogs')
        rel = UserRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 1.0)
        rec.unrelate('subject', 'dogs')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedUser.clear()
        self.assertEqual(RecommendedUser.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(UserRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)

    def test_create_rec_group(self):
        rec = RecommendedGroup.recommend(self.user, self.group, relevance=0.5)
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_group, self.group)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 0)
        rec.relate('foo', 'bar', 0.4)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='foo')
        self.assertEqual(kv.value, 'bar')
        rel = GroupRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 0.4)
        rec.unrelate('foo', 'bar')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedGroup.clear()
        self.assertEqual(RecommendedGroup.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(GroupRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)

    def test_create_rec_group_with_keywords(self):
        rec = RecommendedGroup.recommend(self.user, self.group, relevance=0.5,
                                         keywords=(('subject', 'dogs', 1.0),))
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_group, self.group)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(rec.keywords.count(), 1)
        kv = rec.keywords.get(key='subject', value='dogs')
        rel = GroupRecToPair.objects.get(pair=kv)
        self.assertEqual(rel.recommendation, rec)
        self.assertEqual(rel.weight, 1.0)
        rec.unrelate('subject', 'dogs')
        self.assertEqual(rec.keywords.count(), 0)
        RecommendedGroup.clear()
        self.assertEqual(RecommendedGroup.objects.all().count(), 0)
        # does cascade delete work?
        self.assertEqual(GroupRecToPair.objects.all().count(), 0)
        # deleting references doesn't delete key/value pairs
        KeyValuePair.clear()
        self.assertEqual(KeyValuePair.objects.all().count(), 0)
