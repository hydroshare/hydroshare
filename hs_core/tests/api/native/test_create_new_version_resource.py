import os
import tempfile
import shutil

from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from hs_core import hydroshare
from hs_core.models import GenericResource
from hs_core.hydroshare import utils
from hs_access_control.models import PrivilegeCodes
from hs_geo_raster_resource.models import RasterResource, OriginalCoverage, CellInformation, BandInformation

class TestNewVersionResource(TestCase):
    def setUp(self):
        super(TestNewVersionResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user who is the owner of the resource to be versioned
        self.owner = hydroshare.create_account(
            'owner@gmail.edu',
            username='owner',
            first_name='owner_firstname',
            last_name='owner_lastname',
            superuser=False,
            groups=[]
        )

        # create a user who is NOT the owner of the resource to be versioned
        self.nonowner = hydroshare.create_account(
            'nonowner@gmail.com',
            username='nonowner',
            first_name='nonowner_firstname',
            last_name='nonowner_lastname',
            superuser=False,
            groups=[]
        )

        # create a generic resource
        self.res_generic = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.owner,
            title='Test Generic Resource'
        )

        # create a raster resource that represents a specific resource type
        raster_file = 'hs_core/tests/data/cea.tif'
        temp_dir = tempfile.mkdtemp()
        temp_raster_file = os.path.join(temp_dir, 'cea.tif')
        shutil.copy(raster_file, temp_raster_file)
        self.raster_obj = open(temp_raster_file, 'r')
        files = [UploadedFile(file=self.raster_obj, name='cea.tif')]
        _, _, metadata = utils.resource_pre_create_actions(resource_type='RasterResource',
                                                          resource_title='Test Raster Resource',
                                                          page_redirect_url_key=None,
                                                          files=files,
                                                          metadata=None,)
        self.res_raster = hydroshare.create_resource(
            resource_type='RasterResource',
            owner=self.owner,
            title='Test Raster Resource',
            files=files,
            metadata=metadata
        )

    def test_new_version_generic_resource(self):
        # test to make sure only owners can version a resource
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_generic.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.res_generic, self.nonowner, PrivilegeCodes.CHANGE)
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_generic.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.res_generic, self.nonowner, PrivilegeCodes.VIEW)
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_generic.short_id, self.nonowner)

        new_res_generic = hydroshare.create_new_version_empty_resource(self.res_generic.short_id, self.owner)
        new_res_generic = hydroshare.create_new_version_resource(self.res_generic, new_res_generic, self.owner)

        # test the new versioned resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res_generic, GenericResource))

        # test science metadata elements are copied from the original resource to the new versioned resource
        self.assertTrue(new_res_generic.metadata.title.value == self.res_generic.metadata.title.value)
        self.assertTrue(new_res_generic.creator == self.owner)

        # test to make sure a new unique identifier has been created for the new versioned resource
        self.assertIsNotNone(new_res_generic.short_id, msg='Unique identifier has not been created for new versioned resource.')
        self.assertNotEqual(new_res_generic.short_id, self.res_generic.short_id)

        # test to make sure the new versioned resource has no content files
        self.assertEqual(new_res_generic.files.all().count(), 0)
        # test to make sure the new versioned resource has the correct identifier
        self.assertEqual(new_res_generic.metadata.identifiers.all().count(), 1, msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier', [id.name for id in new_res_generic.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new versioned resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), new_res_generic.short_id)
        self.assertIn(id_url, [id.url for id in new_res_generic.metadata.identifiers.all()],
                      msg="Identifier url was not found for new versioned resource.")

        # test to make sure the new versioned resource is linked with the original resource via isReplacedBy and isVersionOf metadata elements
        self.assertGreater(new_res_generic.metadata.relations.all().count(), 0, msg="New versioned resource does has relation element.")
        self.assertIn('isVersionOf', [rel.type for rel in new_res_generic.metadata.relations.all()],
                      msg="No relation element of type 'isVersionOf' for new versioned resource")
        version_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), self.res_generic.short_id)
        self.assertIn(version_value, [rel.value for rel in new_res_generic.metadata.relations.all()],
                      msg="The original resource identifier is not set as value for isVersionOf for new versioned resource.")
        self.assertIn('isReplacedBy', [rel.type for rel in self.res_generic.metadata.relations.all()],
                      msg="No relation element of type 'isReplacedBy' for the original resource")
        version_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), new_res_generic.short_id)
        self.assertIn(version_value, [rel.value for rel in self.res_generic.metadata.relations.all()],
                      msg="The new versioned resource identifier is not set as value for isReplacedBy for original resource.")

        # test isReplacedBy is removed after the new versioned resource is deleted
        hydroshare.delete_resource(new_res_generic.short_id)
        self.assertNotIn('isReplacedBy', [rel.type for rel in self.res_generic.metadata.relations.all()],
                         msg="isReplacedBy is not removed from the original resource after its versioned resource is deleted")


    def test_new_version_raster_resource(self):
        # test to make sure only owners can version a resource
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_generic.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.res_raster, self.nonowner, PrivilegeCodes.CHANGE)
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_raster.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.res_raster, self.nonowner, PrivilegeCodes.VIEW)
        with self.assertRaises(ValidationError):
            hydroshare.create_new_version_empty_resource(self.res_raster.short_id, self.nonowner)

        new_res_raster = hydroshare.create_new_version_empty_resource(self.res_raster.short_id, self.owner)
        new_res_raster = hydroshare.create_new_version_resource(self.res_raster, new_res_raster, self.owner)

        # test the new versioned resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_res_raster, RasterResource))

        # test science metadata elements are copied from the original resource to the new versioned resource
        self.assertTrue(new_res_raster.metadata.title.value == self.res_raster.metadata.title.value)
        self.assertTrue(new_res_raster.creator == self.owner)

        # test extended metadata elements are copied from the original resource to the new versioned resource
        if OriginalCoverage.objects.filter(object_id=self.res_raster.metadata.id).exists():
            self.assertTrue(OriginalCoverage.objects.filter(object_id=new_res_raster.metadata.id).exists())
            self.assertEquals(new_res_raster.metadata.originalCoverage.value, self.res_raster.metadata.originalCoverage.value,
                              msg="OriginalCoverage of new versioned resource is not equal to that of the original resource")

        if CellInformation.objects.filter(object_id=self.res_raster.metadata.id).exists():
            self.assertTrue(CellInformation.objects.filter(object_id=new_res_raster.metadata.id).exists())
            newcell = new_res_raster.metadata.cellInformation
            oldcell = self.res_raster.metadata.cellInformation
            self.assertEquals(newcell.rows, oldcell.rows, msg="Rows of new versioned resource is not equal to that of the original resource")
            self.assertEquals(newcell.columns, oldcell.columns, msg="Columns of new versioned resource is not equal to that of the original resource")
            self.assertEquals(newcell.cellSizeXValue, oldcell.cellSizeXValue, msg="CellSizeXValue of new versioned resource is not equal to that of the original resource")
            self.assertEquals(newcell.cellSizeYValue, oldcell.cellSizeYValue, msg="CellSizeYValue of new versioned resource is not equal to that of the original resource")
            self.assertEquals(newcell.cellDataType, oldcell.cellDataType, msg="CellDataType of new versioned resource is not equal to that of the original resource")

        if BandInformation.objects.filter(object_id=self.res_raster.metadata.id).exists():
            self.assertTrue(BandInformation.objects.filter(object_id=new_res_raster.metadata.id).exists())
            newband = new_res_raster.metadata.bandInformation.first()
            oldband = self.res_raster.metadata.bandInformation.first()
            self.assertEquals(newband.name, oldband.name, msg="Band name of new versioned resource is not equal to that of the original resource")

        # test to make sure a new unique identifier has been created for the new versioned resource
        self.assertIsNotNone(new_res_raster.short_id, msg='Unique identifier has not been created for new versioned resource.')
        self.assertNotEqual(new_res_raster.short_id, self.res_raster.short_id)

        # test to make sure the new versioned resource has 1 content file
        self.assertEqual(new_res_raster.files.all().count(), 1)

        # test to make sure the new versioned resource has the correct identifier
        self.assertEqual(new_res_raster.metadata.identifiers.all().count(), 1, msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier', [id.name for id in new_res_raster.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new versioned resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), new_res_raster.short_id)
        self.assertIn(id_url, [id.url for id in new_res_raster.metadata.identifiers.all()],
                      msg="Identifier url was not found for new versioned resource.")

        # test to make sure the new versioned resource is linked with the original resource via isReplacedBy and isVersionOf metadata elements
        self.assertGreater(new_res_raster.metadata.relations.all().count(), 0, msg="New versioned resource does has relation element.")
        self.assertIn('isVersionOf', [rel.type for rel in new_res_raster.metadata.relations.all()],
                      msg="No relation element of type 'isVersionOf' for new versioned resource")
        version_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), self.res_raster.short_id)
        self.assertIn(version_value, [rel.value for rel in new_res_raster.metadata.relations.all()],
                      msg="The original resource identifier is not set as value for isVersionOf for new versioned resource.")
        self.assertIn('isReplacedBy', [rel.type for rel in self.res_raster.metadata.relations.all()],
                      msg="No relation element of type 'isReplacedBy' for the original resource")
        version_value = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), new_res_raster.short_id)
        self.assertIn(version_value, [rel.value for rel in self.res_raster.metadata.relations.all()],
                      msg="The new versioned resource identifier is not set as value for isReplacedBy for original resource.")

        # test isReplacedBy is removed after the new versioned resource is deleted
        hydroshare.delete_resource(new_res_raster.short_id)
        self.assertNotIn('isReplacedBy', [rel.type for rel in self.res_raster.metadata.relations.all()],
                         msg="isReplacedBy is not removed from the original resource after its versioned resource is deleted")