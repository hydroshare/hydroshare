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
from hs_swat_modelinstance.models import SWATModelInstanceMetaData, ModelObjective, ModelMethod, \
    ModelParameter, ModelInput, ModelOutput, ExecutedBy, SimulationType


class TestSWATModelInstanceMetaData(MockIRODSTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestSWATModelInstanceMetaData, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[self.group]
        )

        self.resSWATModelInstance = hydroshare.create_resource(
            resource_type='SWATModelInstanceResource',
            owner=self.user,
            title='Test SWAT Model Instance Resource'
        )

        self.resGenModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model SWAT Program Resource'
        )

        self.resSwatModelProgram = hydroshare.create_resource(
            resource_type='ModelProgramResource',
            owner=self.user,
            title='Model Program Resource 2'
        )

        self.temp_dir = tempfile.mkdtemp()

        self.file_name = "MIR.txt"
        temp_text_file = os.path.join(self.temp_dir, self.file_name)
        text_file = open(temp_text_file, 'w')
        text_file.write("Model SWAT Instance resource files")
        text_file.close()
        self.text_file_obj = open(temp_text_file, 'r')

        self.file_name_2 = "MIR.csv"
        temp_text_file_2 = os.path.join(self.temp_dir, self.file_name_2)
        text_file = open(temp_text_file_2, 'w')
        text_file.write("Model,SWAT,Instance,resource,files")
        text_file.close()
        self.text_file_obj_2 = open(temp_text_file_2, 'r')

    def tearDown(self):
        super(TestSWATModelInstanceMetaData, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_allowed_file_types(self):
        # test allowed file type is '.*'
        self.assertEquals(self.resSWATModelInstance.get_supported_upload_file_types(), '.*')

        # there should not be any content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 0)

        # Upload any file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files,
                                        user=self.user, extract_metadata=False)

        # there should one content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 1)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)

        # Upload any other file type should pass both the file pre add check post add check
        files = [UploadedFile(file=self.text_file_obj_2, name=self.text_file_obj_2.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files,
                                            user=self.user, extract_metadata=True)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files,
                                        user=self.user, extract_metadata=True)

        # there should two content files
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 2)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)

    def test_extended_metadata_CRUD(self):
        # test the core metadata at this point
        # there should be a title element
        self.assertEquals(self.resSWATModelInstance.metadata.title.value,
                          'Test SWAT Model Instance Resource')

        # there should be a creator element
        self.assertEquals(self.resSWATModelInstance.metadata.creators.count(), 1)

        # # there should be a type element
        self.assertNotEqual(self.resSWATModelInstance.metadata.type, None)

        # there should be an identifier element
        self.assertEquals(self.resSWATModelInstance.metadata.identifiers.count(), 1)

        # there should be rights element
        self.assertNotEqual(self.resSWATModelInstance.metadata.rights, None)

        # there shouldn't any source element
        self.assertEquals(self.resSWATModelInstance.metadata.sources.count(), 0)

        # there shouldn't any relation element
        self.assertEquals(self.resSWATModelInstance.metadata.relations.count(), 0)

        # there shouldn't any abstract element
        self.assertEquals(self.resSWATModelInstance.metadata.description, None)

        # there shouldn't any coverage element
        self.assertEquals(self.resSWATModelInstance.metadata.coverages.all().count(), 0)

        # there shouldn't any format element
        self.assertEquals(self.resSWATModelInstance.metadata.formats.all().count(), 0)

        # there shouldn't any subject element
        self.assertEquals(self.resSWATModelInstance.metadata.subjects.all().count(), 0)

        # there shouldn't any contributor element
        self.assertEquals(self.resSWATModelInstance.metadata.contributors.all().count(), 0)

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_input, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_method, None)
        self.assertEquals(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_objective, None)

        # create
        # create model_output
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)
        modeloutput_element = self.resSWATModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, False)
        # multiple ModelOutput elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)
        self.resSWATModelInstance.metadata.delete_element(
            'ModelOutput',
            self.resSWATModelInstance.metadata.model_output.id
        )
        self.assertEqual(self.resSWATModelInstance.metadata.model_output, None)
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        modeloutput_element = self.resSWATModelInstance.metadata.model_output
        self.assertEquals(modeloutput_element.includes_output, True)
        # multiple ModelOutput elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
            self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=False)

        # create ExecutedBy
        self.resSWATModelInstance.metadata.create_element(
            'ExecutedBy',
            model_name=self.resGenModelProgram.short_id
        )
        modelparam_element = self.resSWATModelInstance.metadata.executed_by
        self.assertEquals(modelparam_element.model_name,
                          self.resGenModelProgram.metadata.title.value)
        self.assertEquals(modelparam_element.model_program_fk, self.resGenModelProgram)
        # multiple ExecutedBy elements are not allowed - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element(
                'ExecutedBy',
                model_name=self.resSwatModelProgram.short_id
            )

        # create ModelObjective
        # try to create a modelobjective with no swat_model_objective - it would raise an exception
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                              other_objectives="boaty mcboatface")
        # now do it legit
        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives=s_objs,
                                                          other_objectives=o_objs)
        modelparam_element = self.resSWATModelInstance.metadata.model_objective
        self.assertNotEqual(modelparam_element, None)
        v = modelparam_element.get_swat_model_objectives()
        for o in s_objs:
            self.assertEquals(o in v, True)
        self.assertEquals(modelparam_element.other_objectives, o_objs)
        # try to create a swat_model_objective with a non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element(
                'ModelObjective',
                swat_model_objectives=['gravity waves']
            )
        # try to create another swat_model_objective - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                              swat_model_objectives=[s_objs[0]],
                                                              other_objectives="bleh")

        # create simulation type
        # try to create a simulation type with a non cv term - it would raise an exception
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('SimulationType',
                                                              simulation_type_name='bilbo baggins')
        # create legit SimType
        self.resSWATModelInstance.metadata.create_element('SimulationType',
                                                          simulation_type_name='Normal Simulation')
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEqual(
            self.resSWATModelInstance.metadata.simulation_type.get_simulation_type_name_display(),
            'Normal Simulation'
        )
        # try to create another simulation type - it would raise an exception
        with self.assertRaises(IntegrityError):
                self.resSWATModelInstance.metadata.create_element(
                    'SimulationType',
                    simulation_type_name='Sensitivity Analysis'
                )

        # create modelmethod
        self.resSWATModelInstance.metadata.create_element('ModelMethod',
                                                          runoffCalculationMethod='aaa',
                                                          flowRoutingMethod='bbb',
                                                          petEstimationMethod='ccc')
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_method, None)
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.runoffCalculationMethod,
                         'aaa')
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.flowRoutingMethod, 'bbb')
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.petEstimationMethod, 'ccc')
        # try to create another model_method - it would raise an exception
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelMethod',
                                                              runoffCalculationMethod='bbb',
                                                              flowRoutingMethod='ccc',
                                                              petEstimationMethod='ddd')

        # create ModelParameter
        # try to create a modelparam with a non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                              model_parameters="chucky cheese")
        # try to create a modelparam with a no model_parameter term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('ModelParameter', george="clooney")
        # create legit modelparam
        s_params = ["Crop rotation", "Tillage operation"]
        o_params = "spongebob"
        self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                          model_parameters=s_params,
                                                          other_parameters=o_params)
        modelparam_element = self.resSWATModelInstance.metadata.model_parameter
        self.assertNotEqual(modelparam_element, None)
        v = modelparam_element.get_swat_model_parameters()
        for p in s_params:
            self.assertEquals(p in v, True)
        self.assertEquals(modelparam_element.other_parameters, o_params)
        # try to create another swat_model_objective
        with self.assertRaises(IntegrityError):
            self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                              model_parameters=[s_params[0]],
                                                              other_parameters="bleh")

        # create ModelInput
        # try to create a ModelInput with non cv terms
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                              rainfallTimeStepType='frodo baggins')
            self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                              routingTimeStepType='legolas')
            self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                              simulationTimeStepType='gandalf')
        # create normal ModelInput
        self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                          warmupPeriodValue='a',
                                                          rainfallTimeStepType='Daily',
                                                          rainfallTimeStepValue='c',
                                                          routingTimeStepType='Daily',
                                                          routingTimeStepValue='e',
                                                          simulationTimeStepType='Hourly',
                                                          simulationTimeStepValue='g',
                                                          watershedArea='h',
                                                          numberOfSubbasins='i',
                                                          numberOfHRUs='j',
                                                          demResolution='k',
                                                          demSourceName='l',
                                                          demSourceURL='m',
                                                          landUseDataSourceName='n',
                                                          landUseDataSourceURL='o',
                                                          soilDataSourceName='p',
                                                          soilDataSourceURL='q',
                                                          )
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.warmupPeriodValue, 'a')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.rainfallTimeStepType,
                         'Daily')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.rainfallTimeStepValue, 'c')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.routingTimeStepType,
                         'Daily')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.routingTimeStepValue, 'e')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.simulationTimeStepType,
                         'Hourly')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.simulationTimeStepValue,
                         'g')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.watershedArea, 'h')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.numberOfSubbasins, 'i')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.numberOfHRUs, 'j')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demResolution, 'k')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demSourceName, 'l')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demSourceURL, 'm')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.landUseDataSourceName, 'n')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.landUseDataSourceURL, 'o')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.soilDataSourceName, 'p')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.soilDataSourceURL, 'q')
        # try to create another ModelInput
        with self.assertRaises(IntegrityError):
                self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                                  warmupPeriodValue='patrick')

        # update

        # update ModelOutput
        self.resSWATModelInstance.metadata.update_element(
            'ModelOutput',
            self.resSWATModelInstance.metadata.model_output.id,
            includes_output=False
        )
        self.assertEquals(self.resSWATModelInstance.metadata.model_output.includes_output, False)
        self.resSWATModelInstance.metadata.update_element(
            'ModelOutput',
            self.resSWATModelInstance.metadata.model_output.id,
            includes_output=True
        )
        self.assertEquals(self.resSWATModelInstance.metadata.model_output.includes_output, True)

        # update ExecutedBy
        self.resSWATModelInstance.metadata.update_element(
            'ExecutedBy',
            self.resSWATModelInstance.metadata.executed_by.id,
            model_name=self.resSwatModelProgram.short_id
        )
        modelparam_element = self.resSWATModelInstance.metadata.executed_by
        self.assertEquals(modelparam_element.model_name,
                          self.resSwatModelProgram.metadata.title.value)
        self.assertEquals(modelparam_element.model_program_fk, self.resSwatModelProgram)

        # update ModelObjective
        self.resSWATModelInstance.metadata.update_element(
            'ModelObjective',
            self.resSWATModelInstance.metadata.model_objective.id,
            swat_model_objectives=[s_objs[2]],
            other_objectives='jelly beans'
        )
        modelparam_element = self.resSWATModelInstance.metadata.model_objective
        self.assertNotEqual(modelparam_element, None)
        v = modelparam_element.get_swat_model_objectives()
        for o in [s_objs[2]]:
            self.assertEquals(o in v, True)
        self.assertEquals(modelparam_element.other_objectives, 'jelly beans')
        # try with a non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.update_element(
                'ModelObjective',
                self.resSWATModelInstance.metadata.model_objective.id,
                swat_model_objectives=["gravity waves"])
        # update just other objective
        self.resSWATModelInstance.metadata.update_element(
            'ModelObjective',
            self.resSWATModelInstance.metadata.model_objective.id,
            other_objectives="einstein")
        modelparam_element = self.resSWATModelInstance.metadata.model_objective
        self.assertEquals(modelparam_element.other_objectives, 'einstein')

        # update SimulationType
        self.resSWATModelInstance.metadata.update_element(
            'SimulationType',
            self.resSWATModelInstance.metadata.simulation_type.id,
            simulation_type_name='Auto-Calibration')
        modelparam_element = self.resSWATModelInstance.metadata.simulation_type
        self.assertEquals(modelparam_element.get_simulation_type_name_display(), 'Auto-Calibration')
        # try with non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.update_element(
                'SimulationType',
                self.resSWATModelInstance.metadata.simulation_type.id,
                simulation_type_name="Panda")

        # update ModelMethod
        self.resSWATModelInstance.metadata.update_element(
            'ModelMethod',
            self.resSWATModelInstance.metadata.model_method.id,
            runoffCalculationMethod="go hoos",
            flowRoutingMethod='rotunda',
            petEstimationMethod='honor code')
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.runoffCalculationMethod,
                         'go hoos')
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.flowRoutingMethod,
                         'rotunda')
        self.assertEqual(self.resSWATModelInstance.metadata.model_method.petEstimationMethod,
                         'honor code')

        # update ModelParameter
        # try to update a modelparam with a non cv term
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.update_element(
                'ModelParameter',
                self.resSWATModelInstance.metadata.model_parameter.id,
                model_parameters="chucky cheese")
        # update legit modelparam
        s_params = ["Point source", "Fertilizer"]
        self.resSWATModelInstance.metadata.update_element(
            'ModelParameter',
            self.resSWATModelInstance.metadata.model_parameter.id,
            model_parameters=s_params)
        modelparam_element = self.resSWATModelInstance.metadata.model_parameter
        v = modelparam_element.get_swat_model_parameters()
        for p in s_params:
            self.assertEquals(p in v, True)
        self.assertEquals(modelparam_element.other_parameters, o_params)
        # now update the other params
        o_params = 'square pants'
        self.resSWATModelInstance.metadata.update_element(
            'ModelParameter',
            self.resSWATModelInstance.metadata.model_parameter.id,
            other_parameters=o_params)
        # check that the other params was updated and that the model params are the same
        modelparam_element = self.resSWATModelInstance.metadata.model_parameter
        v = modelparam_element.get_swat_model_parameters()
        for p in s_params:
            self.assertEquals(p in v, True)
        self.assertEquals(modelparam_element.other_parameters, o_params)

        # update ModelInput
        # try to update a ModelInput with non cv terms
        with self.assertRaises(ValidationError):
            self.resSWATModelInstance.metadata.update_element(
                'ModelInput',
                self.resSWATModelInstance.metadata.model_input.id,
                rainfallTimeStepType='frodo baggins')
            self.resSWATModelInstance.metadata.update_element(
                'ModelInput',
                self.resSWATModelInstance.metadata.model_input.id,
                routingTimeStepType='legolas')
            self.resSWATModelInstance.metadata.update_element(
                'ModelInput',
                self.resSWATModelInstance.metadata.model_input.id,
                simulationTimeStepType='gandalf')
        # update normal ModelInput
        self.resSWATModelInstance.metadata.update_element(
            'ModelInput',
            self.resSWATModelInstance.metadata.model_input.id,
            warmupPeriodValue='b',
            rainfallTimeStepType='Sub-hourly',
            rainfallTimeStepValue='d',
            routingTimeStepType='Hourly',
            routingTimeStepValue='f',
            simulationTimeStepType='Annual',
            simulationTimeStepValue='h',
            watershedArea='i',
            numberOfSubbasins='j',
            numberOfHRUs='k',
            demResolution='l',
            demSourceName='m',
            demSourceURL='n',
            landUseDataSourceName='o',
            landUseDataSourceURL='p',
            soilDataSourceName='q',
            soilDataSourceURL='r',
        )
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.warmupPeriodValue, 'b')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.rainfallTimeStepType,
                         'Sub-hourly')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.rainfallTimeStepValue, 'd')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.routingTimeStepType,
                         'Hourly')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.routingTimeStepValue, 'f')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.simulationTimeStepType,
                         'Annual')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.simulationTimeStepValue,
                         'h')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.watershedArea, 'i')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.numberOfSubbasins, 'j')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.numberOfHRUs, 'k')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demResolution, 'l')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demSourceName, 'm')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.demSourceURL, 'n')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.landUseDataSourceName, 'o')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.landUseDataSourceURL, 'p')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.soilDataSourceName, 'q')
        self.assertEqual(self.resSWATModelInstance.metadata.model_input.soilDataSourceURL, 'r')

        # delete

        # check that there are all extended metadata elements at this point
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_input, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_method, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_objective, None)

        # delete all elements
        self.resSWATModelInstance.metadata.delete_element(
            'ModelOutput',
            self.resSWATModelInstance.metadata.model_output.id)
        self.resSWATModelInstance.metadata.delete_element(
            'ExecutedBy',
            self.resSWATModelInstance.metadata.executed_by.id)
        self.resSWATModelInstance.metadata.delete_element(
            'ModelInput',
            self.resSWATModelInstance.metadata.model_input.id)
        self.resSWATModelInstance.metadata.delete_element(
            'ModelParameter',
            self.resSWATModelInstance.metadata.model_parameter.id)
        self.resSWATModelInstance.metadata.delete_element(
            'ModelMethod',
            self.resSWATModelInstance.metadata.model_method.id)
        self.resSWATModelInstance.metadata.delete_element(
            'SimulationType',
            self.resSWATModelInstance.metadata.simulation_type.id)
        self.resSWATModelInstance.metadata.delete_element(
            'ModelObjective',
            self.resSWATModelInstance.metadata.model_objective.id)

        # make sure they are deleted
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_input, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_method, None)
        self.assertEquals(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_objective, None)

    def test_public_or_discoverable(self):
        self.assertFalse(self.resSWATModelInstance.has_required_content_files())
        self.assertFalse(self.resSWATModelInstance.metadata.has_all_required_elements())
        self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)

        # add file
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files,
                                        user=self.user, extract_metadata=False)
        self.assertTrue(self.resSWATModelInstance.has_required_content_files())
        self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)

        # add generically required elements; still should not be made public
        self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)

        self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
        self.assertFalse(self.resSWATModelInstance.can_be_public_or_discoverable)

        # add model objective; should now be ok
        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives=s_objs,
                                                          other_objectives=o_objs)

        self.assertTrue(self.resSWATModelInstance.metadata.has_all_required_elements())
        self.assertTrue(self.resSWATModelInstance.can_be_public_or_discoverable)

    def test_can_have_multiple_content_files(self):
        self.assertTrue(self.resSWATModelInstance.can_have_multiple_files())

    def test_can_upload_multiple_content_files(self):
        # can upload multiple files
        self.assertTrue(self.resSWATModelInstance.allow_multiple_file_upload())

    def test_get_xml(self):
        self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resSWATModelInstance.metadata.create_element(
            'ExecutedBy',
            model_name=self.resGenModelProgram.short_id)
        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives=s_objs,
                                                          other_objectives=o_objs)
        self.resSWATModelInstance.metadata.create_element('SimulationType',
                                                          simulation_type_name='Normal Simulation')
        self.resSWATModelInstance.metadata.create_element('ModelMethod',
                                                          runoffCalculationMethod='aaa',
                                                          flowRoutingMethod='bbb',
                                                          petEstimationMethod='ccc')
        s_params = ["Crop rotation", "Tillage operation"]
        o_params = "spongebob"
        self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                          model_parameters=s_params,
                                                          other_parameters=o_params)

        self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                          warmupPeriodValue='a',
                                                          rainfallTimeStepType='Daily',
                                                          rainfallTimeStepValue='c',
                                                          routingTimeStepType='Daily',
                                                          routingTimeStepValue='e',
                                                          simulationTimeStepType='Hourly',
                                                          simulationTimeStepValue='g',
                                                          watershedArea='h',
                                                          numberOfSubbasins='i',
                                                          numberOfHRUs='j',
                                                          demResolution='k',
                                                          demSourceName='l',
                                                          demSourceURL='m',
                                                          landUseDataSourceName='n',
                                                          landUseDataSourceURL='o',
                                                          soilDataSourceName='p',
                                                          soilDataSourceURL='q',
                                                          )

        # test if xml from get_xml() is well formed
        ET.fromstring(self.resSWATModelInstance.metadata.get_xml())  # todo check actual xml content

    def test_metadata_on_content_file_delete(self):
        # Metadata should remain after content file deletion

        # upload files
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files,
                                        user=self.user, extract_metadata=False)

        # create metadata elements
        self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resSWATModelInstance.metadata.create_element(
            'ExecutedBy',
            model_name=self.resGenModelProgram.short_id)
        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives=s_objs,
                                                          other_objectives=o_objs)
        self.resSWATModelInstance.metadata.create_element('SimulationType',
                                                          simulation_type_name='Normal Simulation')
        self.resSWATModelInstance.metadata.create_element('ModelMethod',
                                                          runoffCalculationMethod='aaa',
                                                          flowRoutingMethod='bbb',
                                                          petEstimationMethod='ccc')
        s_params = ["Crop rotation", "Tillage operation"]
        o_params = "spongebob"
        self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                          model_parameters=s_params,
                                                          other_parameters=o_params)

        self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                          warmupPeriodValue='a',
                                                          rainfallTimeStepType='Daily',
                                                          rainfallTimeStepValue='c',
                                                          routingTimeStepType='Daily',
                                                          routingTimeStepValue='e',
                                                          simulationTimeStepType='Hourly',
                                                          simulationTimeStepValue='g',
                                                          watershedArea='h',
                                                          numberOfSubbasins='i',
                                                          numberOfHRUs='j',
                                                          demResolution='k',
                                                          demSourceName='l',
                                                          demSourceURL='m',
                                                          landUseDataSourceName='n',
                                                          landUseDataSourceURL='o',
                                                          soilDataSourceName='p',
                                                          soilDataSourceURL='q',
                                                          )

        # there should one content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 1)

        # there should be one format element
        self.assertEquals(self.resSWATModelInstance.metadata.formats.all().count(), 1)

        # file name should be the short path to the object
        self.assertEquals(self.resSWATModelInstance.files.all()[0].short_path, self.file_name)

        # delete content file that we added above
        hydroshare.delete_resource_file(self.resSWATModelInstance.short_id, self.file_name,
                                        self.user)

        # there should no content file
        self.assertEquals(self.resSWATModelInstance.files.all().count(), 0)

        # there should be no format element
        self.assertEquals(self.resSWATModelInstance.metadata.formats.all().count(), 0)

        # test the core metadata at this point
        self.assertNotEquals(self.resSWATModelInstance.metadata.title, None)

        # there should be an abstract element
        self.assertNotEquals(self.resSWATModelInstance.metadata.description, None)

        # there should be one creator element
        self.assertEquals(self.resSWATModelInstance.metadata.creators.all().count(), 1)

        # testing extended metadata elements
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_input, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_method, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_objective, None)

    def test_metadata_delete_on_resource_delete(self):
        files = [UploadedFile(file=self.text_file_obj, name=self.text_file_obj.name)]
        utils.resource_file_add_pre_process(resource=self.resSWATModelInstance, files=files,
                                            user=self.user, extract_metadata=False)

        utils.resource_file_add_process(resource=self.resSWATModelInstance, files=files,
                                        user=self.user, extract_metadata=False)

        # create metadata elements
        self.resSWATModelInstance.metadata.create_element('Description', abstract="test abstract")
        self.resSWATModelInstance.metadata.create_element('Subject', value="test subject")
        self.resSWATModelInstance.metadata.create_element('ModelOutput', includes_output=True)
        self.resSWATModelInstance.metadata.create_element(
            'ExecutedBy',
            model_name=self.resGenModelProgram.short_id)
        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "elon musk"
        self.resSWATModelInstance.metadata.create_element('ModelObjective',
                                                          swat_model_objectives=s_objs,
                                                          other_objectives=o_objs)
        self.resSWATModelInstance.metadata.create_element('SimulationType',
                                                          simulation_type_name='Normal Simulation')
        self.resSWATModelInstance.metadata.create_element('ModelMethod',
                                                          runoffCalculationMethod='aaa',
                                                          flowRoutingMethod='bbb',
                                                          petEstimationMethod='ccc')
        s_params = ["Crop rotation", "Tillage operation"]
        o_params = "spongebob"
        self.resSWATModelInstance.metadata.create_element('ModelParameter',
                                                          model_parameters=s_params,
                                                          other_parameters=o_params)

        self.resSWATModelInstance.metadata.create_element('ModelInput',
                                                          warmupPeriodValue='a',
                                                          rainfallTimeStepType='Daily',
                                                          rainfallTimeStepValue='c',
                                                          routingTimeStepType='Daily',
                                                          routingTimeStepValue='e',
                                                          simulationTimeStepType='Hourly',
                                                          simulationTimeStepValue='g',
                                                          watershedArea='h',
                                                          numberOfSubbasins='i',
                                                          numberOfHRUs='j',
                                                          demResolution='k',
                                                          demSourceName='l',
                                                          demSourceURL='m',
                                                          landUseDataSourceName='n',
                                                          landUseDataSourceURL='o',
                                                          soilDataSourceName='p',
                                                          soilDataSourceURL='q',
                                                          )
        self.resSWATModelInstance.metadata.create_element('Contributor', name="user2")

        # before resource delete
        core_metadata_obj = self.resSWATModelInstance.metadata
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
        self.assertEquals(SWATModelInstanceMetaData.objects.all().count(), 1)
        # there should be Model Output metadata objects
        self.assertTrue(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ExecutedBy metadata objects
        self.assertTrue(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelObjective metadata objects
        self.assertTrue(ModelObjective.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be SimulationType metadata objects
        self.assertTrue(SimulationType.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelMethod metadata objects
        self.assertTrue(ModelMethod.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelParameter metadata objects
        self.assertTrue(ModelParameter.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be ModelInput metadata objects
        self.assertTrue(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.resSWATModelInstance.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 2)
        self.assertEquals(SWATModelInstanceMetaData.objects.all().count(), 0)

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
        # there should be no Model Output metadata objects
        self.assertFalse(ModelOutput.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ExecutedBy metadata objects
        self.assertFalse(ExecutedBy.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ModelObjective metadata objects
        self.assertFalse(ModelObjective.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no SimulationType metadata objects
        self.assertFalse(SimulationType.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ModelMethod metadata objects
        self.assertFalse(ModelMethod.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ModelParameter metadata objects
        self.assertFalse(ModelParameter.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no ModelInput metadata objects
        self.assertFalse(ModelInput.objects.filter(object_id=core_metadata_obj.id).exists())

    def test_bulk_metadata_update(self):
        # here we are testing the update() method of the SWATModelInstanceMetaData class

        # check that there are no extended metadata elements at this point
        self.assertEquals(self.resSWATModelInstance.metadata.model_output, None)
        self.assertEquals(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_input, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_method, None)
        self.assertEquals(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertEquals(self.resSWATModelInstance.metadata.model_objective, None)

        # create modeloutput element using the update()
        self.resSWATModelInstance.metadata.update([{'modeloutput': {'includes_output': False}}],
                                                  self.user)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)

        self.resSWATModelInstance.metadata.update([{'modeloutput': {'includes_output': True}}],
                                                  self.user)
        self.assertEqual(self.resSWATModelInstance.metadata.model_output.includes_output, True)

        # test that we can also update core metadata using update()
        # there should be a creator element
        self.assertEqual(self.resSWATModelInstance.metadata.creators.count(), 1)
        self.resSWATModelInstance.metadata.update([{'creator': {'name': 'Second Creator'}},
                                                   {'creator': {'name': 'Third Creator'}}],
                                                  self.user)
        # there should be 2 creators at this point (previously existed creator gets
        # delete as part of the update() call
        self.assertEqual(self.resSWATModelInstance.metadata.creators.count(), 2)

        # test multiple updates in a single call to update()
        metadata = list()
        metadata.append({'executedby': {'model_name': self.resGenModelProgram.short_id}})
        metadata.append({'modeloutput': {'includes_output': False}})
        metadata.append({'modelobjective': {'swat_model_objectives':
                                            ["BMPs", "Hydrology", "Water quality"],
                                            'other_objectives': 'elon musk'}})
        metadata.append({'simulationtype': {'simulation_type_name': 'Normal Simulation'}})
        metadata.append({'modelmethod': {'runoffCalculationMethod': 'aaa',
                                         'flowRoutingMethod': 'bbb', 'petEstimationMethod': 'ccc'}})
        metadata.append({'modelparameter': {'model_parameters':
                                            ["Crop rotation", "Tillage operation"],
                                            'other_parameters': 'spongebob'}})
        metadata.append({'modelinput': {'warmupPeriodValue': 'a',
                                        'rainfallTimeStepType': 'Daily',
                                        'rainfallTimeStepValue': 'c',
                                        'routingTimeStepType': 'Daily',
                                        'routingTimeStepValue': 'e',
                                        'simulationTimeStepType': 'Hourly',
                                        'simulationTimeStepValue': 'g',
                                        'watershedArea': 'h',
                                        'numberOfSubbasins': 'i',
                                        'numberOfHRUs': 'j',
                                        'demResolution': 'k',
                                        'demSourceName': 'l',
                                        'demSourceURL': 'm',
                                        'landUseDataSourceName': 'n',
                                        'landUseDataSourceURL': 'o',
                                        'soilDataSourceName': 'p',
                                        'soilDataSourceURL': 'q'}})

        self.resSWATModelInstance.metadata.update(metadata, self.user)

        # check that there are extended metadata elements at this point
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_output, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.executed_by, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_input, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_parameter, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_method, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.simulation_type, None)
        self.assertNotEqual(self.resSWATModelInstance.metadata.model_objective, None)
