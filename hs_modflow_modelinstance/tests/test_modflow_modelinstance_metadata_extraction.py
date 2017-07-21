import tempfile
import shutil
import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.testing import MockIRODSTestCaseMixin


class TestMODFLOWModelInstanceMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestMODFLOWModelInstanceMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.res = hydroshare.create_resource(
            resource_type='MODFLOWModelInstanceResource',
            owner=self.user,
            title='Test MODFLOW Model Instance Resource'
        )

        self.resGenModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model MODFLOW Program Resource'
        )

        self.resMODFLOWModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model Program Resource 2'
        )

        self.temp_dir = tempfile.mkdtemp()

        d = 'hs_modflow_modelinstance/tests/modflow_example/'
        self.file_list = []
        self.file_names = []
        self.sample_nam_name = 'example.nam'
        self.sample_nam_name2 = 'example2.nam'
        self.sample_dis_file = 'example.dis'
        for file in os.listdir(d):
            self.file_names.append(file)
            target_temp_file = os.path.join(self.temp_dir, file)
            shutil.copy("{}{}".format(d, file), target_temp_file)
            if self.sample_nam_name == file:
                self.sample_nam_obj = open(target_temp_file, 'r')
            elif self.sample_nam_name2 == file:
                self.sample_nam_obj2 = open(target_temp_file, 'r')
            elif self.sample_dis_file == file:
                self.sample_dis_obj = open(target_temp_file, 'r')
            else:
                self.file_list.append(target_temp_file)

        self.file_name = "MIR.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model Instance resource files")
        self.text_file_obj = open(temp_text_file, 'r')

    def tearDown(self):
        super(TestMODFLOWModelInstanceMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_metadata_extraction(self):
        # test allowed file type is '.*'
        self.assertEqual(self.res.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEqual(self.res.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.sample_nam_obj, name=self.sample_nam_obj.name)]
        utils.resource_file_add_pre_process(resource=self.res, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.res, files=files, user=self.user,
                                        extract_metadata=False)
        # here are the things that the modflow modelinstance should include from the .nam file
        # GroundWaterFlow
        # flowPackage: 'LPF', 'UZF'(?)
        #
        # GeneralElements
        # modelSolver: 'SIP'
        # outputcontrolpackage: 'OC', 'GAGE'
        #
        # BoundaryCondition
        # head_dependent_flux_boundary_packages: 'SFR', 'GHB', 'UZF'(?)
        # specified_flux_boundary_packages: 'WEL'

        self.assertEqual(self.res.metadata.general_elements.modelSolver, 'SIP')
        self.assertTrue(self.res.metadata.ground_water_flow.unsaturatedZonePackage)
        self.assertIn(
            'GHB',
            self.res.metadata.boundary_condition.get_head_dependent_flux_boundary_packages()
        )
        self.assertIn(
            'SFR',
            self.res.metadata.boundary_condition.get_head_dependent_flux_boundary_packages()
        )
        self.assertIn(
            'WEL',
            self.res.metadata.boundary_condition.get_specified_flux_boundary_packages()
        )
        self.assertIn(
            'OC',
            self.res.metadata.general_elements.get_output_control_package()
        )
        self.assertIn(
            'GAGE',
            self.res.metadata.general_elements.get_output_control_package()
        )

    def test_metadata_extraction_DIS_file(self):
        # Extract Metadata from DIS File
        files = [UploadedFile(file=self.sample_dis_obj, name=self.sample_dis_obj.name)]
        utils.resource_file_add_pre_process(resource=self.res,
                                            files=files,
                                            user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.res,
                                        files=files,
                                        user=self.user,
                                        extract_metadeta=False)

        # ---Tests for Grid Dimensions
        # Number of Layers
        self.assertEquals(self.res.metadata.grid_dimensions.numberOfLayers, str(4))
        # Type of Rows
        self.assertEquals(self.res.metadata.grid_dimensions.typeOfRows, 'Regular')
        # Number of Rows
        self.assertEquals(self.res.metadata.grid_dimensions.numberOfRows, str(20))
        # Type of Columns
        self.assertEquals(self.res.metadata.grid_dimensions.typeOfColumns, 'Regular')
        # Number of Columns
        self.assertEquals(self.res.metadata.grid_dimensions.numberOfColumns, str(15))

        # ---Tests for Stress Period
        # Stress Period Type
        self.assertEquals(self.res.metadata.stress_period.stressPeriodType, 'Steady and Transient')

        # ---Tests for Study Area
        # Total Length
        self.assertEquals(self.res.metadata.study_area.totalLength, str(20*2000.0))  # double
        # Total Width
        self.assertEquals(self.res.metadata.study_area.totalWidth, str(15*2000.0))  # double
