import os
import time
from unittest import TestCase

from django.contrib.auth.models import Group

from hs_core.hydroshare import resource
from hs_core.hydroshare.resource import add_resource_files
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from django.conf import settings


class TestUpdateQuotaUsage(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestUpdateQuotaUsage, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create two users
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='test_user',
            first_name='test_user_first_name',
            last_name='test_user_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        # create file
        self.n = "test.txt"
        test_file = open(self.n, 'w')
        test_file.write("Test text file in test.txt")
        test_file.close()
        # open file for read and upload
        self.myfile = open(self.n, "r")

    def tearDown(self):
        super(TestUpdateQuotaUsage, self).tearDown()
        self.myfile.close()
        os.remove(self.myfile.name)

    def test_update_quota_usage(self):
        res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

        self.assertTrue(res.creator == self.user)
        self.assertTrue(res.get_quota_holder() == self.user)
        # COMMENTED THE FOLLOWING TEST CODE FOR NOW SINCE IRODS PROXY USER DOES NOT HAVE PERMISSION
        # TO SET USER TYPE AVU ON IT ALTHOUGH RODS SERVICE USER HAS PERMISSION TO DO SO. WILL
        # UPDATE THE TEST ACCORDINGLY AFTER THIS PERMISSION ISSUE IS WORKED OUT
        # attname = self.user.username + '-quota'
        # test_qsize = 2 # unit: GB
        # this quota size AVU will be set by real time iRODS quota usage update micro-services.
        # For testing, setting it programmatically to test the quota size will be picked up
        # automatically when files are added into this resource
        # istorage = res.get_irods_storage()
        # data_proxy_name = settings.IRODS_USERNAME + '#' + settings.HS_WWW_IRODS_ZONE
        # istorage.setAVU(data_proxy_name, attname, str(test_qsize), type='-u')
        # get_qsize = istorage.getAVU(data_proxy_name, attname, type='-u')
        # self.assertEqual(test_qsize, int(get_qsize))

        # add_resource_files(res.short_id, self.myfile)
        # wait up to 70 seconds to accommodate celery quota update task being triggered in 60
        # seconds in order to give some time for iRODS micro-services to finish updating quota
        # calculation and update
        # for i in range(35):
        #    uquota = self.user.quotas.first()
        #    if uquota == test_qsize:
        #        break
        #    time.sleep(2)
        # self.assertEqual(uquota.used_value, test_qsize)

        if res:
            res.delete()
