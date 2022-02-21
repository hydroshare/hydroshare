from django.test import TestCase
from hs_linux.storage import LinuxStorage
import os
import shutil


class LinuxStorageTest(TestCase):
    def setUp(self):
        if (not os.path.exists("./test")):
            os.makedirs("./test/subtest1")
            os.makedirs("./test/subtest2")
            os.chdir("./test")
            open("testfile.txt", "w+")
            os.chdir("./subtest1")
            open("testfile11.txt", "w+")
            open("testfile12.txt", "w+")
            os.chdir("../subtest2")
            open("testfile21.txt", "w+")
            open("testfile22.txt", "w+")
            os.chdir("../../")

    def tearDown(self):
        for root, dirs, files in os.walk("./test", topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.removedirs(os.path.join(root, name))

    def test_savefile(self):
        LinuxStorage.saveFile(LinuxStorage, "./test/subtest2/testfile21.txt", "test2")
        self.assertTrue(os.path.exists("./irods/test2"))

        LinuxStorage.saveFile(LinuxStorage, "./test/subtest1", "test1")
        LinuxStorage.saveFile(LinuxStorage, "./test/subtest1", "test1")
        self.assertTrue(os.path.exists("./irods/test1"))
        self.assertTrue(os.path.exists("./irods/test1/subtest1"))
        self.assertTrue(os.path.exists("./irods/test1/testfile11.txt"))
        self.assertTrue(os.path.exists("./irods/test1/testfile12.txt"))
        shutil.rmtree("./irods")

    def test_movefile(self):
        LinuxStorage.saveFile(LinuxStorage, "./test", "./")
        print("Here!!!")
        # file --> directory
        LinuxStorage.moveFile(LinuxStorage, "test/testfile.txt", "test/subtest1")
        self.assertTrue(os.path.exists("./irods/test/subtest1/testfile.txt"))
        self.assertFalse(os.path.exists("./irods/test/testfile.txt"))

        # directory -> directory
        LinuxStorage.moveFile(LinuxStorage, "test/subtest2", "test/subtest1")
        self.assertTrue(os.path.exists("./irods/test/subtest1/subtest2/testfile21.txt"))
        self.assertTrue(os.path.exists("./irods/test/subtest1/subtest2/testfile22.txt"))
        self.assertFalse(os.path.exists("./irods/test/subtest2"))

        # file -> file
        with open('./irods/test/subtest1/testfile11.txt') as f:
            testfile11_string = f.read()
        LinuxStorage.moveFile(LinuxStorage, "test/subtest1/testfile11.txt", "test/subtest1/subtest2/testfile22.txt")
        with open('./irods/test/subtest1/subtest2/testfile22.txt') as f:
            testfile22_string = f.read()
        self.assertTrue(testfile11_string == testfile22_string)
        self.assertFalse(os.path.exists("./irods/test/subtest1/testfile11.txt"))

        shutil.rmtree("./irods")

    def test_getfile(self):
        os.makedirs("./irods/manish/aryal")
        os.makedirs("./irods/alva/couch")
        os.makedirs("linuxtest")
        open("./irods/manish/aryal/manishfile.txt", "w+")
        open("./irods/alva/couch/alvafile.txt", "w+")

        LinuxStorage.getFile(LinuxStorage, "manish", "linuxtest")
        self.assertTrue(os.path.exists("./linuxtest/manish"))

        LinuxStorage.getFile(LinuxStorage, "./alva/couch/alvafile.txt", "linuxtest")
        self.assertTrue(os.path.exists("./linuxtest/alvafile.txt"))
        shutil.rmtree("./irods")
        shutil.rmtree("./linuxtest")

    def test_copyfile(self):
        LinuxStorage.saveFile(LinuxStorage, "./test", "./")
        print("Here!!!")
        # file --> directory
        LinuxStorage.copyFiles(LinuxStorage, "test/testfile.txt", "test/subtest1")
        self.assertTrue(os.path.exists("./irods/test/subtest1/testfile.txt"))
        self.assertTrue(os.path.exists("./irods/test/testfile.txt"))

        # directory -> directory
        LinuxStorage.copyFiles(LinuxStorage, "test/subtest2", "test/subtest1")
        self.assertTrue(os.path.exists("./irods/test/subtest1/subtest2/testfile21.txt"))
        self.assertTrue(os.path.exists("./irods/test/subtest1/subtest2/testfile22.txt"))
        self.assertTrue(os.path.exists("./irods/test/subtest2"))

        # file -> file
        with open('./irods/test/subtest1/testfile11.txt') as f:
            testfile11_string = f.read()
        LinuxStorage.copyFiles(LinuxStorage, "test/subtest1/testfile11.txt", "test/subtest1/subtest2/testfile22.txt")
        with open('./irods/test/subtest1/subtest2/testfile22.txt') as f:
            testfile22_string = f.read()
        self.assertTrue(testfile11_string == testfile22_string)
        self.assertTrue(os.path.exists("./irods/test/subtest1/testfile11.txt"))

        shutil.rmtree("./irods")


'''
storage class methods     | filesystem storage class
open                      | base_location
save                      | location
get_valid_name            | base_url
get_available_name ..     | file_permissions_mode
generate_filename         | directory_permissions_mode
path                      | get_storage_class
delete ..
exists ..
lsitdir ..
size ..
url ..
get_accessed_time
get_created_time
get_modified_time
'''
