import os
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
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        self.res = create_resource(resource_type='CompositeResource',
                                   owner=self.user,
                                   title='Test Resource',
                                   metadata=[])

        ResourceFile.create_folder(self.res, 'foo')

        # create files
        self.n1 = "test1.txt"
        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()

        self.test_file = open(self.n1, "r")
        add_resource_files(self.res.short_id, self.test_file, folder='foo')

        # copy refts file into new file to be added to the resource as an aggregation
        reft_data_file = open('hs_core/tests/data/multi_sites_formatted_version1.0.refts.json', 'r')
        refts_file = open('multi_sites_formatted_version1.0.refts.json', 'w')
        refts_file.writelines(reft_data_file.readlines())
        refts_file.close()
        self.refts_file = open('multi_sites_formatted_version1.0.refts.json', 'r')

        add_resource_files(self.res.short_id, self.refts_file)
        self.res.create_aggregation_xml_documents()

    def tearDown(self):
        super(TestFolderDownloadZip, self).tearDown()
        if self.res:
            self.res.delete()
        if self.test_file:
            os.remove(self.test_file.name)
        if self.refts_file:
            os.remove(self.refts_file.name)
        GenericResource.objects.all().delete()
        istorage = IrodsStorage()
        if istorage.exists("zips"):
            istorage.delete("zips")

    def test_create_temp_zip(self):
        input_path = "/data/contents/foo"
        output_path = "zips/rand/foo.zip"

        self.assertTrue(create_temp_zip(self.res.short_id, input_path,
                                        output_path, False))
        self.assertTrue(IrodsStorage().exists(output_path))

        # test aggregation
        input_path = "/data/contents/multi_sites_formatted_version1.0.refts.json"
        output_path = "zips/rand/multi_sites_formatted_version1.0.refts.json.zip"

        self.assertTrue(create_temp_zip(self.res.short_id, input_path,
                                        output_path, True))
        self.assertTrue(IrodsStorage().exists(output_path))
