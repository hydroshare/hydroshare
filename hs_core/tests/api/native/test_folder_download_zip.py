from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.hydroshare.users import create_account
from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.models import GenericResource
from hs_core.tasks import create_temp_zip
from django_irods.storage import IrodsStorage
from hs_core.models import ResourceFile


class TestFolderDownloadZip(TestCase):

    def setUp(self):
        super(TestFolderDownloadZip, self).setUp()
        self.output_path = "zips/rand/foo.zip"
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        # create files
        self.n1 = "test1.txt"

        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()

        test_file = open(self.n1, "r")

        self.res = create_resource(resource_type='GenericResource',
                                   owner=self.user,
                                   title='Test Resource',
                                   metadata=[], )

        ResourceFile.create_folder(self.res, 'foo')

        # add one file to the resource
        add_resource_files(self.res.short_id, test_file, folder='foo')

    def tearDown(self):
        super(TestFolderDownloadZip, self).tearDown()
        if self.res:
            self.res.delete()
        GenericResource.objects.all().delete()
        istorage = IrodsStorage()
        if istorage.exists(self.output_path):
            istorage.delete(self.output_path)

    def test_create_temp_zip(self):
        input_path = "/data/contents/foo"
        try:
            self.assertTrue(create_temp_zip(self.res.short_id, input_path,
                                            self.output_path))
            self.assertTrue(IrodsStorage().exists(self.output_path))
        except Exception as ex:
            self.fail("create_temp_zip() raised exception.{}".format(ex.message))
