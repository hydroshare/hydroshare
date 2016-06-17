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
from hs_swat_modelinstance.models import *


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
        self.file_name = "MIR.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model MODFLOW Instance resource files")
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
                                                                 outputControlPackage='LMT6',
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 outputControlPackage='LMTd6',
                                                                 subsidencePackage='SUB')
        with self.assertRaises(ValidationError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 outputControlPackage='LMT6',
                                                                 subsidencePackage='SaUB')

        self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                             modelParameter='BCF6',
                                                             modelSolver='DE4',
                                                             outputControlPackage='LMT6',
                                                             subsidencePackage='SUB')
        modelparam_element = self.resMODFLOWModelInstance.metadata.general_elements
        self.assertNotEqual(modelparam_element, None)
        self.assertEquals(modelparam_element.modelParameter, 'BCF6')
        self.assertEquals(modelparam_element.modelSolver, 'DE4')
        self.assertEquals(modelparam_element.outputControlPackage, 'LMT6')
        self.assertEquals(modelparam_element.subsidencePackage, 'SUB')

        # try to create another generalelements - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resMODFLOWModelInstance.metadata.create_element('GeneralElements',
                                                                 modelParameter='BCF6',
                                                                 modelSolver='DE4',
                                                                 outputControlPackage='LMT6',
                                                                 subsidencePackage='SUB')
            #     # create simulation type
    #     # try to create a simulation type with a non cv term - it would raise an exception
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                              simulation_type_name='bilbo baggins')
    #     # create legit SimType
    #     self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                          simulation_type_name='Normal Simulation')
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.simulation_type.get_simulation_type_name_display(),
    #                      'Normal Simulation')
    #     # try to create another simulation type - it would raise an exception
    #     with self.assertRaises(IntegrityError):
    #             self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                                  simulation_type_name='Sensitivity Analysis')
    #
    #     # create modelmethod
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelMethod',
    #                                                          runoffCalculationMethod='aaa',
    #                                                          flowRoutingMethod='bbb',
    #                                                          petEstimationMethod='ccc')
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_method, None)
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.runoffCalculationMethod, 'aaa')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.flowRoutingMethod, 'bbb')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.petEstimationMethod, 'ccc')
    #     # try to create another model_method - it would raise an exception
    #     with self.assertRaises(IntegrityError):
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelMethod',
    #                                                              runoffCalculationMethod='bbb',
    #                                                              flowRoutingMethod='ccc',
    #                                                              petEstimationMethod='ddd')
    #
    #     # create ModelParameter
    #     # try to create a modelparam with a non cv term
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                              model_parameters="chucky cheese")
    #     # try to create a modelparam with a no model_parameter term
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelParameter', george="clooney")
    #     # create legit modelparam
    #     s_params = ["Crop rotation", "Tillage operation"]
    #     o_params = "spongebob"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                          model_parameters=s_params,
    #                                                          other_parameters=o_params)
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.model_parameter
    #     self.assertNotEqual(modelparam_element, None)
    #     v = modelparam_element.get_swat_model_parameters()
    #     for p in s_params:
    #         self.assertEquals(p in v, True)
    #     self.assertEquals(modelparam_element.other_parameters, o_params)
    #     # try to create another swat_model_objective
    #     with self.assertRaises(IntegrityError):
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                              model_parameters=[s_params[0]],
    #                                                              other_parameters="bleh")
    #
    #     # create ModelInput
    #     # try to create a ModelInput with non cv terms
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                              rainfallTimeStepType='frodo baggins')
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                              routingTimeStepType='legolas')
    #         self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                              simulationTimeStepType='gandalf')
    #     # create normal ModelInput
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                          warmupPeriodValue='a',
    #                                                          rainfallTimeStepType='Daily',
    #                                                          rainfallTimeStepValue='c',
    #                                                          routingTimeStepType='Daily',
    #                                                          routingTimeStepValue='e',
    #                                                          simulationTimeStepType='Hourly',
    #                                                          simulationTimeStepValue='g',
    #                                                          watershedArea='h',
    #                                                          numberOfSubbasins='i',
    #                                                          numberOfHRUs='j',
    #                                                          demResolution='k',
    #                                                          demSourceName='l',
    #                                                          demSourceURL='m',
    #                                                          landUseDataSourceName='n',
    #                                                          landUseDataSourceURL='o',
    #                                                          soilDataSourceName='p',
    #                                                          soilDataSourceURL='q',
    #                                                          )
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.warmupPeriodValue, 'a')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.rainfallTimeStepType, 'Daily')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.rainfallTimeStepValue, 'c')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.routingTimeStepType, 'Daily')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.routingTimeStepValue, 'e')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.simulationTimeStepType, 'Hourly')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.simulationTimeStepValue, 'g')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.watershedArea, 'h')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.numberOfSubbasins, 'i')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.numberOfHRUs, 'j')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demResolution, 'k')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demSourceName, 'l')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demSourceURL, 'm')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.landUseDataSourceName, 'n')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.landUseDataSourceURL, 'o')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.soilDataSourceName, 'p')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.soilDataSourceURL, 'q')
    #     # try to create another ModelInput
    #     with self.assertRaises(IntegrityError):
    #             self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                                  warmupPeriodValue='patrick')
    #
    #     # update
    #
    #     # update ModelOutput
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelOutput',
    #                                                          self.resMODFLOWModelInstance.metadata.model_output.id,
    #                                                          includes_output=False)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output.includes_output, False)
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelOutput',
    #                                                          self.resMODFLOWModelInstance.metadata.model_output.id,
    #                                                          includes_output=True)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output.includes_output, True)
    #
    #     # update ExecutedBy
    #     self.resMODFLOWModelInstance.metadata.update_element('ExecutedBy',
    #                                                          self.resMODFLOWModelInstance.metadata.executed_by.id,
    #                                                          model_name=self.resMODFLOWModelProgram.short_id)
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.executed_by
    #     self.assertEquals(modelparam_element.model_name, self.resMODFLOWModelProgram.metadata.title.value)
    #     self.assertEquals(modelparam_element.model_program_fk, self.resMODFLOWModelProgram)
    #
    #     # update ModelObjective
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelObjective',
    #                                                          self.resMODFLOWModelInstance.metadata.model_objective.id,
    #                                                          swat_model_objectives=[s_objs[2]],
    #                                                          other_objectives='jelly beans')
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.model_objective
    #     self.assertNotEqual(modelparam_element, None)
    #     v = modelparam_element.get_swat_model_objectives()
    #     for o in [s_objs[2]]:
    #         self.assertEquals(o in v, True)
    #     self.assertEquals(modelparam_element.other_objectives, 'jelly beans')
    #     # try with a non cv term
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.update_element('ModelObjective',
    #                                                              self.resMODFLOWModelInstance.metadata.model_objective.id,
    #                                                              swat_model_objectives=["gravity waves"])
    #     # update just other objective
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelObjective',
    #                                                          self.resMODFLOWModelInstance.metadata.model_objective.id,
    #                                                          other_objectives="einstein")
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.model_objective
    #     self.assertEquals(modelparam_element.other_objectives, 'einstein')
    #
    #     # update SimulationType
    #     self.resMODFLOWModelInstance.metadata.update_element('SimulationType',
    #                                                          self.resMODFLOWModelInstance.metadata.simulation_type.id,
    #                                                          simulation_type_name='Auto-Calibration')
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.simulation_type
    #     self.assertEquals(modelparam_element.get_simulation_type_name_display(), 'Auto-Calibration')
    #     # try with non cv term
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.update_element('SimulationType',
    #                                                              self.resMODFLOWModelInstance.metadata.simulation_type.id,
    #                                                              simulation_type_name="Panda")
    #
    #     # update ModelMethod
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelMethod',
    #                                                          self.resMODFLOWModelInstance.metadata.model_method.id,
    #                                                          runoffCalculationMethod="go hoos",
    #                                                          flowRoutingMethod='rotunda',
    #                                                          petEstimationMethod='honor code')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.runoffCalculationMethod, 'go hoos')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.flowRoutingMethod, 'rotunda')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_method.petEstimationMethod, 'honor code')
    #
    #     # update ModelParameter
    #     # try to update a modelparam with a non cv term
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.update_element('ModelParameter',
    #                                                              self.resMODFLOWModelInstance.metadata.model_parameter.id,
    #                                                              model_parameters="chucky cheese")
    #     # update legit modelparam
    #     s_params = ["Point source", "Fertilizer"]
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelParameter',
    #                                                          self.resMODFLOWModelInstance.metadata.model_parameter.id,
    #                                                          model_parameters=s_params)
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.model_parameter
    #     v = modelparam_element.get_swat_model_parameters()
    #     for p in s_params:
    #         self.assertEquals(p in v, True)
    #     self.assertEquals(modelparam_element.other_parameters, o_params)
    #     # now update the other params
    #     o_params = 'square pants'
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelParameter',
    #                                                          self.resMODFLOWModelInstance.metadata.model_parameter.id,
    #                                                          other_parameters=o_params)
    #     # check that the other params was updated and that the model params are the same
    #     modelparam_element = self.resMODFLOWModelInstance.metadata.model_parameter
    #     v = modelparam_element.get_swat_model_parameters()
    #     for p in s_params:
    #         self.assertEquals(p in v, True)
    #     self.assertEquals(modelparam_element.other_parameters, o_params)
    #
    #     # update ModelInput
    #     # try to update a ModelInput with non cv terms
    #     with self.assertRaises(ValidationError):
    #         self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
    #                                                              self.resMODFLOWModelInstance.metadata.model_input.id,
    #                                                              rainfallTimeStepType='frodo baggins')
    #         self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
    #                                                              self.resMODFLOWModelInstance.metadata.model_input.id,
    #                                                              routingTimeStepType='legolas')
    #         self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
    #                                                              self.resMODFLOWModelInstance.metadata.model_input.id,
    #                                                              simulationTimeStepType='gandalf')
    #     # update normal ModelInput
    #     self.resMODFLOWModelInstance.metadata.update_element('ModelInput',
    #                                                          self.resMODFLOWModelInstance.metadata.model_input.id,
    #                                                          warmupPeriodValue='b',
    #                                                          rainfallTimeStepType='Sub-hourly',
    #                                                          rainfallTimeStepValue='d',
    #                                                          routingTimeStepType='Hourly',
    #                                                          routingTimeStepValue='f',
    #                                                          simulationTimeStepType='Annual',
    #                                                          simulationTimeStepValue='h',
    #                                                          watershedArea='i',
    #                                                          numberOfSubbasins='j',
    #                                                          numberOfHRUs='k',
    #                                                          demResolution='l',
    #                                                          demSourceName='m',
    #                                                          demSourceURL='n',
    #                                                          landUseDataSourceName='o',
    #                                                          landUseDataSourceURL='p',
    #                                                          soilDataSourceName='q',
    #                                                          soilDataSourceURL='r',
    #                                                          )
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.warmupPeriodValue, 'b')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.rainfallTimeStepType, 'Sub-hourly')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.rainfallTimeStepValue, 'd')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.routingTimeStepType, 'Hourly')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.routingTimeStepValue, 'f')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.simulationTimeStepType, 'Annual')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.simulationTimeStepValue, 'h')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.watershedArea, 'i')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.numberOfSubbasins, 'j')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.numberOfHRUs, 'k')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demResolution, 'l')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demSourceName, 'm')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.demSourceURL, 'n')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.landUseDataSourceName, 'o')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.landUseDataSourceURL, 'p')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.soilDataSourceName, 'q')
    #     self.assertEqual(self.resMODFLOWModelInstance.metadata.model_input.soilDataSourceURL, 'r')
    #
    #     # delete
    #
    #     # check that there are all extended metadata elements at this point
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.executed_by, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_input, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_parameter, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_method, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_objective, None)
    #
    #     # delete all elements
    #     self.resMODFLOWModelInstance.metadata.delete_element('ModelOutput',
    #                                                          self.resMODFLOWModelInstance.metadata.model_output.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('ExecutedBy',
    #                                                          self.resMODFLOWModelInstance.metadata.executed_by.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('ModelInput',
    #                                                          self.resMODFLOWModelInstance.metadata.model_input.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('ModelParameter',
    #                                                          self.resMODFLOWModelInstance.metadata.model_parameter.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('ModelMethod',
    #                                                          self.resMODFLOWModelInstance.metadata.model_method.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('SimulationType',
    #                                                          self.resMODFLOWModelInstance.metadata.simulation_type.id)
    #     self.resMODFLOWModelInstance.metadata.delete_element('ModelObjective',
    #                                                          self.resMODFLOWModelInstance.metadata.model_objective.id)
    #
    #     # make sure they are deleted
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_output, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.executed_by, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_input, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_parameter, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_method, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.model_objective, None)
    #
    # def test_public_or_discoverable(self):
    #     self.assertFalse(self.resMODFLOWModelInstance.has_required_content_files())
    #     self.assertFalse(self.resMODFLOWModelInstance.metadata.has_all_required_elements())
    #     self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
    #
    #     # add file
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #     self.assertTrue(self.resMODFLOWModelInstance.has_required_content_files())
    #     self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
    #
    #     # add generically required elements; still should not be made public
    #     self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
    #
    #     self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.assertFalse(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
    #
    #     # add model objective; should now be ok
    #     s_objs = ["BMPs", "Hydrology", "Water quality"]
    #     o_objs = "elon musk"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelObjective',
    #                                                          swat_model_objectives=s_objs,
    #                                                          other_objectives=o_objs)
    #
    #     self.assertTrue(self.resMODFLOWModelInstance.metadata.has_all_required_elements())
    #     self.assertTrue(self.resMODFLOWModelInstance.can_be_public_or_discoverable)
    #
    # def test_multiple_content_files(self):
    #     self.assertTrue(self.resMODFLOWModelInstance.can_have_multiple_files())
    #
    # def test_get_xml(self):
    #     self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #     s_objs = ["BMPs", "Hydrology", "Water quality"]
    #     o_objs = "elon musk"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelObjective',
    #                                                          swat_model_objectives=s_objs,
    #                                                          other_objectives=o_objs)
    #     self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                          simulation_type_name='Normal Simulation')
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelMethod',
    #                                                          runoffCalculationMethod='aaa',
    #                                                          flowRoutingMethod='bbb',
    #                                                          petEstimationMethod='ccc')
    #     s_params = ["Crop rotation", "Tillage operation"]
    #     o_params = "spongebob"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                          model_parameters=s_params,
    #                                                          other_parameters=o_params)
    #
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                          warmupPeriodValue='a',
    #                                                          rainfallTimeStepType='Daily',
    #                                                          rainfallTimeStepValue='c',
    #                                                          routingTimeStepType='Daily',
    #                                                          routingTimeStepValue='e',
    #                                                          simulationTimeStepType='Hourly',
    #                                                          simulationTimeStepValue='g',
    #                                                          watershedArea='h',
    #                                                          numberOfSubbasins='i',
    #                                                          numberOfHRUs='j',
    #                                                          demResolution='k',
    #                                                          demSourceName='l',
    #                                                          demSourceURL='m',
    #                                                          landUseDataSourceName='n',
    #                                                          landUseDataSourceURL='o',
    #                                                          soilDataSourceName='p',
    #                                                          soilDataSourceURL='q',
    #                                                          )
    #
    #     # test if xml from get_xml() is well formed
    #     ET.fromstring(self.resMODFLOWModelInstance.metadata.get_xml())  # todo check actual xml content
    #
    # def test_metadata_on_content_file_delete(self):
    #     # Metadata should remain after content file deletion
    #
    #     # upload files
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #
    #     # create metadata elements
    #     self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #     s_objs = ["BMPs", "Hydrology", "Water quality"]
    #     o_objs = "elon musk"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelObjective',
    #                                                          swat_model_objectives=s_objs,
    #                                                          other_objectives=o_objs)
    #     self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                          simulation_type_name='Normal Simulation')
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelMethod',
    #                                                          runoffCalculationMethod='aaa',
    #                                                          flowRoutingMethod='bbb',
    #                                                          petEstimationMethod='ccc')
    #     s_params = ["Crop rotation", "Tillage operation"]
    #     o_params = "spongebob"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                          model_parameters=s_params,
    #                                                          other_parameters=o_params)
    #
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                          warmupPeriodValue='a',
    #                                                          rainfallTimeStepType='Daily',
    #                                                          rainfallTimeStepValue='c',
    #                                                          routingTimeStepType='Daily',
    #                                                          routingTimeStepValue='e',
    #                                                          simulationTimeStepType='Hourly',
    #                                                          simulationTimeStepValue='g',
    #                                                          watershedArea='h',
    #                                                          numberOfSubbasins='i',
    #                                                          numberOfHRUs='j',
    #                                                          demResolution='k',
    #                                                          demSourceName='l',
    #                                                          demSourceURL='m',
    #                                                          landUseDataSourceName='n',
    #                                                          landUseDataSourceURL='o',
    #                                                          soilDataSourceName='p',
    #                                                          soilDataSourceURL='q',
    #                                                          )
    #
    #     # there should one content file
    #     self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 1)
    #
    #     # there should be one format element
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.formats.all().count(), 1)
    #
    #     # delete content file that we added above
    #     hydroshare.delete_resource_file(self.resMODFLOWModelInstance.short_id, self.file_name, self.user)
    #
    #     # there should no content file
    #     self.assertEquals(self.resMODFLOWModelInstance.files.all().count(), 0)
    #
    #     # there should be no format element
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.formats.all().count(), 0)
    #
    #     # test the core metadata at this point
    #     self.assertNotEquals(self.resMODFLOWModelInstance.metadata.title, None)
    #
    #     # there should be an abstract element
    #     self.assertNotEquals(self.resMODFLOWModelInstance.metadata.description, None)
    #
    #     # there should be one creator element
    #     self.assertEquals(self.resMODFLOWModelInstance.metadata.creators.all().count(), 1)
    #
    #     # testing extended metadata elements
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_output, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.executed_by, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_input, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_parameter, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_method, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.simulation_type, None)
    #     self.assertNotEqual(self.resMODFLOWModelInstance.metadata.model_objective, None)
    #
    # def test_metadata_delete_on_resource_delete(self):
    #     files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
    #     utils.resource_file_add_pre_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                         extract_metadata=False)
    #
    #     utils.resource_file_add_process(resource=self.resMODFLOWModelInstance, files=files, user=self.user,
    #                                     extract_metadata=False)
    #
    #     # create metadata elements
    #     self.resMODFLOWModelInstance.metadata.create_element('Description', abstract="test abstract")
    #     self.resMODFLOWModelInstance.metadata.create_element('Subject', value="test subject")
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelOutput', includes_output=True)
    #     self.resMODFLOWModelInstance.metadata.create_element('ExecutedBy', model_name=self.resGenModelProgram.short_id)
    #     s_objs = ["BMPs", "Hydrology", "Water quality"]
    #     o_objs = "elon musk"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelObjective',
    #                                                          swat_model_objectives=s_objs,
    #                                                          other_objectives=o_objs)
    #     self.resMODFLOWModelInstance.metadata.create_element('SimulationType',
    #                                                          simulation_type_name='Normal Simulation')
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelMethod',
    #                                                          runoffCalculationMethod='aaa',
    #                                                          flowRoutingMethod='bbb',
    #                                                          petEstimationMethod='ccc')
    #     s_params = ["Crop rotation", "Tillage operation"]
    #     o_params = "spongebob"
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelParameter',
    #                                                          model_parameters=s_params,
    #                                                          other_parameters=o_params)
    #
    #     self.resMODFLOWModelInstance.metadata.create_element('ModelInput',
    #                                                          warmupPeriodValue='a',
    #                                                          rainfallTimeStepType='Daily',
    #                                                          rainfallTimeStepValue='c',
    #                                                          routingTimeStepType='Daily',
    #                                                          routingTimeStepValue='e',
    #                                                          simulationTimeStepType='Hourly',
    #                                                          simulationTimeStepValue='g',
    #                                                          watershedArea='h',
    #                                                          numberOfSubbasins='i',
    #                                                          numberOfHRUs='j',
    #                                                          demResolution='k',
    #                                                          demSourceName='l',
    #                                                          demSourceURL='m',
    #                                                          landUseDataSourceName='n',
    #                                                          landUseDataSourceURL='o',
    #                                                          soilDataSourceName='p',
    #                                                          soilDataSourceURL='q',
    #                                                          )
    #     self.resMODFLOWModelInstance.metadata.create_element('Contributor', name="user2")
    #
    #     # before resource delete
    #     core_metadata_obj = self.resMODFLOWModelInstance.metadata
    #     self.assertEquals(CoreMetaData.objects.all().count(), 3)
    #     # there should be Creator metadata objects
    #     self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Contributor metadata objects
    #     self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Identifier metadata objects
    #     self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Type metadata objects
    #     self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Source metadata objects
    #     self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Relation metadata objects
    #     self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Publisher metadata objects
    #     self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Title metadata objects
    #     self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Description (Abstract) metadata objects
    #     self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Date metadata objects
    #     self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Subject metadata objects
    #     self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Coverage metadata objects
    #     self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Format metadata objects
    #     self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Language metadata objects
    #     self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be Rights metadata objects
    #     self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # resource specific metadata
    #     self.assertEquals(SWATModelInstanceMetaData.objects.all().count(), 1)
    #     # there should be Model Output metadata objects
    #     self.assertTrue(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ExecutedBy metadata objects
    #     self.assertTrue(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ModelObjective metadata objects
    #     self.assertTrue(ModelObjective.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be SimulationType metadata objects
    #     self.assertTrue(SimulationType.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ModelMethod metadata objects
    #     self.assertTrue(ModelMethod.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ModelParameter metadata objects
    #     self.assertTrue(ModelParameter.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be ModelInput metadata objects
    #     self.assertTrue(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # delete resource
    #     hydroshare.delete_resource(self.resMODFLOWModelInstance.short_id)
    #     self.assertEquals(CoreMetaData.objects.all().count(), 2)
    #     self.assertEquals(SWATModelInstanceMetaData.objects.all().count(), 0)
    #
    #     # there should be no Creator metadata objects
    #     self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Contributor metadata objects
    #     self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Identifier metadata objects
    #     self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Type metadata objects
    #     self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Source metadata objects
    #     self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Relation metadata objects
    #     self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Publisher metadata objects
    #     self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Title metadata objects
    #     self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Description (Abstract) metadata objects
    #     self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Date metadata objects
    #     self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Subject metadata objects
    #     self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Coverage metadata objects
    #     self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Format metadata objects
    #     self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Language metadata objects
    #     self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no Rights metadata objects
    #     self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
    #
    #     # resource specific metadata
    #     # there should be no Model Output metadata objects
    #     self.assertFalse(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ExecutedBy metadata objects
    #     self.assertFalse(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ModelObjective metadata objects
    #     self.assertFalse(ModelObjective.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no SimulationType metadata objects
    #     self.assertFalse(SimulationType.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ModelMethod metadata objects
    #     self.assertFalse(ModelMethod.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ModelParameter metadata objects
    #     self.assertFalse(ModelParameter.objects.filter(object_id=core_metadata_obj.id).exists())
    #     # there should be no ModelInput metadata objects
    #     self.assertFalse(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())
