import os

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.hydroshare.hs_bagit import create_bag_files 
from hs_core.tasks import create_bag_by_irods

from pprint import pprint


class TestTickets(MockIRODSTestCaseMixin, TestCase):
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
            'GenericResource',
            self.user,
            'test resource',
        )
        self.res.save()

        # create a file
        self.test_file_name1 = 'file1.txt'
        self.file_name_list = [self.test_file_name1, ]

        # put predictable contents into the file
        test_file = open(self.test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        self.test_file_1 = open(self.test_file_name1, 'r')

        # add one file to the resource: necessary so data/contents is created.
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1)

    def tearDown(self):
        super(TestTickets, self).tearDown()
        self.test_file_1.close()
        os.remove(self.test_file_1.name)

    def test_get_file_read_ticket(self):
        file = self.res.files.all()[0]
        print(file.storage_path)
        ticket = file.create_ticket(self.user)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(file.storage_path))
        self.assertEqual(file.short_path, attrs['filename'])
        self.res.delete_ticket(self.user, ticket)

    def test_get_dir_read_ticket(self):
        print(self.res.file_path)
        ticket = self.res.create_ticket(self.user, self.res.file_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.file_path))
        self.res.delete_ticket(self.user, ticket)

    def test_get_meta_read_ticket(self):
        print("getting ticket for {}".format(self.res.scimeta_path))

        # print("testing: creating bag files for {}".format(self.res.short_id))
        # create_bag_files(self.res)
        # print("testing: create_bag_by_irods for {}".format(self.res.short_id))
        # create_bag_by_irods(self.res.short_id)

        istorage = self.res.get_irods_storage()
        stuff = istorage.listdir(os.path.join(self.res.root_path, 'data')) 
        pprint(stuff) 
        ticket = self.res.create_ticket(self.user, self.res.scimeta_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.scimeta_path))
        self.res.delete_ticket(self.user, ticket)

    def test_get_map_read_ticket(self):
        print("getting ticket for {}".format(self.res.resmap_path))

        # print("testing: creating bag files for {}".format(self.res.short_id))
        # create_bag_files(self.res)
        # print("testing: create_bag_by_irods for {}".format(self.res.short_id))
        # create_bag_by_irods(self.res.short_id)

        istorage = self.res.get_irods_storage() 
        stuff = istorage.listdir(os.path.join(self.res.root_path, 'data')) 
        pprint(stuff) 
        ticket = self.res.create_ticket(self.user, self.res.resmap_path)
        attrs = self.res.list_ticket(ticket)
        print("full_path = {}, resmap_path = {}".format(attrs['full_path'], self.res.resmap_path))
        self.assertTrue(attrs['full_path'].endswith(self.res.resmap_path))
        self.res.delete_ticket(self.user, ticket)

    def test_get_bag_read_ticket(self):
        print("getting ticket for {}".format(self.res.bag_path))

        # print("testing: creating bag files for {}".format(self.res.short_id))
        # create_bag_files(self.res)
        # print("testing: create_bag_by_irods for {}".format(self.res.short_id))
        # create_bag_by_irods(self.res.short_id)

        istorage = self.res.get_irods_storage() 
        stuff = istorage.listdir('bags') 
        pprint(stuff) 
        ticket = self.res.create_ticket(self.user, self.res.bag_path)
        attrs = self.res.list_ticket(ticket)
        self.assertTrue(attrs['full_path'].endswith(self.res.bag_path))
        self.res.delete_ticket(self.user, ticket)

