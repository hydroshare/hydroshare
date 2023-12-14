"""
comments- not sure how to implement test_email_function

"""

import unittest

from django.contrib.auth.models import User, Group
from django.test import TestCase
from theme.models import UserProfile
from django.core.exceptions import ValidationError

from hs_core import hydroshare
from hs_dictionary.models import UncategorizedTerm


class CreateAccountTest(TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name="Hydroshare Author")

    def test_basic_superuser(self):
        username, first_name, last_name, password = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        user = hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=True,
            password=password,
            active=True,
        )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertTrue(db_user.is_superuser)
        self.assertTrue(user.is_superuser)

    def test_basic_user(self):
        username, first_name, last_name, password = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        user = hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True,
        )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertFalse(db_user.is_superuser)
        self.assertFalse(user.is_superuser)

    def test_with_groups(self):
        groups = []

        username, first_name, last_name, _ = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        user = hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            groups=groups,
        )

        g0 = user.uaccess.create_group(title="group0", description="This is group0")
        g1 = user.uaccess.create_group(title="group1", description="This is group1")
        g2 = user.uaccess.create_group(title="group2", description="This is group2")

        # TODO from @alvacouch: no order assumption -> poor test.
        user_groups = list(Group.objects.filter(g2ugp__user=user))

        groups = [g0, g1, g2]

        self.assertEqual(groups, user_groups)

    def test_with_organizations(self):
        organizations = ["org with, comma", "another org", "single"]
        organization = ";".join(organizations)

        username, first_name, last_name, _ = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            organization=organization,
        )

        user = UserProfile.objects.filter(user__username="shaunjl").first()
        self.assertEqual(user.organization, "org with, comma;another org;single")

        terms = UncategorizedTerm.objects.all()
        self.assertEqual(3, terms.count())
        for term in terms:
            self.assertTrue(term.name in organizations)

    def test_with_usertype_country_state(self):
        username = "testuser"
        usertype = "University Faculty"
        country = "United States"
        state = "NC"
        hydroshare.create_account(
            "testuser@gmail.com",
            username=username,
            first_name="Test",
            last_name="User",
            organization="TestOrg",
            user_type=usertype,
            country=country,
            state=state,
        )
        user = UserProfile.objects.filter(user__username=username).first()
        self.assertEqual(user.user_type, usertype)
        self.assertEqual(user.country, country)
        self.assertEqual(user.state, state)

    def test_case_in_username(self):
        username, first_name, last_name, password = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        user = hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True,
        )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertFalse(db_user.is_superuser)
        self.assertFalse(user.is_superuser)

        username, first_name, last_name, password = (
            "sHaUnJl",
            "shaun",
            "joseph",
            "mypass",
        )
        try:
            user = hydroshare.create_account(
                "other@gmail.com",
                username=username,
                first_name=first_name,
                last_name=last_name,
                superuser=False,
                password=password,
                active=True,
            )
            self.fail(
                "Should not be able to create an account with case insensitivie matching "
                "usernames"
            )
        except ValidationError as v:
            self.assertEqual("['User with provided username already exists.']", str(v))
            pass

    def test_case_in_email(self):
        username, first_name, last_name, password = (
            "shaunjl",
            "shaun",
            "joseph",
            "mypass",
        )
        user = hydroshare.create_account(
            "shaun@gmail.com",
            username=username,
            first_name=first_name,
            last_name=last_name,
            superuser=False,
            password=password,
            active=True,
        )

        users_in_db = User.objects.all()
        db_user = users_in_db[0]
        self.assertEqual(user.email, db_user.email)
        self.assertEqual(user.username, db_user.username)
        self.assertEqual(user.first_name, db_user.first_name)
        self.assertEqual(user.last_name, db_user.last_name)
        self.assertEqual(user.password, db_user.password)
        self.assertEqual(user.is_superuser, db_user.is_superuser)
        self.assertEqual(user.is_active, db_user.is_active)
        self.assertTrue(db_user.is_active)
        self.assertTrue(user.is_active)
        self.assertFalse(db_user.is_superuser)
        self.assertFalse(user.is_superuser)

        username, first_name, last_name, password = "other", "shaun", "joseph", "mypass"
        try:
            user = hydroshare.create_account(
                "ShAuN@gmail.com",
                username=username,
                first_name=first_name,
                last_name=last_name,
                superuser=False,
                password=password,
                active=True,
            )
            self.fail(
                "Should not be able to create an account with case insensitive matching "
                "emails"
            )
        except ValidationError as v:
            self.assertEqual("['User with provided email already exists.']", str(v))
            pass

    @unittest.skip
    def test_email_function(self):
        pass
