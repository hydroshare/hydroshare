from hs_core.hydroshare import resource
from django.test.testcases import TestCase

from django.contrib.auth.models import Group

from hs_core.hydroshare import users
from django_irods.storage import IrodsStorage


class TestStorage(TestCase):
    def setUp(self):
        super(TestStorage, self).setUp()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False)

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        self.res = resource.create_resource(self.rtype, self.user, self.title)

        self.pid = self.res.short_id

    def tearDown(self):
        resource.delete_resource(self.pid)
        self.group.delete()
        self.user.delete()

    def test_listdir_replicas(self):
        def mocked_ils_l(self, path):
            return "/hydroshareZone/home/wwwHydroProxy" \
                   "/ff7435cd22d94914ad3a674c40b229e9/data/contents:\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         9191 2018-01-21.15:09 & CRB METHODS.csv\n" \
                "  wwwHydroProx      1 hydroshareReplResc;mdcRRResource;hydrodata2Resource" \
                   "         9191 2018-01-21.15:09 & CRB METHODS.csv\n" \
                "  wwwHydroProx      2 hydroshareReplResc;mdcRRResource;hydrodata1Resource" \
                   "         9191 2018-01-26.12:08 & CRB METHODS.csv\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         6195 2018-01-21.15:09 & CRB_SITES.csv\n" \
                "  wwwHydroProx      1 hydroshareReplResc;mdcRRResource;hydrodata1Resource" \
                   "         6195 2018-01-26.12:08 & CRB_SITES.csv\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         7118 2018-01-21.15:09 & CZO_CRB_WCC_KARWAN_STABLEISOTOPE.csv\n" \
                "  wwwHydroProx      1 hydroshareReplResc;mdcRRResource;hydrodata1Resource" \
                   "         7118 2018-01-26.12:08 & CZO_CRB_WCC_KARWAN_STABLEISOTOPE.csv\n"
        storage = self.res.get_irods_storage()
        funcType = type(IrodsStorage.ils_l)
        storage.ils_l = funcType(mocked_ils_l, storage, IrodsStorage)

        listing = storage.listdir("path")
        self.assertEqual(len(listing[1]), 3)

    def test_listdir(self):
        def mocked_ils_l(self, path):
            return "/hydroshareZone/home/wwwHydroProxy" \
                   "/ff7435cd22d94914ad3a674c40b229e9/data/contents:\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         9191 2018-01-21.15:09 & CRB METHODS.csv\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         6195 2018-01-21.15:09 & CRB_SITES.csv\n" \
                "  wwwHydroProx      0 hydroshareReplResc;hydroshareResc" \
                   "         7118 2018-01-21.15:09 & CZO_CRB_WCC_KARWAN_STABLEISOTOPE.csv\n"
        storage = self.res.get_irods_storage()
        funcType = type(IrodsStorage.ils_l)
        storage.ils_l = funcType(mocked_ils_l, storage, IrodsStorage)

        listing = storage.listdir("path")
        self.assertEqual(len(listing[1]), 3)
