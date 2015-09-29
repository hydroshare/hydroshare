import unittest

from django.contrib.auth.models import User, Group

from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.hydroshare.users import create_account
from hs_core.models import GenericResource


class TestAddResourceFiles(unittest.TestCase):
    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

    def tearDown(self):
        User.objects.filter(username='shaun').delete()
        self.group.delete()
        GenericResource.objects.all().delete()

    def test_add_files(self):
        user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        # create files
        n1 = "test.txt"
        n2 = "test2.txt"
        n3 = "test3.txt"

        open(n1, "w").close()
        open(n2, "w").close()
        open(n3, "w").close()

        # open files for read
        myfile = open(n1, "r")
        myfile1 = open(n2, "r")
        myfile2 = open(n3, "r")

        # create a resource
        res = create_resource(resource_type='GenericResource',
                              owner=user,
                              title='Test Resource',
                              metadata=[],)

        # delete all resource files for created resource
        res.files.all().delete()

        # add files
        add_resource_files(res.short_id, myfile, myfile1, myfile2)

        # add each file of resource to list
        res = get_resource_by_shortkey(res.short_id)
        l = []
        for f in res.files.all():
            l.append(f.resource_file.name.split('/')[-1])

        # check if the file name is in the list of files
        self.assertTrue(n1 in l, "file 1 has not been added")
        self.assertTrue(n2 in l, "file 2 has not been added")
        self.assertTrue(n3 in l, "file 3 has not been added")
