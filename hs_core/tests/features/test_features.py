from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset
from hs_core.hydroshare.features import Features
from rest_framework import status
import socket
from django.test import Client
from datetime import timedelta, datetime
from hs_tracking.models import Variable, Session, Visitor
from mock import Mock


class TestFeatures(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestFeatures, self).setUp()
        global_reset()
        self.hostname = socket.gethostname()
        self.resource_url = "/resource/{res_id}/"
        self.client = Client(HTTP_USER_AGENT='Mozilla/5.0')  # fake use of a real browser
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.end_date = datetime.now() + timedelta(days=2)
        self.start_date = datetime.now() - timedelta(days=2)
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

        self.cats = self.cat.uaccess.create_group(
            title='cats', description="We are the cats")

        self.posts = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[],
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            password='barfoo',
            first_name='not a cat',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.dogs = self.dog.uaccess.create_group(
            title='dogs', description="We are the dogs")

        self.bones = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about bones',
            metadata=[],
        )

        self.squirrel = hydroshare.create_account(
            'squirrel@gmail.com',
            username='squirrel',
            first_name='first_name_squirrel',
            last_name='last_name_squirrel',
            superuser=False,
            groups=[]
        )

        self.pinecorns = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.squirrel,
            title='all about pinecorns',
            metadata=[],
        )

        self.cat.uaccess.share_resource_with_group(self.posts, self.cats, PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_resource_with_group(self.bones, self.dogs, PrivilegeCodes.VIEW)
        self.cat.uaccess.share_resource_with_user(self.posts, self.squirrel, PrivilegeCodes.CHANGE)
        self.cat.uaccess.share_group_with_user(self.cats, self.squirrel, PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_group_with_user(self.dogs, self.squirrel, PrivilegeCodes.VIEW)
        self.client.login(username='dog', password='barfoo')

    def createRequest(self, user=None):
        request = Mock()
        if user is not None:
            request.user = user

        # sample request with mocked ip address
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.255.182, 10.0.0.0, ' +
                                    '127.0.0.1, 198.84.193.157, '
            '177.139.233.139',
            'HTTP_X_REAL_IP': '177.139.233.132',
            'REMOTE_ADDR': '177.139.233.133',
        }

        return request

    def test_resource_owner(self):
        records = Features.resource_owners()
        self.assertEqual(len(records), 3)
        test = [(self.cat.username, self.posts.short_id),
                (self.dog.username, self.bones.short_id),
                (self.squirrel.username, self.pinecorns.short_id)]
        self.assertCountEqual(test, records)

    def test_group_onwer(self):
        records = Features.group_owners()
        self.assertEqual(len(records), 2)
        test = [(self.cat.username, self.cats.name), (self.dog.username, self.dogs.name)]
        self.assertCountEqual(test, records)

    def test_resource_editors(self):
        records = Features.resource_editors()
        self.assertEqual(len(records), 4)
        test = [(self.cat.username, self.posts.short_id),
                (self.dog.username, self.bones.short_id),
                (self.squirrel.username, self.pinecorns.short_id),
                (self.squirrel.username, self.posts.short_id)]
        self.assertCountEqual(test, records)

    def test_group_editors(self):
        records = Features.group_editors()
        self.assertEqual(len(records), 3)
        test = [(self.cat.username, self.cats.name),
                (self.dog.username, self.dogs.name),
                (self.squirrel.username, self.cats.name)]
        self.assertCountEqual(test, records)

    def test_resource_viewers(self):
        response = self.client.get(self.resource_url.format(res_id=self.bones.short_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = Features.resource_viewers(self.start_date, self.end_date)
        test = {}
        test[self.bones.short_id] = [self.dog.username]
        self.assertEqual(len(records), 1)
        self.assertCountEqual(records[self.bones.short_id], test[self.bones.short_id])

    def test_visited_resources(self):
        response = self.client.get(self.resource_url.format(res_id=self.bones.short_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = Features.visited_resources(self.start_date, self.end_date)
        test = {}
        test[self.dog.username] = [self.bones.short_id]
        self.assertEqual(len(records), 1)
        self.assertCountEqual(records[self.dog.username], test[self.dog.username])

    def test_resource_downloads(self):
        visitor = Visitor.objects.get(user=self.dog)
        session = Session.objects.get(visitor=visitor)
        fields = {}
        fields['filename'] = 'test_file'
        fields['resource_size_bytes'] = self.bones.size
        fields['resource_guid'] = self.bones.short_id
        fields['resource_type'] = self.bones.resource_type
        value = Variable.format_kwargs(**fields)
        Variable.objects.create(session=session, name='download',
                                type=Variable.encode_type(value),
                                value=Variable.encode(value),
                                last_resource_id=self.bones.short_id,
                                resource=self.bones,
                                rest=False,
                                landing=False)
        records = Features.resource_downloads(self.start_date, self.end_date)
        self.assertEqual(len(records), 1)
        test = {}
        test[self.bones.short_id] = [self.dog.username]
        self.assertCountEqual(records[self.bones.short_id], test[self.bones.short_id])

    def test_user_downloads(self):
        visitor = Visitor.objects.get(user=self.dog)
        session = Session.objects.get(visitor=visitor)
        fields = {}
        fields['filename'] = 'test_file'
        fields['resource_size_bytes'] = self.bones.size
        fields['resource_guid'] = self.bones.short_id
        fields['resource_type'] = self.bones.resource_type
        value = Variable.format_kwargs(**fields)
        Variable.objects.create(session=session, name='download',
                                type=Variable.encode_type(value),
                                value=Variable.encode(value),
                                last_resource_id=self.bones.short_id,
                                resource=self.bones,
                                rest=False,
                                landing=False)
        records = Features.user_downloads(self.start_date, self.end_date)
        self.assertEqual(len(records), 1)
        test = {}
        test[self.dog.username] = [self.bones.short_id]
        self.assertCountEqual(records[self.dog.username], test[self.dog.username])

    def test_resource_apps(self):
        visitor = Visitor.objects.get(user=self.dog)
        session = Session.objects.get(visitor=visitor)
        fields = {}
        fields['filename'] = 'test_file'
        fields['resource_size_bytes'] = self.bones.size
        fields['resource_guid'] = self.bones.short_id
        fields['resourceid'] = self.bones.short_id
        fields['resource_type'] = self.bones.resource_type
        value = Variable.format_kwargs(**fields)
        Variable.objects.create(session=session, name='app_launch',
                                type=Variable.encode_type(value),
                                value=Variable.encode(value),
                                last_resource_id=self.bones.short_id,
                                resource=self.bones,
                                rest=False,
                                landing=False)
        records = Features.resource_apps(self.start_date, self.end_date)
        self.assertEqual(len(records), 1)
        test = {}
        test[self.bones.short_id] = [self.dog.username]
        self.assertCountEqual(records[self.bones.short_id], test[self.bones.short_id])

    def test_user_apps(self):
        visitor = Visitor.objects.get(user=self.dog)
        session = Session.objects.get(visitor=visitor)
        fields = {}
        fields['filename'] = 'test_file'
        fields['resource_size_bytes'] = self.bones.size
        fields['resource_guid'] = self.bones.short_id
        fields['resourceid'] = self.bones.short_id
        fields['resource_type'] = self.bones.resource_type
        value = Variable.format_kwargs(**fields)
        Variable.objects.create(session=session, name='app_launch',
                                type=Variable.encode_type(value),
                                value=Variable.encode(value),
                                last_resource_id=self.bones.short_id,
                                resource=self.bones,
                                rest=False,
                                landing=False)
        records = Features.user_apps(self.start_date, self.end_date)
        self.assertEqual(len(records), 1)
        test = {}
        test[self.dog.username] = [self.bones.short_id]
        self.assertCountEqual(records[self.dog.username], test[self.dog.username])

    def test_user_favorites(self):
        cat = self.cat
        posts = self.posts
        cat.ulabels.favorite_resource(posts)
        records = Features.user_favorites()
        self.assertEqual(len(records), 1)
        test = {}
        test[cat.username] = [posts.short_id]
        self.assertCountEqual(test[cat.username], records[cat.username])

    def test_my_resources(self):
        cat = self.cat
        posts = self.posts
        cat.ulabels.claim_resource(posts)
        records = Features.user_my_resources()
        self.assertEqual(len(records), 1)
        test = {}
        test[cat.username] = [posts.short_id]
        self.assertCountEqual(test[cat.username], records[cat.username])

    def test_user_owned_groups(self):
        records = Features.user_owned_groups()
        self.assertEqual(len(records), 2)
        test = {}
        test[self.cat.username] = [self.cats.name]
        test[self.dog.username] = [self.dogs.name]
        self.assertCountEqual(test, records)

    def test_user_edit_groups(self):
        records = Features.user_edited_groups()
        self.assertEqual(len(records), 1)
        test = {}
        test[self.squirrel.username] = self.cats.name
        self.assertCountEqual(test, records)

    def test_user_viewed_groups(self):
        records = Features.user_viewed_groups()
        self.assertEqual(len(records), 1)
        test = {}
        test[self.squirrel.username] = self.dogs.name
        self.assertCountEqual(test, records)

    def test_resources_editable_via_group(self):
        records = Features.resources_editable_via_group(self.cats)
        self.assertEqual(len(records), 1)
        test = [self.posts.short_id]
        self.assertCountEqual(test, records)

    def test_resources_viewable_via_group(self):
        records = Features.resources_viewable_via_group(self.dogs)
        self.assertEqual(len(records), 1)
        test = [self.bones.short_id]
        self.assertCountEqual(test, records)
