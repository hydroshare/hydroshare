import unittest
from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.hydroshare.resource import add_resource_files, create_resource, get_resource_map
from django.contrib.auth.models import User
from hs_core.models import ResourceFile
from hs_core.models import GenericResource

class testAddResourceFiles(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        User.objects.filter(username='shaun').delete() #delete user after test is done

    def test_add_files(self):
        user = User.objects.create_user('shaun', 'shauntheta@gmail.com', 'shaun6745') #create user

        #create files
        n1 = "test.txt"
        n2 = "test2.txt"
        n3 = "test3.txt"

        open(n1,"w").close() #files are created
        open(n2,"w").close()
        open(n3,"w").close()

        myfile = open(n1,"r") #files are opened as 'read-only'
        myfile1 = open(n2,"r")
        myfile2 = open(n3,"r")

        res1 = create_resource('GenericResource',user,'res1') #create resource

        #delete all resource files for created resource
        res1.files.all().delete()

        #add files
        add_resource_files(res1.short_id,myfile,myfile1,myfile2)

        #add each file of resource to list
        res1 = get_resource_by_shortkey(res1.short_id)
        l=[]
        for f in res1.files.all():
            l.append(f.resource_file.name.split('/')[-1])

        #check if the file name is in the list of files
        self.assertTrue(n1 in l, "file 1 has not been added")
        self.assertTrue(n2 in l, "file 2 has not been added")
        self.assertTrue(n3 in l, "file 3 has not been added")

        
