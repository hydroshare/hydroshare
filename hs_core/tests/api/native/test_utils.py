from unittest import TestCase
from hs_core.hydroshare import utils
from hs_core.models import GenericResource
from django.contrib.auth.models import Group, User
from hs_core import hydroshare
from dublincore.models import QualifiedDublinCoreElement
#from hs_scholar_profile.models import *

class TestUtils(TestCase):
    def setUp(self):
        try:
            #self.user = User.objects.create_user('user1', email='user1@nowhere.com')
            self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
            self.user = hydroshare.create_account(
                'user1@nowhere.com',
                username='user1',
                first_name='Creator_FirstName',
                last_name='Creator_LastName',
                superuser=False,
                groups=[self.group]
            )

            # create dublin core elements
            self.dublin_metadata = []

        except:
            self.tearDown()
            self.user = User.objects.create_user('user1', email='user1@nowhere.com')

        #self.group, _ = Group.objects.get_or_create(name='group1')
        self.res, created = GenericResource.objects.get_or_create(
            user=self.user,
            title='resource',
            creator=self.user,
            last_changed_by=self.user,
            doi='doi1000100010001'
        )
        if created:
            self.res.owners.add(self.user)


    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        QualifiedDublinCoreElement.objects.all().delete()


    def test_get_resource_types(self):
        # first time gets them anew
        self.assertListEqual(
            [GenericResource],
            utils.get_resource_types(),
            msg="Resource types was more than just [GenericResource]")

        # second time gets cached instances
        self.assertListEqual(
            [GenericResource],
            utils.get_resource_types(),
            msg="Resource types was more than just [GenericResource] using cached resource types")

    def test_get_resource_instance(self):
        self.assertEqual(
            utils.get_resource_instance('hs_core', 'GenericResource', self.res.pk),
            self.res
        )

    def test_get_resource_by_shortkey(self):
        self.assertEqual(
            utils.get_resource_by_shortkey(self.res.short_id),
            self.res
        )

    def test_get_resource_by_doi(self):
        self.assertEqual(
            utils.get_resource_by_doi('doi1000100010001'),
            self.res
        )

    def test_user_from_id(self):
        self.assertEqual(
            utils.user_from_id(self.user),
            self.user,
            msg='user passthrough failed'
        )

        self.assertEqual(
            utils.user_from_id('user1@nowhere.com'),
            self.user,
            msg='lookup by email address failed'
        )

        self.assertEqual(
            utils.user_from_id('user1'),
            self.user,
            msg='lookup by username failed'
        )

    def test_group_from_id(self):
        self.assertEqual(
            utils.group_from_id(self.group),
            self.group,
            msg='group passthrough failed'
        )

        self.assertEqual(
            utils.group_from_id('group1'),
            self.group,
            msg='lookup by group name failed'
        )


    # not really a unit test. primarily this function
    # allows us to see the generated science metadata xml
    def test_serialize_science_metadata_xml(self):

        QualifiedDublinCoreElement.objects.create(
            term='AB',
            qualifier=None,
            content='This a sample abstract.',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='CN',
            qualifier=None,
            content='Contributor_1',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='CN',
            qualifier=None,
            content='Contributor_2',
            content_object=self.res
        )

        contributor_3 = hydroshare.create_account(
            'contributor_3@usu.edu',
            username='contributor_3',
            first_name='Contributor',
            last_name='_3',
            superuser=False,
            groups=[self.group]
        )
        QualifiedDublinCoreElement.objects.create(
            term='CN',
            qualifier=None,
            content='contributor_3@usu.edu',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='DSC',
            qualifier=None,
            content='This a sample description of the resource.',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='CR',
            qualifier=None,
            content='Tian Gan.',
            content_object=self.res
        )

        creator_2 = hydroshare.create_account(
            'creator_2@usu.edu',
            username='creator_2',
            first_name='Creator',
            last_name='_2',
            superuser=False,
            groups=[self.group]
        )

        creator_3 = hydroshare.create_account(
            'creator_3@usu.edu',
            username='creator_3',
            first_name='Creator',
            last_name='_3',
            superuser=False,
            groups=[self.group]
        )

        QualifiedDublinCoreElement.objects.create(
            term='CR',
            qualifier=None,
            content='creator_2@usu.edu',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='CR',
            qualifier=None,
            content='creator_3@usu.edu',
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='DTS',
            qualifier=None,
            content="2014-07-14T16:31:08.429890+00:00",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='FMT',
            qualifier=None,
            content="text/csv",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='FMT',
            qualifier=None,
            content="application/netCDF",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='LG',
            qualifier=None,
            content="eng",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='PBL',
            qualifier=None,
            content="http://hydroshare.org/",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='REL',
            qualifier=None,
            content="Mahat, V., and D. G. Tarboton (2012), Canopy radiation transmission for an energy balance snowmelt model, Water Resour. Res., 48, W01534.",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='RT',
            qualifier=None,
            content="http://creativecommons.org/licenses/by/3.0/",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='BX',
            qualifier=None,
            content="northlimit=4635150.0; southlimit=4634790.0; eastlimit=458010.0; westlimit=457560.0; units= meter; projection = UTM zone 12N",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='SRC',
            qualifier=None,
            content="Tarboton, D. G. and C. H. Luce, (1996), \'Utah Energy Balance Snow Accumulation and Melt Model (UEB),\' Computer model technical description and users guide, Utah Water Research Laboratory and USDA Forest Service Intermountain Research Station. http://www.engineering.usu.edu/dtarb/",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='SUB',
            qualifier=None,
            content="Snow water equivalent, Utah Energy Balance Model",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='T',
            qualifier=None,
            content="UEB MODEL SIMULATION OF SNOW WATER EQUIVALENT AT TWDEF SITE FROM OCT 2009 TO JUNE 2010",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='PD',
            qualifier=None,
            content="start= 2009-10-01; end= 2010-06-31; scheme=W3C-DTF;",
            content_object=self.res
        )

        QualifiedDublinCoreElement.objects.create(
            term='TYP',
            qualifier=None,
            content="NetCDf Resource",
            content_object=self.res
        )

        xml = utils.serialize_science_metadata_xml(self.res)
        print(xml)

        # knowingly have this buggy statement so that I (Pabitra) can see the output of the above print statement
        print(xml1)