class MockIRODSTestCaseMixin(object):
    def setUp(self):
        super(MockIRODSTestCaseMixin, self).setUp()
        from mock import patch
        self.irods_patchers = (
            patch("hs_core.hydroshare.hs_bagit.delete_bag"),
            patch("hs_core.hydroshare.hs_bagit.create_bag"),
            patch("hs_core.hydroshare.hs_bagit.create_bag_files"),
            patch("hs_core.hydroshare.hs_bagit.create_bag_by_irods"),
            patch("hs_core.hydroshare.utils.copy_resource_files_and_AVUs"),
        )
        for patcher in self.irods_patchers:
            patcher.start()

    def tearDown(self):
        for patcher in self.irods_patchers:
            patcher.stop()
        super(MockIRODSTestCaseMixin, self).tearDown()
