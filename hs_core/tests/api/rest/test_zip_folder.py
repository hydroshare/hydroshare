import os
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.views.utils import zip_folder
from hs_core.hydroshare.utils import QuotaException

from .base import HSRESTTestCase


class TestPublicZipEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicZipEndpoint, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        self.res = resource.create_resource(self.rtype, self.user, self.title, unpack_file=False)

        self.pid = self.res.short_id
        self.resources_to_delete.append(self.pid)

        # create a folder 'foo'
        url = str.format('/hsapi/resource/{}/folders/foo/', self.pid)
        self.client.put(url, {})

        # put a file 'test.txt' into folder 'foo'
        url2 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': ('text.txt',
                           open(self.txt_file_path, 'rb'),
                           'text/plain')}
        self.client.post(url2, params)

        # put a file 'cea.tif' into folder 'foo'
        url3 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': (self.raster_file_name,
                           open(self.raster_file_path, 'rb'),
                           'image/tiff')}
        self.client.post(url3, params)

    def test_zip_folder_bad_requests(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid

        response_no_path = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip"
        }, format="json")
        response_empty_path = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip"
        }, format="json")
        response_no_fname = self.client.post(zip_url, {
            "output_zip_file_name": " ",
            "input_coll_path": "/files/foo"
        }, format="json")
        response_empty_fname = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip",
            "input_coll_path": " "
        }, format="json")

        self.assertEqual(response_no_path.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_empty_path.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_no_fname.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_empty_fname.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zip_folder(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid
        response = self.client.post(zip_url, {
            "input_coll_path": "data/contents/foo",
            "output_zip_file_name": "test.zip",
            "remove_original_after_zip": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zip_aggregation(self):
        zip_url = "/hsapi/resource/%s/functions/zip-by-aggregation-file/" % self.pid
        raster_vrt_filename, _ = os.path.splitext(self.raster_file_name)
        raster_vrt_filename = f"{raster_vrt_filename}.vrt"
        response = self.client.post(zip_url, {
            "aggregation_path": f"data/contents/foo/{raster_vrt_filename}",
            "output_zip_file_name": "test.zip"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zip_folder_remove(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid
        response = self.client.post(zip_url, {
            "input_coll_path": "data/contents/foo",
            "output_zip_file_name": "test.zip",
            "remove_original_after_zip": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zip_over_quota(self):
        """
        Test case for zipping a folder when the user is over the quota limit.

        This test case verifies that the `zip_folder` function raises a `QuotaException` when the user is over the quota
        limit and the quota enforce flag is set to True. It also checks that the function does not raise a
        `QuotaException` when the quota enforce flag is set to False.

        Steps:
        1. Create a composite resource.
        2. Create three test files.
        3. Open the files for read and upload.
        4. Add the files to the resource.
        5. Set the user's quota over the hard limit.
        6. Verify that zipping the folder raises a `QuotaException`.
        7. Verify that zipping the files does not raise a `QuotaException` when `bool_remove_original` is set to True.
        8. Increase the user's quota.
        9. Add the files to a different folder.
        10. Verify that zipping the files does not raise a `QuotaException` when quota enforcement is disabled.

        """
        self.res = resource.create_resource(resource_type='CompositeResource',
                                            owner=self.user,
                                            title='Test Resource',
                                            metadata=[], )

        # create files
        self.n1 = "test1.txt"
        self.n2 = "test2.txt"
        self.n3 = "test3.txt"

        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()

        test_file = open(self.n2, 'w')
        test_file.write("Test text file in test2.txt")
        test_file.close()

        test_file = open(self.n3, 'w')
        test_file.write("Test text file in test3.txt")
        test_file.close()

        # open files for read and upload
        self.myfile1 = open(self.n1, "rb")
        self.myfile2 = open(self.n2, "rb")
        self.myfile3 = open(self.n3, "rb")

        resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3, folder='test')

        uquota = self.user.quotas.first()
        # make user's quota over hard limit 125%
        from hs_core.tests.utils.test_utils import set_quota_usage_over_hard_limit, wait_for_quota_update
        set_quota_usage_over_hard_limit(uquota)
        uquota.save()

        # zip should raise quota exception now that the quota holder is over hard limit
        with self.assertRaises(QuotaException):
            zip_folder(self.user, self.res.short_id, 'data/contents/test', 'test.zip', bool_remove_original=False)

        # Zip should raise quota exception now that the quota holder is over hard limit and minio is enforcing quota
        with self.assertRaises(QuotaException):
            zip_folder(self.user, self.res.short_id, 'data/contents/test', 'test.zip', bool_remove_original=True)

        uquota.save_allocated_value(20, "GB")
        wait_for_quota_update()

        resource.add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3, folder='test2')
        # zip files should not raise quota exception since the user has quota
        try:
            zip_folder(self.user, self.res.short_id, 'data/contents/test2', 'test2.zip', bool_remove_original=False)
        except QuotaException as ex:
            self.fail("zip resource file action should not raise QuotaException for "
                      "over quota cases if quota is not enforced - Quota Exception: " + str(ex))

        self.myfile1.close()
        os.remove(self.myfile1.name)
        self.myfile2.close()
        os.remove(self.myfile2.name)
        self.myfile3.close()
        os.remove(self.myfile3.name)
