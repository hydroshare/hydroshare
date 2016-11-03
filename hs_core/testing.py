from django.conf import settings


class MockIRODSTestCaseMixin(object):
    def setUp(self):
        super(MockIRODSTestCaseMixin, self).setUp()
        # only mock up testing iRODS operations when local iRODS container is not used
        if settings.IRODS_HOST != 'data.local.org':
            from mock import patch
            self.irods_patchers = (
                patch("hs_core.hydroshare.hs_bagit.delete_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag"),
                patch("hs_core.hydroshare.hs_bagit.create_bag_files"),
                patch("hs_core.tasks.create_bag_by_irods"),
                patch("hs_core.hydroshare.utils.copy_resource_files_and_AVUs"),
            )
            for patcher in self.irods_patchers:
                patcher.start()

    def tearDown(self):
        if settings.IRODS_HOST != 'data.local.org':
            for patcher in self.irods_patchers:
                patcher.stop()
        super(MockIRODSTestCaseMixin, self).tearDown()
