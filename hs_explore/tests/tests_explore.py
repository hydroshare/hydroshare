from django.test import TransactionTestCase
from hs_core.testing import TestCaseCommonUtilities
# Create your tests here.
from hs_core import hydroshare
from hs_explore.models import RecommendedResource, UserPreferences, LDAWord
from django.contrib.auth.models import Group


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
            superuser=False
        )

        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
        )

    def test_create_rec_resource(self):
        rec = RecommendedResource.recommend(self.user, self.res, 'Propensity', relevance=0.5)
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_resource, self.res)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(len(rec.keywords), 0)
        rec.relate('foo', '2')
        self.assertEqual(len(rec.keywords), 1)
        kv = rec.keywords['foo']
        self.assertEqual(kv, '2')
        rec.unrelate('foo')
        self.assertEqual(len(rec.keywords), 0)
        RecommendedResource.clear()
        self.assertEqual(RecommendedResource.objects.all().count(), 0)

    def test_create_rec_resource_with_keywords(self):
        rec = RecommendedResource.recommend(self.user, self.res, 'Propensity', relevance=0.5,
                                            keywords={'dogs': '2'})
        self.assertEqual(rec.user, self.user)
        self.assertEqual(rec.candidate_resource, self.res)
        self.assertEqual(rec.relevance, 0.5)
        self.assertEqual(len(rec.keywords), 1)
        kv = rec.keywords['dogs']
        self.assertEqual(kv, '2')
        rec.unrelate('dogs')
        self.assertEqual(len(rec.keywords), 0)
        RecommendedResource.clear()
        self.assertEqual(RecommendedResource.objects.all().count(), 0)


class TestCreateUserPreferences(TestCaseCommonUtilities, TransactionTestCase):

    def setUp(self):
        super(TestCreateUserPreferences, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user to be used for creating the resource
        self.user = hydroshare.create_account(
            'foo@usu.edu',
            username='foo',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False
        )

    def test_create_user_preferences(self):
        up = UserPreferences.prefer(self.user, 'Resource')
        self.assertEqual(up.user, self.user)
        self.assertEqual(up.pref_for, 'Resource')
        self.assertEqual(len(up.preferences), 0)
        up.relate('foo', '2')
        self.assertEqual(len(up.preferences), 1)
        kv = up.preferences['foo']
        self.assertEqual(kv, '2')
        up.unrelate('foo')
        self.assertEqual(len(up.preferences), 0)
        UserPreferences.clear()
        self.assertEqual(UserPreferences.objects.all().count(), 0)

    def test_create_user_preferences_with_preferences(self):
        up = UserPreferences.prefer(self.user, 'Resource',
                                    preferences={'dogs': '2'})
        self.assertEqual(up.user, self.user)
        self.assertEqual(up.pref_for, 'Resource')
        self.assertEqual(len(up.preferences), 1)
        kv = up.preferences['dogs']
        self.assertEqual(kv, '2')
        up.unrelate('dogs')
        self.assertEqual(len(up.preferences), 0)
        UserPreferences.clear()
        self.assertEqual(UserPreferences.objects.all().count(), 0)


class TestAddLDAWord(TestCaseCommonUtilities, TransactionTestCase):

    def test_add_lda_word(self):
        lda_word = LDAWord.add_word('ODM2', 'keep', 'name', 'cat')
        self.assertEqual(lda_word.source, 'ODM2')
        self.assertEqual(lda_word.word_type, 'keep')
        self.assertEqual(lda_word.part, 'name')
        self.assertEqual(lda_word.value, 'cat')
        lda_word2 = LDAWord.add_word('ODM2', 'keep', 'name', 'cat')
        self.assertEqual(lda_word, lda_word2)
