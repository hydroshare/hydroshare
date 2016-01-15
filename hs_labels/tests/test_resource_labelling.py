from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_labels.models import UserLabels, ResourceLabels, \
    UserResourceLabels, UserResourceFlags, UserStoredLabels, FlagCodes

def global_reset():
    UserResourceLabels.objects.all().delete()
    UserResourceFlags.objects.all().delete()
    UserStoredLabels.objects.all().delete()
    UserLabels.objects.all().delete()
    ResourceLabels.objects.all().delete()
    BaseResource.objects.all().delete()

def match_lists_as_sets(l1, l2):
    """ return True if two lists contain the same content as sets

    :param l1: first list
    :param l2: second list
    :return: whether lists match

    Lists are treated as multisets, in the sense that order is unimportant.
    """
    return len(set(l1) & set(l2)) == len(set(l1))\
       and len(set(l1) | set(l2)) == len(set(l1))

def match_nested_dicts(d1, d2):
    """
    Match nested dictionary objects with string keys and arbitrary values against one another.

    :param d1: first dict object
    :param d2: second dict object
    :return: True if d1 and d2 agree exactly in structure, False otherwise.

    It is assumed that when recursively descending, values are either dicts or some other object
    for which == is a valid comparison, including object instances.
    """
    # pprint(d1)
    # pprint(d2)
    if not isinstance(d1, dict): return False
    if not isinstance(d2, dict): return False
    # print("got two dicts")
    if not match_lists_as_sets(d1.keys(), d2.keys()): return False
    # print("same keys")
    for k in d1:
        # print("key is ", k)
        # print("type of d1[k] is ", type(d1[k]))
        # print("type of d2[k] is ", type(d2[k]))
        if type(d1[k]) != type(d2[k]): return False
        if isinstance(d1[k], dict) and isinstance(d2[k], dict):
            # print("checking dicts against one another")
            if not match_nested_dicts(d1[k], d2[k]): return False
        else:
            # print("checking base values")
            return d1[k]==d2[k]
    return True

def match_nested_lists(l1, l2):
    """ Match nested lists term for term

    :param l1: first list
    :param l2: second list
    :return: True or False

    This differs from "match_lists_as_sets" in the sense that order is important. The
    lists in question can only contain other lists or objects for which == is a valid
    comparison.
    """
    if not isinstance(l1, list): return False
    if not isinstance(l2, list): return False
    if len(l1) != len(l2): return False
    for i in range(len(l1)):
        if isinstance(l1[i], list) and isinstance(l2[i], list):
            if not match_nested_lists(l1[i], l2[i]): return False
        elif not isinstance(l1[i], list) and not isinstance(l2[i], list):
            if l1[i] != l2[i]: return False
        else: return False
    return True


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

    def test_labels(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, "penalty clause")
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['penalty clause']))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_resources_with_label('penalty clause'), [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.user_labels, ['penalty clause']))

    def test_favorite(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.favorite_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.favorited_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_favorite(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))

    def test_mine(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.claim_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))

    def test_flag(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.MINE), []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.FAVORITE), []))
        self.assertFalse(scratching.rlabels.is_flagged(cat, FlagCodes.MINE))
        self.assertFalse(scratching.rlabels.is_flagged(cat, FlagCodes.FAVORITE))
        cat.ulabels.flag_resource(scratching, FlagCodes.MINE) 
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.favorited_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.MINE), [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.FAVORITE), []))
        self.assertTrue(scratching.rlabels.is_flagged(cat, FlagCodes.MINE))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))

    def test_clear_label(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, "penalty clause")
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['penalty clause']))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.label_resource(scratching, "penalty claws")
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['penalty clause', 'penalty claws']))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unlabel_resource(scratching, "penalty clause")
        cat.ulabels.unlabel_resource(scratching, "penalty claws")
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), []))

    def test_clear_favorite(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.favorite_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.favorited_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_favorite(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unfavorite_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), []))

    def test_clear_mine(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.claim_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unclaim_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), []))

    def test_clear_flag(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.claim_resource(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.MINE), [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))
        cat.ulabels.unflag_resource(scratching, FlagCodes.MINE)
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_flagged_resources(FlagCodes.MINE), []))
        self.assertFalse(scratching.rlabels.is_flagged(cat, FlagCodes.MINE))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), []))

    # argument cleaning
    def test_label_cleaning(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, r'  A grevious //  label  ')
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [scratching]))
        # pprint(scratching.rlabels.get_labels(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['A grevious label']))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [cat]))

    def test_not_exist(self):
        cat = self.cat
        scratching = self.scratching
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.favorited_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, []))
        self.assertFalse(scratching.rlabels.is_favorite(cat))
        self.assertFalse(scratching.rlabels.is_mine(cat))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))

    def test_crosstalk(self):
        cat = self.cat  # user
        dog = self.dog  # user
        scratching = self.scratching  # resource
        bones = self.bones            # resource
        dog.ulabels.label_resource(bones, r'cool!')
        cat.ulabels.claim_resource(bones)
        dog.ulabels.favorite_resource(scratching)

        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, [bones]))
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_users(), [dog]))
        self.assertTrue(match_lists_as_sets(bones.rlabels.get_labels(dog), ['cool!']))
        self.assertTrue(match_lists_as_sets(bones.rlabels.get_users(), [cat, dog]))

    def test_all_clear(self):
        cat = self.cat  # user
        scratching = self.scratching  # resource
        cat.ulabels.label_resource(scratching, r'cool!')
        cat.ulabels.claim_resource(scratching)
        cat.ulabels.favorite_resource(scratching)

        dog = self.dog
        dog.ulabels.label_resource(scratching, r'dumb cats')

        cat.ulabels.clear_resource_all(scratching)
        self.assertTrue(match_lists_as_sets(cat.ulabels.resources_of_interest, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.labeled_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.favorited_resources, []))
        self.assertTrue(match_lists_as_sets(cat.ulabels.my_resources, []))

        self.assertTrue(match_lists_as_sets(dog.ulabels.resources_of_interest, [scratching]))
        self.assertTrue(match_lists_as_sets(dog.ulabels.labeled_resources, [scratching]))
        self.assertTrue(match_lists_as_sets(dog.ulabels.favorited_resources, []))
        self.assertTrue(match_lists_as_sets(dog.ulabels.my_resources, []))

    def test_saved_labels(self):
        cat = self.cat
        scratching = self.scratching
        cat.ulabels.save_label('silly')
        cat.ulabels.save_label('cranky')
        self.assertTrue(match_lists_as_sets(cat.ulabels.saved_labels, ['silly', 'cranky']))
        cat.ulabels.unsave_label('silly')
        self.assertTrue(match_lists_as_sets(cat.ulabels.saved_labels, ['cranky']))
        cat.ulabels.clear_saved_labels()
        self.assertTrue(match_lists_as_sets(cat.ulabels.saved_labels, []))

        # test cascading deletion of labels from assigned resources when a stored label is deleted
        cat.ulabels.save_label('silly')
        cat.ulabels.save_label('cranky')
        cat.ulabels.label_resource(scratching, "silly")
        cat.ulabels.label_resource(scratching, "cranky")
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['silly', 'cranky']))
        cat.ulabels.unsave_label("silly")
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), ['cranky']))
        cat.ulabels.unsave_label('cranky')
        self.assertTrue(match_lists_as_sets(scratching.rlabels.get_labels(cat), []))

    def test_remove_label(self):
        cat = self.cat
        scratching = self.scratching
        bones = self.bones
        cat.ulabels.label_resource(scratching, "cool")
        cat.ulabels.label_resource(bones, "cool")
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_resources_with_label("cool"), [scratching, bones]))
        cat.ulabels.remove_resource_label("cool")
        self.assertTrue(match_lists_as_sets(cat.ulabels.get_resources_with_label("cool"), []))


