import os
import tempfile
import shutil

from xml.etree import ElementTree as ET

from django.test import TransactionTestCase
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData, Creator, Contributor, Coverage, Rights, Title, Language, \
    Publisher, Identifier, Type, Subject, Description, Date, Format, Relation, Source
from hs_core.testing import MockIRODSTestCaseMixin
from hs_modflow_modelinstance.models import *

# cmd to run tests: ./hsctl managepy test --keepdb hs_modflow_modelinstance/tests


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

        self.resMODFLOWModelInstance = hydroshare.create_resource(
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
        for file in os.listdir(d):
            self.file_names.append(file)
            target_temp_file = os.path.join(self.temp_dir, file)
            shutil.copy("{}{}".format(d, file), target_temp_file)
            if self.sample_nam_name == file:
                self.sample_nam_obj = open(target_temp_file, 'r')
            elif self.sample_nam_name2 == file:
                self.sample_nam_obj2 = open(target_temp_file, 'r')
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

    def test_allowed_file_types(self):
        # test allowed file type is '.*'        
        self.assertEquals(self.resMODFLOWModelInstance.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 1)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.executed_by, None)

        # Upload any other file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=True)

        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=True)

        # there should two content files
        self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 2)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.executed_by, None)

    def test_extended_metadata_CRUD(self):
        # test the core metadata at this point
        # there should be a title element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.title.value, 'Test MODFLOW Model Instance Resource')

        # there should be a creator element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.creators.count(), 1)

        # # there should be a type element
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.type, None)

        # there should be an identifier element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.identifiers.count(), 1)

        # there should be rights element
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.rights, None)

        # there shouldn't any source element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.sources.count(), 0)

        # there shouldn't any relation element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.relations.count(), 0)

        # there shouldn't any abstract element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.executed_by, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.study_area, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.grid_dimensions, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.stress_period, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.ground_water_flow, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.boundary_condition, None)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_calibration, None)
        self.assertEquals(len(self.resMODFLOWModelInstance.metadata.model_inputs), 0)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.general_elements, None)

        # create
        # create study_area
        self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=False)
        modeloutput_element = self.resMODFLOWModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, False)
        # multiple ModelOutput elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=False)
        self.resMODFLOWModelInstance.metadata.delete_element('ModelOutput',
                                                             self.resMODFLOWModelInstance.metadata.model_output.id)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        modeloutput_element = self.resMODFLOWModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, True)
        # multiple ModelOutput elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
            self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        # create ExecutedBy
        self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
        modelparam_element = self.resMODFLOWModelInstance.metadata.executed_by
        self.assertEquals(modelparam_element.model_name, self.resGenModelProgram.metadata.title.value)
        self.assertEquals(modelparam_element.model_program_fk, self.resGenModelProgram)
        # multiple ExecutedBy elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy',
                                                                 model_name=self.resMODFLOWModelProgram.short_id)

        # create StudyArea
        self.resMODFLOWModelInstance.metadata.create_element('StudyArea',
                                                             totalLength='a',
                                                             totalWidth='b',
                                                             maximumElevation='c',
                                                             minimumElevation='d')
        modelparam_element = self.resMODFLOWModelInstance.metadata.study_area
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.totalLength, 'a')
        self.assertEquals(modelparam_element.totalWidth, 'b')
        self.assertEquals(modelparam_element.maximumElevation, 'c')
        self.assertEquals(modelparam_element.minimumElevation, 'd')

        # try to create another studyarea - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('StudyArea',
                                                                 totalLength='b',
                                                                 totalWidth='c',
                                                                 maximumElevation='d',
                                                                 minimumElevation='e')

        # create GridDimensions
        self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                             numberOfLayers='a',
                                                             typeOfRows='Regular',
                                                             numberOfRows='c',
                                                             typeOfColumns='Irregular',
                                                             numberOfColumns='e')
        modelparam_element = self.resMODFLOWModelInstance.metadata.grid_dimensions
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.numberOfLayers, 'a')
        self.assertEquals(modelparam_element.typeOfRows, 'Regular')
        self.assertEquals(modelparam_element.numberOfRows, 'c')
        self.assertEquals(modelparam_element.typeOfColumns, 'Irregular')
        self.assertEquals(modelparam_element.numberOfColumns, 'e')

        # try to create another griddimensions - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                                 numberOfLayers='b',
                                                                 typeOfRows='Irregular',
                                                                 numberOfRows='c',
                                                                 typeOfColumns='Regular',
                                                                 numberOfColumns='z')
        # try with wrong dimension types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                                 numberOfLayers='b',
                                                                 typeOfRows='catspajamas',
                                                                 numberOfRows='c',
                                                                 typeOfColumns='Regular',
                                                                 numberOfColumns='z')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                                 numberOfLayers='b',
                                                                 typeOfRows='Irregular',
                                                                 numberOfRows='c',
                                                                 typeOfColumns='beach',
                                                                 numberOfColumns='z')

        # create stressperiod
        self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                             stressPeriodType='Steady',
                                                             steadyStateValue='a',
                                                             transientStateValueType='Daily',
                                                             transientStateValue='b')
        modelparam_element = self.resMODFLOWModelInstance.metadata.stress_period
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.stressPeriodType, 'Steady')
        self.assertEquals(modelparam_element.steadyStateValue, 'a')
        self.assertEquals(modelparam_element.transientStateValueType, 'Daily')
        self.assertEquals(modelparam_element.transientStateValue, 'b')

        # try to create another stressperiod - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                                 stressPeriodType='Steady',
                                                                 steadyStateValue='a',
                                                                 transientStateValueType='Daily',
                                                                 transientStateValue='b')
        # try with wrong stressperiod types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                                 stressPeriodType='Steady',
                                                                 steadyStateValue='a',
                                                                 transientStateValueType='Daly',
                                                                 transientStateValue='b')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                                 stressPeriodType='Bready',
                                                                 steadyStateValue='a',
                                                                 transientStateValueType='Daily',
                                                                 transientStateValue='b')

        # create groundwaterflow
        self.resMODFLOWModelInstance.metadata.create_element('GroundWaterFlow',
                                                             flowPackage='BCF6',
                                                             flowParameter='Transmissivity')
        modelparam_element = self.resMODFLOWModelInstance.metadata.ground_water_flow
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.flowPackage, 'BCF6')
        self.assertEquals(modelparam_element.flowParameter, 'Transmissivity')

        # try to create another groundwaterflow - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('GroundWaterFlow',
                                                                 flowPackage='BCF6',
                                                                 flowParameter='Transmissivity')
        # try with wrong groundwaterflow types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GroundWaterFlow',
                                                                 flowPackage='BCFd6',
                                                                 flowParameter='Transmissivity')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GroundWaterFlow',
                                                                 flowPackage='BCF6',
                                                                 flowParameter='Tranasmissivity')

        # create boundary condition
        # try with wrong boundarycondition types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                                 specified_head_boundary_packages=['BFH'],
                                                                 specified_flux_boundary_packages=['FHB'],
                                                                 head_dependent_flux_boundary_packages=['mmm'])
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                                 specified_head_boundary_packages=['BFH'],
                                                                 specified_flux_boundary_packages=['mmm'],
                                                                 head_dependent_flux_boundary_packages=['SFR'])
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                                 specified_head_boundary_packages=['mmm'],
                                                                 specified_flux_boundary_packages=['FHB'],
                                                                 head_dependent_flux_boundary_packages=['SFR'])

        spec_hd_bd_pkgs = ['CHD', 'FHB']
        spec_fx_bd_pkgs = ['RCH', 'WEL']
        hd_dep_fx_pkgs = ['MNW2', 'GHB', 'LAK']
        self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                             specified_head_boundary_packages=spec_hd_bd_pkgs,
                                                             specified_flux_boundary_packages=spec_fx_bd_pkgs,
                                                             head_dependent_flux_boundary_packages=hd_dep_fx_pkgs)
        modelparam_element = self.resMODFLOWModelInstance.metadata.boundary_condition
        self.assertNotEqual(modelparam_element, None)

        # check specified_head_boundary_packages
        added_packages = modelparam_element.get_specified_head_boundary_packages()
        for intended_package in spec_hd_bd_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # check specified_flux_boundary_packages
        added_packages = modelparam_element.get_specified_flux_boundary_packages()
        for intended_package in spec_fx_bd_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # check head_dependent_flux_boundary_packages
        added_packages = modelparam_element.get_head_dependent_flux_boundary_packages()
        for intended_package in hd_dep_fx_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # try to create another boundarycondition - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                                 specified_head_boundary_packages=spec_hd_bd_pkgs,
                                                                 specified_flux_boundary_packages=spec_fx_bd_pkgs,
                                                                 head_dependent_flux_boundary_packages=hd_dep_fx_pkgs)

        # create modelcalibration
        self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                             calibratedParameter='a',
                                                             observationType='b',
                                                             observationProcessPackage='RVOB',
                                                             calibrationMethod='c')
        modelparam_element = self.resMODFLOWModelInstance.metadata.model_calibration
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.calibratedParameter, 'a')
        self.assertEquals(modelparam_element.observationType, 'b')
        self.assertEquals(modelparam_element.observationProcessPackage, 'RVOB')
        self.assertEquals(modelparam_element.calibrationMethod, 'c')

        # try to create another modelcalibration - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                                 calibratedParameter='aa',
                                                                 observationType='b',
                                                                 observationProcessPackage='RVOB',
                                                                 calibrationMethod='c')
        # try with wrong modelcalibration types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                                 calibratedParameter='a',
                                                                 observationType='b',
                                                                 observationProcessPackage='RVoB',
                                                                 calibrationMethod='c')

        # create ModelInput
        self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
                                                             inputType='a',
                                                             inputSourceName='b',
                                                             inputSourceURL='http://www.RVOB.com')
        modelparam_elements = self.resMODFLOWModelInstance.metadata.model_inputs
        self.assertEqual(len(modelparam_elements), 1)
        modelparam_element = modelparam_elements[0]
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.inputType, 'a')
        self.assertEquals(modelparam_element.inputSourceName, 'b')
        self.assertEquals(modelparam_element.inputSourceURL, 'http://www.RVOB.com')

        # create another modelinput
        self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
                                                             inputType='aa',
                                                             inputSourceName='bd',
                                                             inputSourceURL='http://www.RVOBs.com')
        modelparam_elements = self.resMODFLOWModelInstance.metadata.model_inputs
        self.assertEqual(len(modelparam_elements), 2)
        modelparam_element = modelparam_elements[0]
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.inputType, 'aa')
        self.assertEquals(modelparam_element.inputSourceName, 'bd')
        self.assertEquals(modelparam_element.inputSourceURL, 'http://www.RVOBs.com')

        # create generalelements
        # try with wrong generalelements types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DsE4',
                                                                 output_control_package=['LMT6'],
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 output_control_package=['LMt6'],
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 output_control_package=['LMT6'],
                                                                 subsidencePackage='SaUB')
        ot_ctl_pkgs = ['LMT6', 'OC']
        self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                             modelParameter='BCF6',
                                                             modelSolver='DE4',
                                                             output_control_package=ot_ctl_pkgs,
                                                             subsidencePackage='SUB')
        modelparam_element = self.resMODFLOWModelInstance.metadata.general_elements
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.modelParameter, 'BCF6')
        self.assertEquals(modelparam_element.modelSolver, 'DE4')

        # check outputControlPackage
        added_packages = modelparam_element.get_output_control_package()
        for intended_package in ot_ctl_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        self.assertEquals(modelparam_element.subsidencePackage, 'SUB')

        # try to create another generalelements - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 output_control_package=['LMT6'],
                                                                 subsidencePackage='SUB')


        # update

        # update ModelOutput
        self.resMODFLOWModelInstance.metadata.update_element('ModelOutput',
                                                             self.resMODFLOWModelInstance.metadata.model_output.id,
                                                             includes_output=False)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output.includes_output, False)
        self.resMODFLOWModelInstance.metadata.update_element('ModelOutput',
                                                             self.resMODFLOWModelInstance.metadata.model_output.id,
                                                             includes_output=True)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output.includes_output, True)

        # update ExecutedBy
        self.resMODFLOWModelInstance.metadata.update_element('ExecutedBy',
                                                             self.resMODFLOWModelInstance.metadata.executed_by.id,
                                                             model_name=self.resMODFLOWModelProgram.short_id)
        modelparam_element = self.resMODFLOWModelInstance.metadata.executed_by
        self.assertEquals(modelparam_element.model_name, self.resMODFLOWModelProgram.metadata.title.value)
        self.assertEquals(modelparam_element.model_program_fk, self.resMODFLOWModelProgram)

        # update StudyArea
        self.resMODFLOWModelInstance.metadata.update_element('StudyArea',
                                                             self.resMODFLOWModelInstance.metadata.study_area.id,
                                                             totalLength=33,
                                                             totalWidth=2533,
                                                             maximumElevation=12,
                                                             minimumElevation=-148)
        modelparam_element = self.resMODFLOWModelInstance.metadata.study_area
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.totalLength, '33')
        self.assertEquals(modelparam_element.totalWidth, '2533')
        self.assertEquals(modelparam_element.maximumElevation, '12')
        self.assertEquals(modelparam_element.minimumElevation, '-148')



        # update GridDimensions
        self.resMODFLOWModelInstance.metadata.update_element('GridDimensions',
                                                             self.resMODFLOWModelInstance.metadata.grid_dimensions.id,
                                                             numberOfLayers='b',
                                                             typeOfRows='Irregular',
                                                             numberOfRows='d',
                                                             typeOfColumns='Regular',
                                                             numberOfColumns='f')
        modelparam_element = self.resMODFLOWModelInstance.metadata.grid_dimensions
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.numberOfLayers, 'b')
        self.assertEquals(modelparam_element.typeOfRows, 'Irregular')
        self.assertEquals(modelparam_element.numberOfRows, 'd')
        self.assertEquals(modelparam_element.typeOfColumns, 'Regular')
        self.assertEquals(modelparam_element.numberOfColumns, 'f')

        # try with wrong dimension types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GridDimensions',
                                                                 self.resMODFLOWModelInstance.metadata.grid_dimensions.id,
                                                                 numberOfLayers='b',
                                                                 typeOfRows='catspajamas',
                                                                 numberOfRows='c',
                                                                 typeOfColumns='Regular',
                                                                 numberOfColumns='z')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GridDimensions',
                                                                 self.resMODFLOWModelInstance.metadata.grid_dimensions.id,
                                                                 numberOfLayers='b',
                                                                 typeOfRows='Irregular',
                                                                 numberOfRows='c',
                                                                 typeOfColumns='beach',
                                                                 numberOfColumns='z')

        # update stressperiod
        self.resMODFLOWModelInstance.metadata.update_element('StressPeriod',
                                                             self.resMODFLOWModelInstance.metadata.stress_period.id,
                                                             stressPeriodType='Transient',
                                                             steadyStateValue='555',
                                                             transientStateValueType='Annually',
                                                             transientStateValue='123')
        modelparam_element = self.resMODFLOWModelInstance.metadata.stress_period
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.stressPeriodType, 'Transient')
        self.assertEquals(modelparam_element.steadyStateValue, '555')
        self.assertEquals(modelparam_element.transientStateValueType, 'Annually')
        self.assertEquals(modelparam_element.transientStateValue, '123')

        # try with wrong stressperiod types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('StressPeriod',
                                                                 self.resMODFLOWModelInstance.metadata.stress_period.id,
                                                                 stressPeriodType='Transsdfasient',
                                                                 steadyStateValue='555',
                                                                 transientStateValueType='Annually',
                                                                 transientStateValue='123')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('StressPeriod',
                                                                 self.resMODFLOWModelInstance.metadata.stress_period.id,
                                                                 stressPeriodType='Transient',
                                                                 steadyStateValue='555',
                                                                 transientStateValueType='Annfadsfually',
                                                                 transientStateValue='123')


        # update groundwaterflow
        self.resMODFLOWModelInstance.metadata.update_element('GroundWaterFlow',
                                                             self.resMODFLOWModelInstance.metadata.ground_water_flow.id,
                                                             flowPackage='UPW',
                                                             flowParameter='Hydraulic Conductivity')
        modelparam_element = self.resMODFLOWModelInstance.metadata.ground_water_flow
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.flowPackage, 'UPW')
        self.assertEquals(modelparam_element.flowParameter, 'Hydraulic Conductivity')

        # try with wrong groundwaterflow types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GroundWaterFlow',
                                                                 self.resMODFLOWModelInstance.metadata.ground_water_flow.id,
                                                                 flowPackage='UPsW',
                                                                 flowParameter='Hydraulic Conductivity')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GroundWaterFlow',
                                                                 self.resMODFLOWModelInstance.metadata.ground_water_flow.id,
                                                                 flowPackage='UPW',
                                                                 flowParameter='Hydraalic Conductivity')

        # update boundary condition
        # try with wrong boundarycondition types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('BoundaryCondition',
                                                                 self.resMODFLOWModelInstance.metadata.boundary_condition.id,
                                                                 specified_head_boundary_packages=['BFH'],
                                                                 specified_flux_boundary_packages=['FHB'],
                                                                 head_dependent_flux_boundary_packages=['mmm'])
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('BoundaryCondition',
                                                                 self.resMODFLOWModelInstance.metadata.boundary_condition.id,
                                                                 specified_head_boundary_packages=['BFH'],
                                                                 specified_flux_boundary_packages=['mmm'],
                                                                 head_dependent_flux_boundary_packages=['SFR'])
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('BoundaryCondition',
                                                                 self.resMODFLOWModelInstance.metadata.boundary_condition.id,
                                                                 specified_head_boundary_packages=['mmm'],
                                                                 specified_flux_boundary_packages=['FHB'],
                                                                 head_dependent_flux_boundary_packages=['SFR'])

        spec_hd_bd_pkgs = ['BFH']
        spec_fx_bd_pkgs = ['FHB']
        hd_dep_fx_pkgs = ['RIV', 'DAFG', 'DRT']
        self.resMODFLOWModelInstance.metadata.update_element('BoundaryCondition',
                                                             self.resMODFLOWModelInstance.metadata.boundary_condition.id,
                                                             specified_head_boundary_packages=spec_hd_bd_pkgs,
                                                             specified_flux_boundary_packages=spec_fx_bd_pkgs,
                                                             head_dependent_flux_boundary_packages=hd_dep_fx_pkgs)
        modelparam_element = self.resMODFLOWModelInstance.metadata.boundary_condition
        self.assertNotEqual(modelparam_element, None)

        # check specified_head_boundary_packages
        added_packages = modelparam_element.get_specified_head_boundary_packages()
        for intended_package in spec_hd_bd_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # check specified_flux_boundary_packages
        added_packages = modelparam_element.get_specified_flux_boundary_packages()
        for intended_package in spec_fx_bd_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # check head_dependent_flux_boundary_packages
        added_packages = modelparam_element.get_head_dependent_flux_boundary_packages()
        for intended_package in hd_dep_fx_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        # update modelcalibration
        self.resMODFLOWModelInstance.metadata.update_element('ModelCalibration',
                                                             self.resMODFLOWModelInstance.metadata.model_calibration.id,
                                                             calibratedParameter='b',
                                                             observationType='c',
                                                             observationProcessPackage='OBS',
                                                             calibrationMethod='d')
        modelparam_element = self.resMODFLOWModelInstance.metadata.model_calibration
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.calibratedParameter, 'b')
        self.assertEquals(modelparam_element.observationType, 'c')
        self.assertEquals(modelparam_element.observationProcessPackage, 'OBS')
        self.assertEquals(modelparam_element.calibrationMethod, 'd')

        # try with wrong modelcalibration types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('ModelCalibration',
                                                                 self.resMODFLOWModelInstance.metadata.model_calibration.id,
                                                                 calibratedParameter='a',
                                                                 observationType='b',
                                                                 observationProcessPackage='dtarb',
                                                                 calibrationMethod='c')

        # update ModelInput
        self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
                                                             self.resMODFLOWModelInstance.metadata.model_inputs[1].id,
                                                             inputType='b',
                                                             inputSourceName='c',
                                                             inputSourceURL='http://www.RVOB.com')
        modelparam_elements = self.resMODFLOWModelInstance.metadata.model_inputs
        self.assertEqual(len(modelparam_elements), 2)
        modelparam_element = modelparam_elements[1]
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.inputType, 'b')
        self.assertEquals(modelparam_element.inputSourceName, 'c')
        self.assertEquals(modelparam_element.inputSourceURL, 'http://www.RVOB.com')

        # update another modelinput
        self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
                                                             self.resMODFLOWModelInstance.metadata.model_inputs[0].id,
                                                             inputType='bb',
                                                             inputSourceName='cc',
                                                             inputSourceURL='http://www.RVOBss.com')
        modelparam_elements = self.resMODFLOWModelInstance.metadata.model_inputs
        self.assertEqual(len(modelparam_elements), 2)
        modelparam_element = modelparam_elements[0]
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.inputType, 'bb')
        self.assertEquals(modelparam_element.inputSourceName, 'cc')
        self.assertEquals(modelparam_element.inputSourceURL, 'http://www.RVOBss.com')

        # update generalelements
        # try with wrong generalelements types - raises exception
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GeneralElements',
                                                                 self.resMODFLOWModelInstance.metadata.general_elements.id,
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DsE4',
                                                                 output_control_package=['LMT6'],
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GeneralElements',
                                                                 self.resMODFLOWModelInstance.metadata.general_elements.id,
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 output_control_package=['LMTd6'],
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.update_element('GeneralElements',
                                                                 self.resMODFLOWModelInstance.metadata.general_elements.id,
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 output_control_package=['LMT6'],
                                                                 subsidencePackage='SaUB')
        ot_ctl_pkgs = ['GAGE', 'MNWI']

        self.resMODFLOWModelInstance.metadata.update_element('GeneralElements',
                                                             self.resMODFLOWModelInstance.metadata.general_elements.id,
                                                             modelParameter='hydraulic conductivity',
                                                             modelSolver='PCGN',
                                                             output_control_package=ot_ctl_pkgs,
                                                             subsidencePackage='SWT')
        modelparam_element = self.resMODFLOWModelInstance.metadata.general_elements
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.modelParameter, 'hydraulic conductivity')
        self.assertEquals(modelparam_element.modelSolver, 'PCGN')

        # check outputControlPackage
        added_packages = modelparam_element.get_output_control_package()
        for intended_package in ot_ctl_pkgs:
            self.assertEquals(intended_package in added_packages, True)

        self.assertEquals(modelparam_element.subsidencePackage, 'SWT')


        # delete

        # check that there are all extended metadata elements at this point
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.executed_by, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.study_area, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.grid_dimensions, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.stress_period, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.ground_water_flow, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.boundary_condition, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_calibration, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_inputs, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.general_elements, None)

        # delete all elements
        self.resMODFLOWModelInstance.metadata.delete_element('ModelOutput',
                                                             self.resMODFLOWModelInstance.metadata.model_output.id)
        self.resMODFLOWModelInstance.metadata.delete_element('ExecutedBy',
                                                             self.resMODFLOWModelInstance.metadata.executed_by.id)
        self.resMODFLOWModelInstance.metadata.delete_element('StudyArea',
                                                             self.resMODFLOWModelInstance.metadata.study_area.id)
        self.resMODFLOWModelInstance.metadata.delete_element('GridDimensions',
                                                             self.resMODFLOWModelInstance.metadata.grid_dimensions.id)
        self.resMODFLOWModelInstance.metadata.delete_element('StressPeriod',
                                                             self.resMODFLOWModelInstance.metadata.stress_period.id)
        self.resMODFLOWModelInstance.metadata.delete_element('GroundWaterFlow',
                                                             self.resMODFLOWModelInstance.metadata.ground_water_flow.id)
        self.resMODFLOWModelInstance.metadata.delete_element('BoundaryCondition',
                                                             self.resMODFLOWModelInstance.metadata.boundary_condition.id)
        self.resMODFLOWModelInstance.metadata.delete_element('ModelCalibration',
                                                             self.resMODFLOWModelInstance.metadata.model_calibration.id)
        for items in range(len(self.resMODFLOWModelInstance.metadata.model_inputs)):
            self.resMODFLOWModelInstance.metadata.delete_element('ModelInput', self.resMODFLOWModelInstance.metadata.model_inputs[0].id)
        self.resMODFLOWModelInstance.metadata.delete_element('GeneralElements',
                                                             self.resMODFLOWModelInstance.metadata.general_elements.id)

        # make sure they are deleted
        self.assertEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.executed_by, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.study_area, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.grid_dimensions, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.stress_period, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.ground_water_flow, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.boundary_condition, None)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.model_calibration, None)
        self.assertEqual(len(self.resMODFLOWModelInstance.metadata.model_inputs), 0)
        self.assertEqual(self.resMODFLOWModelInstance.metadata.general_elements, None)

    def test_public_or_discoverable(self):
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.metadata.has_all_required_elements())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add txt file
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add .nam file
        files = [UploadedFile(file=self.sample_nam_obj, name=self.sample_nam_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add reqd files except 2
        for f in self.file_list[2:]:
            self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
            self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
            f_obj = open(f, 'r')
            files = [UploadedFile(file=f_obj, name=f_obj.name)]
            utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                                extract_metadata=False)
            utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add all reqd files
        for f in self.file_list[:2]:
            self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
            self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
            f_obj = open(f, 'r')
            files = [UploadedFile(file=f_obj, name=f_obj.name)]
            utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                                extract_metadata=False)
            utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        self.assertTrue(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add generically required elements; should be made public
        self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
        self.assertTrue(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # add another .nam file; should not be able to be public
        files = [UploadedFile(file=self.sample_nam_obj2, name=self.sample_nam_obj2.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # delete extra .nam file; should be able to be public again
        hydroshare.delete_resource_file(self.resMODFLOWModelInstance.short_id, self.sample_nam_name2, self.user)
        self.assertTrue(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertTrue(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

        # delete one reqd file; should not be able to be public again
        hydroshare.delete_resource_file(self.resMODFLOWModelInstance.short_id, self.file_names[2], self.user)
        self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
        self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)

    def test_multiple_content_files(self):
        self.assertTrue(self.resMODFLOWModelInstance.can_have_multiple_files())

    def test_get_xml(self):
        self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
        self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
        self.resMODFLOWModelInstance.metadata.create_element('StudyArea',
                                                             totalLength=1111,
                                                             totalWidth=2222,
                                                             maximumElevation=3333,
                                                             minimumElevation=4444)
        self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                             numberOfLayers=5555,
                                                             typeOfRows='Irregular',
                                                             numberOfRows=6666,
                                                             typeOfColumns='Regular',
                                                             numberOfColumns=7777)
        self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                             stressPeriodType='Steady and Transient',
                                                             steadyStateValue=8888,
                                                             transientStateValueType='Monthly',
                                                             transientStateValue=9999)
        self.resMODFLOWModelInstance.metadata.create_element('GroundwaterFlow',
                                                             flowPackage='LPF',
                                                             flowParameter='Hydraulic Conductivity')
        self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                             specified_head_boundary_packages=['CHD', 'FHB'],
                                                             specified_flux_boundary_packages=['FHB', 'WEL'],
                                                             head_dependent_flux_boundary_packages=['RIV', 'MNW1'])
        self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                             calibratedParameter='test parameter',
                                                             observationType='test observation type',
                                                             observationProcessPackage='GBOB',
                                                             calibrationMethod='test calibration method')
        self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
                                                             inputType='test input type',
                                                             inputSourceName='test source name',
                                                             inputSourceURL='http://www.test.com')
        self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                             modelParameter='test model parameter',
                                                             modelSolver='SIP',
                                                             output_control_package=['HYD', 'OC'],
                                                             subsidencePackage='SWT')
        xml_doc = self.resMODFLOWModelInstance.metadata.get_xml()
        # check to see if the specific metadata are in the xml doc
        self.assertTrue('1111' in xml_doc)
        self.assertTrue('2222' in xml_doc)
        self.assertTrue('3333' in xml_doc)
        self.assertTrue('4444' in xml_doc)
        self.assertTrue('5555' in xml_doc)
        self.assertTrue('Irregular' in xml_doc)
        self.assertTrue('6666' in xml_doc)
        self.assertTrue('Regular' in xml_doc)
        self.assertTrue('7777' in xml_doc)
        self.assertTrue('Steady and Transient' in xml_doc)
        self.assertTrue('8888' in xml_doc)
        self.assertTrue('Monthly' in xml_doc)
        self.assertTrue('9999' in xml_doc)
        self.assertTrue('LPF' in xml_doc)
        self.assertTrue('Hydraulic Conductivity' in xml_doc)
        self.assertTrue('CHD' in xml_doc)
        self.assertTrue('FHB' in xml_doc)
        self.assertTrue('FHB' in xml_doc)
        self.assertTrue('WEL' in xml_doc)
        self.assertTrue('RIV' in xml_doc)
        self.assertTrue('MNW1' in xml_doc)
        self.assertTrue('test parameter' in xml_doc)
        self.assertTrue('test observation type' in xml_doc)
        self.assertTrue('GBOB' in xml_doc)
        self.assertTrue('test calibration method' in xml_doc)
        self.assertTrue('test input type' in xml_doc)
        self.assertTrue('test source name' in xml_doc)
        self.assertTrue('http://www.test.com' in xml_doc)
        self.assertTrue('test model parameter' in xml_doc)
        self.assertTrue('SIP' in xml_doc)
        self.assertTrue('HYD' in xml_doc)
        self.assertTrue('OC' in xml_doc)
        self.assertTrue('SWT' in xml_doc)

    def test_metadata_on_content_file_delete(self):
        # Metadata should remain after content file deletion

        # upload files
        files = [UploadedFile(file=self.sample_nam_obj, name=self.sample_nam_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        files = [UploadedFile(file=self.sample_nam_obj2, name=self.sample_nam_obj2.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        for f in self.file_list:
            f_obj = open(f, 'r')
            files = [UploadedFile(file=f_obj, name=f_obj.name)]
            utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                                extract_metadata=False)
            utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        # create metadata elements
        self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
        self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
        self.resMODFLOWModelInstance.metadata.create_element('StudyArea',
                                                             totalLength=1111,
                                                             totalWidth=2222,
                                                             maximumElevation=3333,
                                                             minimumElevation=4444)
        self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                             numberOfLayers=5555,
                                                             typeOfRows='Irregular',
                                                             numberOfRows=6666,
                                                             typeOfColumns='Regular',
                                                             numberOfColumns=7777)
        self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                             stressPeriodType='Steady and Transient',
                                                             steadyStateValue=8888,
                                                             transientStateValueType='Monthly',
                                                             transientStateValue=9999)
        self.resMODFLOWModelInstance.metadata.create_element('GroundwaterFlow',
                                                             flowPackage='LPF',
                                                             flowParameter='Hydraulic Conductivity')
        self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                             specified_head_boundary_packages=['CHD', 'FHB'],
                                                             specified_flux_boundary_packages=['FHB', 'WEL'],
                                                             head_dependent_flux_boundary_packages=['RIV', 'MNW1'])
        self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                             calibratedParameter='test parameter',
                                                             observationType='test observation type',
                                                             observationProcessPackage='GBOB',
                                                             calibrationMethod='test calibration method')
        self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
                                                             inputType='test input type',
                                                             inputSourceName='test source name',
                                                             inputSourceURL='http://www.test.com')
        self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                             modelParameter='test model parameter',
                                                             modelSolver='SIP',
                                                             output_control_package=['HYD', 'OC'],
                                                             subsidencePackage='SWT')

        # there should 12 content file
        self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 12)

        # there should be 11 format elements (2 nam)
        self.assertEquals(self.resMODFLOWModelInstance.metadata.formats.all().count(), 11)

        # delete content files that we added above
        for f in self.file_names:
            hydroshare.delete_resource_file(self.resMODFLOWModelInstance.short_id, f, self.user)

        # there should no content file
        self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 0)

        # there should be no format element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.formats.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEquals(self.resMODFLOWModelInstance.metadata.title, None)

        # there should be an abstract element
        self.assertNotEquals(self.resMODFLOWModelInstance.metadata.description, None)

        # there should be one creator element
        self.assertEquals(self.resMODFLOWModelInstance.metadata.creators.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.executed_by, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.study_area, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.grid_dimensions, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.stress_period, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.ground_water_flow, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.boundary_condition, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_calibration, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_inputs, None)
        self.assertNotEqual(self.resMODFLOWModelInstance.metadata.general_elements, None)

    def test_metadata_delete_on_resource_delete(self):
        # upload files
        files = [UploadedFile(file=self.sample_nam_obj, name=self.sample_nam_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        files = [UploadedFile(file=self.sample_nam_obj2, name=self.sample_nam_obj2.name)]
        utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)
        utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                        extract_metadata=False)
        for f in self.file_list:
            f_obj = open(f, 'r')
            files = [UploadedFile(file=f_obj, name=f_obj.name)]
            utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                                extract_metadata=False)
            utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
                                            extract_metadata=False)

        # create metadata elements
        self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
        self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
        self.resMODFLOWModelInstance.metadata.create_element('StudyArea',
                                                             totalLength=1111,
                                                             totalWidth=2222,
                                                             maximumElevation=3333,
                                                             minimumElevation=4444)
        self.resMODFLOWModelInstance.metadata.create_element('GridDimensions',
                                                             numberOfLayers=5555,
                                                             typeOfRows='Irregular',
                                                             numberOfRows=6666,
                                                             typeOfColumns='Regular',
                                                             numberOfColumns=7777)
        self.resMODFLOWModelInstance.metadata.create_element('StressPeriod',
                                                             stressPeriodType='Steady and Transient',
                                                             steadyStateValue=8888,
                                                             transientStateValueType='Monthly',
                                                             transientStateValue=9999)
        self.resMODFLOWModelInstance.metadata.create_element('GroundwaterFlow',
                                                             flowPackage='LPF',
                                                             flowParameter='Hydraulic Conductivity')
        self.resMODFLOWModelInstance.metadata.create_element('BoundaryCondition',
                                                             specified_head_boundary_packages=['CHD', 'FHB'],
                                                             specified_flux_boundary_packages=['FHB', 'WEL'],
                                                             head_dependent_flux_boundary_packages=['RIV', 'MNW1'])
        self.resMODFLOWModelInstance.metadata.create_element('ModelCalibration',
                                                             calibratedParameter='test parameter',
                                                             observationType='test observation type',
                                                             observationProcessPackage='GBOB',
                                                             calibrationMethod='test calibration method')
        self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
                                                             inputType='test input type',
                                                             inputSourceName='test source name',
                                                             inputSourceURL='http://www.test.com')
        self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                             modelParameter='test model parameter',
                                                             modelSolver='SIP',
                                                             output_control_package=['HYD', 'OC'],
                                                             subsidencePackage='SWT')
        self.resMODFLOWModelInstance.metadata.create_element('Contributor', name="user2")

        # before resource delete
        core_metadata_obj = self.resMODFLOWModelInstance.metadata
        self.assertEquals(CoreMetaData.objects.all().count(), 3)
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Title metadata objects
        self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Description (Abstract) metadata objects
        self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Date metadata objects
        self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Subject metadata objects
        self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Format metadata objects
        self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Language metadata objects
        self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Rights metadata objects
        self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        self.assertEquals(MODFLOWModelInstanceMetaData.objects.all().count(), 1)
        # there should be Model Output metadata objects
        self.assertTrue(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ExecutedBy metadata objects
        self.assertTrue(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be StudyArea metadata objects
        self.assertTrue(StudyArea.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GridDimensions metadata objects
        self.assertTrue(GridDimensions.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be StressPeriod metadata objects
        self.assertTrue(StressPeriod.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GroundWaterFlow metadata objects
        self.assertTrue(GroundWaterFlow.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be BoundaryCondition metadata objects
        self.assertTrue(BoundaryCondition.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelCalibration metadata objects
        self.assertTrue(ModelCalibration.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelInput metadata objects
        self.assertTrue(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GeneralElements metadata objects
        self.assertTrue(GeneralElements.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resMODFLOWModelInstance.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 2)
        self.assertEquals(MODFLOWModelInstanceMetaData.objects.all().count(), 0)

        # there should be no Creator metadata objects
        self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Identifier metadata objects
        self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Type metadata objects
        self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Title metadata objects
        self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Date metadata objects
        self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Format metadata objects
        self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Language metadata objects
        self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Rights metadata objects
        self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())

        # resource specific metadata
        # there should be Model Output metadata objects
        self.assertFalse(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ExecutedBy metadata objects
        self.assertFalse(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be StudyArea metadata objects
        self.assertFalse(StudyArea.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GridDimensions metadata objects
        self.assertFalse(GridDimensions.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be StressPeriod metadata objects
        self.assertFalse(StressPeriod.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GroundWaterFlow metadata objects
        self.assertFalse(GroundWaterFlow.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be BoundaryCondition metadata objects
        self.assertFalse(BoundaryCondition.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelCalibration metadata objects
        self.assertFalse(ModelCalibration.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelInput metadata objects
        self.assertFalse(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be GeneralElements metadata objects
        self.assertFalse(GeneralElements.objects.filter(object_id=core_metadata_obj.id).exists())
