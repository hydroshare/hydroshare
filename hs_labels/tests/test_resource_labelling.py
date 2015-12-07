from django.test import TestCase
from django.contrib.auth.models import User, Group

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_labels.models import UserLabels, ResourceLabels, \
    UserResourceLabels, LabelCodes, HSLUsageException


def global_reset():
    UserResourceLabels.objects.all().delete()
    UserLabels.objects.all().delete()
    ResourceLabels.objects.all().delete()
    BaseResource.objects.all().delete()

def match_lists(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    return len(set(l1) & set(l2)) == len(set(l1))\
       and len(set(l1) | set(l2)) == len(set(l1))


class T01BasicFunction(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T01BasicFunction, self).setUp()
        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='f_cat',
            last_name='l_cat',
            superuser=False,
            groups=[]
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='f_dog',
            last_name='l_dog',
            superuser=False,
            groups=[]
        )

        self.scratching = hydroshare.create_resource(resource_type='GenericResource',
                                                     owner=self.cat,
                                                     title='Test Resource',
                                                     metadata=[],)

        self.bones = hydroshare.create_resource(resource_type='GenericResource',
                                                     owner=self.dog,
                                                     title='all about dog bones',
                                                     metadata=[],)

    def test01labels(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, "penalty clause")
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), ['penalty clause']))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))
        self.assertTrue(match_lists(cat.ulabels.get_resources_with_label('penalty clause'), [scratching]))
        self.assertTrue(match_lists(cat.ulabels.user_labels, ['penalty clause']))

    def test02folders(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.file_resource(scratching, "penalty clause")
        self.assertTrue(match_lists(cat.ulabels.filed_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists(scratching.rlabels.get_folder(cat), 'penalty clause'))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))

    def test03favorite(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.favorite_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.favorited_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_favorite(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))

    def test04mine(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.claim_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))

    def test05clearlabel(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, "penalty clause")
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), ['penalty clause']))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unlabel_resource(scratching, "penalty clause")
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), []))

    def test06clearfolder(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.file_resource(scratching, "penalty clause")
        self.assertTrue(match_lists(cat.ulabels.filed_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists(scratching.rlabels.get_folder(cat), 'penalty clause'))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unfile_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), []))

    def test07clearfavorite(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.favorite_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.favorited_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_favorite(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unfavorite_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), []))

    def test08clearmine(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.claim_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unclaim_resource(scratching)
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), []))

    # argument cleaning
    def test09labelcleaning(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, r'  A grevious //  label  ')
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        # pprint(scratching.rlabels.get_labels(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), ['A grevious label']))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))

    def test10foldercleaning(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.file_resource(scratching, r' / / / A/ stupid//// folder//// /')
        self.assertTrue(match_lists(cat.ulabels.filed_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching]))
        # pprint(scratching.rlabels.get_folder(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_folder(cat), 'A/stupid/folder'))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat]))

    def test11notexist(self):
        cat = self.cat
        scratching = self.scratching
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.filed_resources, []))
        self.assertTrue(match_lists(cat.ulabels.favorited_resources, []))
        self.assertTrue(match_lists(cat.ulabels.my_resources, []))
        self.assertTrue(scratching.rlabels.get_folder(cat) is None)
        self.assertFalse(scratching.rlabels.is_favorite(cat))
        self.assertFalse(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists(scratching.rlabels.get_labels(cat), []))

    # TODO:crosstalk test
    def test12crosstalk(self):
        cat = self.cat  # user
        dog = self.dog  # user
        scratching = self.scratching  # resource
        bones = self.bones            # resource
        cat.ulabels.file_resource(scratching, r'A/stupid/folder')
        dog.ulabels.label_resource(bones, r'cool!')
        cat.ulabels.claim_resource(bones)
        dog.ulabels.favorite_resource(scratching)

        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.filed_resources, [scratching]))
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, [scratching, bones]))
        self.assertTrue(match_lists(scratching.rlabels.get_folder(cat), 'A/stupid/folder'))
        self.assertTrue(match_lists(scratching.rlabels.get_users(), [cat, dog]))
        # pprint(bones.rlabels.get_folder(cat))
        self.assertTrue(bones.rlabels.get_folder(cat) is None)
        self.assertTrue(match_lists(bones.rlabels.get_labels(dog), ['cool!']))
        self.assertTrue(match_lists(bones.rlabels.get_users(), [cat, dog]))

    # TODO: clear all test
    def test13allclear(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.file_resource(scratching, r'A/stupid/folder')
        cat.ulabels.label_resource(scratching, r'cool!')
        cat.ulabels.claim_resource(scratching)
        cat.ulabels.favorite_resource(scratching)

        dog = self.dog
        dog.ulabels.file_resource(scratching, r'dumb cat tricks')
        dog.ulabels.label_resource(scratching, r'dumb cats')

        cat.ulabels.clear_resource_all(scratching)
        # cat.ulabels.clear_resource_labels(scratching)
        self.assertTrue(match_lists(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists(cat.ulabels.filed_resources, []))
        self.assertTrue(match_lists(cat.ulabels.favorited_resources, []))
        self.assertTrue(match_lists(cat.ulabels.my_resources, []))
        # dog left alone
        self.assertTrue(match_lists(dog.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists(dog.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists(dog.ulabels.filed_resources, [scratching]))
        self.assertTrue(match_lists(dog.ulabels.favorited_resources, []))
        self.assertTrue(match_lists(dog.ulabels.my_resources, []))

    def test14exceptions(self):
        cat = self.cat
        scratching = self.scratching

        try:
            cat.ulabels.unlabel_resource(cat, 'foo')
            self.fail("unlabel_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.unlabel_resource(scratching, cat)
            self.fail("unlabel_resource allowed invalid label")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.label_resource(cat, 'foo')
            self.fail("label_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.label_resource(scratching, cat)
            self.fail("label_resource allowed invalid label")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.unfile_resource(cat)
            self.fail("unfile_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.file_resource(cat, 'foo')
            self.fail("file_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.file_resource(scratching, cat)
            self.fail("file_resource allowed invalid label")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.claim_resource('foo')
            self.fail("claim_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.unclaim_resource('foo')
            self.fail("unclaim_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.favorite_resource('foo')
            self.fail("favorite_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.unfavorite_resource('foo')
            self.fail("unfavorite_resource allowed invalid resource")
        except HSLUsageException:
            pass

        try:
            cat.ulabels.clear_resource_labels('foo')
            self.fail("clear_resource_labels allowed invalid resource")
        except HSLUsageException:
            pass