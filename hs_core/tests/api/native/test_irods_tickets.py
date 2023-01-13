import os

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.core.exceptions import ValidationError

from hs_core import hydroshare
from hs_core.models import BaseResource


class TestTickets(TestCase):
    def setUp(self):
        super(TestTickets, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'test resource',
        )

        # create a file
        self.test_file_name1 = 'file1.txt'
        self.file_name_list = [self.test_file_name1, ]

        # put predictable contents into the file
        test_file = open(self.test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        self.test_file_1 = open(self.test_file_name1, 'rb')

        # add one file to the resource: necessary so data/contents is created.
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1)

    def tearDown(self):
        super(TestTickets, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()
        self.test_file_1.close()
        os.remove(self.test_file_1.name)

    def test_get_file_read_ticket(self):
        file = self.res.files.all()[0]
        ticket, path = file.create_ticket(self.user)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(file.storage_path))
        self.assertEqual(file.short_path, attrs['filename'])
        self.res.delete_ticket(self.user, ticket)
        with self.assertRaises(ValidationError):
            self.res.list_ticket(ticket)

    def test_get_dir_read_ticket(self):
        ticket, path = self.res.create_ticket(self.user, self.res.file_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.file_path))
        self.res.delete_ticket(self.user, ticket)
        with self.assertRaises(ValidationError):
            self.res.list_ticket(ticket)

    def test_get_meta_read_ticket(self):
        ticket, path = self.res.create_ticket(self.user, self.res.scimeta_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.scimeta_path))
        self.res.delete_ticket(self.user, ticket)
        with self.assertRaises(ValidationError):
            self.res.list_ticket(ticket)

    def test_get_map_read_ticket(self):
        ticket, path = self.res.create_ticket(self.user, self.res.resmap_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.resmap_path))
        self.res.delete_ticket(self.user, ticket)
        with self.assertRaises(ValidationError):
            self.res.list_ticket(ticket)

    def test_get_bag_read_ticket(self):
        ticket, path = self.res.create_ticket(self.user, self.res.bag_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.bag_path))
        self.res.delete_ticket(self.user, ticket)
        with self.assertRaises(ValidationError):
            self.res.list_ticket(ticket)
