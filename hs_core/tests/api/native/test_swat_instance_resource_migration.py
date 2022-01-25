import os
import sys
import traceback
from unittest import TestCase

import jsonschema
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile
from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_swat_modelinstance.models import SWATModelInstanceResource


class TestSWATInstanceResourceMigration(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestSWATInstanceResourceMigration, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'mi_resource_migration@email.com',
            username='mi_resource_migration',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )
        self.mi_migration_command = "migrate_swat_model_instance_resources"
        self.mp_migration_command = "migrate_model_program_resources"
        self.prepare_mi_migration_command = "prepare_model_instance_resources_for_migration"
        self.MIGRATED_FROM_EXTRA_META_KEY = "MIGRATED_FROM"
        self.MIGRATING_RESOURCE_TYPE = "SWAT Model Instance Resource"
        self.EXECUTED_BY_EXTRA_META_KEY = "EXECUTED_BY_RES_ID"
        self.MI_FOLDER_NAME = "swat-instance"
        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()

    def tearDown(self):
        super(TestSWATInstanceResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        SWATModelInstanceResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()
        ModelProgramResource.objects.all().delete()

    def test_migrate_no_swat_specific_metadata(self):
        """
        Here we are testing that we can migrate a swat mi resource that doesn't have any swat specific metadata
        """
        mi_res = self._create_swat_resource()
        # check that there are no model specific metadata
        self.assertEqual(mi_res.metadata.model_objective, None)
        self.assertEqual(mi_res.metadata.simulation_type, None)
        self.assertEqual(mi_res.metadata.model_method, None)
        self.assertEqual(mi_res.metadata.model_parameter, None)
        self.assertEqual(mi_res.metadata.model_input, None)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)

        # migrate the swat resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check the mi aggregation has meta schema
        self.assertNotEqual(mi_aggr.metadata_schema_json, {})
        # check the json metadata in mi aggregation - there should not me any swat specific metadata
        self.assertEqual(mi_aggr.metadata.metadata_json, {})
        json_meta_fields = ['modelInput', 'modelMethod', 'modelObjective', 'modelParameter', 'simulationType']
        for meta_field in json_meta_fields:
            self.assertTrue(meta_field not in mi_aggr.metadata.metadata_json)

    def test_migrate_swat_specific_metadata_only_modelMethod(self):
        """
        Here we are testing that we can migrate a swat mi resource that has only one swat specific
        metadata 'model method'
        """
        mi_res = self._create_swat_resource()
        mi_res.metadata.create_element('ModelMethod',
                                       runoffCalculationMethod='aaa',
                                       flowRoutingMethod='bbb',
                                       petEstimationMethod='ccc')
        # check that there is only 'model method' swat model specific metadata
        self.assertEqual(mi_res.metadata.model_objective, None)
        self.assertEqual(mi_res.metadata.simulation_type, None)
        self.assertNotEqual(mi_res.metadata.model_method, None)
        self.assertEqual(mi_res.metadata.model_parameter, None)
        self.assertEqual(mi_res.metadata.model_input, None)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)

        # migrate the swat resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check the mi aggregation has meta schema
        self.assertNotEqual(mi_aggr.metadata_schema_json, {})
        # check the json metadata in mi aggregation - there should be swat specific metadata
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelMethod'], {})
        model_method = mi_aggr.metadata.metadata_json['modelMethod']
        self.assertEqual(model_method['runoffCalculationMethod'], 'aaa')
        self.assertEqual(model_method['flowRoutingMethod'], 'bbb')
        self.assertEqual(model_method['petEstimationMethod'], 'ccc')
        json_meta_fields = ['modelInput', 'modelMethod', 'modelObjective', 'modelParameter', 'simulationType']
        for meta_field in json_meta_fields:
            if meta_field == 'modelMethod':
                self.assertTrue(meta_field in mi_aggr.metadata.metadata_json)
            else:
                self.assertTrue(meta_field not in mi_aggr.metadata.metadata_json)

        self._validate_meta_with_schema(mi_aggr)

    def test_migrate_swat_specific_metadata_all_metadata(self):
        """
        Here we are testing that we can migrate a swat mi resource that has all swat specific
        metadata
        """
        mi_res = self._create_swat_resource()
        mi_res.metadata.create_element('ModelMethod',
                                       runoffCalculationMethod='aaa',
                                       flowRoutingMethod='bbb',
                                       petEstimationMethod='ccc')

        s_params = ["Crop rotation", "Tillage operation"]
        o_params = "spongebob"
        mi_res.metadata.create_element('ModelParameter',
                                       model_parameters=s_params,
                                       other_parameters=o_params)

        s_objs = ["BMPs", "Hydrology", "Water quality"]
        o_objs = "some other objective"
        mi_res.metadata.create_element('ModelObjective',
                                       swat_model_objectives=s_objs,
                                       other_objectives=o_objs)

        mi_res.metadata.create_element('ModelInput',
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

        mi_res.metadata.create_element('SimulationType', simulation_type_name='Normal Simulation')

        # check that there exists all the swat model specific metadata
        self.assertNotEqual(mi_res.metadata.model_objective, None)
        self.assertNotEqual(mi_res.metadata.simulation_type, None)
        self.assertNotEqual(mi_res.metadata.model_method, None)
        self.assertNotEqual(mi_res.metadata.model_parameter, None)
        self.assertNotEqual(mi_res.metadata.model_input, None)

        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        # migrate the swat resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check the mi aggregation has meta schema
        self.assertNotEqual(mi_aggr.metadata_schema_json, {})
        # check the json metadata in mi aggregation - there should be swat specific metadata
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelMethod'], {})
        model_method = mi_aggr.metadata.metadata_json['modelMethod']
        self.assertEqual(model_method['runoffCalculationMethod'], 'aaa')
        self.assertEqual(model_method['flowRoutingMethod'], 'bbb')
        self.assertEqual(model_method['petEstimationMethod'], 'ccc')
        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelParameter'], {})
        model_parameter = mi_aggr.metadata.metadata_json['modelParameter']
        self.assertEqual(model_parameter['cropRotation'], True)
        self.assertEqual(model_parameter['tillageOperation'], True)
        self.assertEqual(model_parameter['fertilizer'], False)
        self.assertEqual(model_parameter['pointSource'], False)
        self.assertEqual(model_parameter['tileDrainage'], False)
        self.assertEqual(model_parameter['irrigationOperation'], False)
        self.assertEqual(model_parameter['inletOfDrainingWatershed'], False)
        self.assertEqual(model_parameter['otherParameters'], o_params)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelObjective'], {})
        model_objective = mi_aggr.metadata.metadata_json['modelObjective']
        self.assertEqual(model_objective['BMPs'], True)
        self.assertEqual(model_objective['hydrology'], True)
        self.assertEqual(model_objective['waterQuality'], True)
        self.assertEqual(model_objective['climateLanduseChange'], False)
        self.assertEqual(model_objective['otherObjectives'], o_objs)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelInput'], {})
        model_input = mi_aggr.metadata.metadata_json['modelInput']
        self.assertEqual(model_input['warmupPeriodValue'], 'a')
        self.assertEqual(model_input['rainfallTimeStepType'], 'Daily')
        self.assertEqual(model_input['rainfallTimeStepValue'], 'c')
        self.assertEqual(model_input['routingTimeStepType'], 'Daily')
        self.assertEqual(model_input['routingTimeStepValue'], 'e')
        self.assertEqual(model_input['simulationTimeStepType'], 'Hourly')
        self.assertEqual(model_input['simulationTimeStepValue'], 'g')
        self.assertEqual(model_input['watershedArea'], 'h')
        self.assertEqual(model_input['numberOfSubbasins'], 'i')
        self.assertEqual(model_input['numberOfHRUs'], 'j')
        self.assertEqual(model_input['demResolution'], 'k')
        self.assertEqual(model_input['demSourceName'], 'l')
        self.assertEqual(model_input['demSourceURL'], 'm')
        self.assertEqual(model_input['landUseDataSourceName'], 'n')
        self.assertEqual(model_input['landUseDataSourceURL'], 'o')
        self.assertEqual(model_input['soilDataSourceName'], 'p')
        self.assertEqual(model_input['soilDataSourceURL'], 'q')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['simulationType'], {})
        simulation_type = mi_aggr.metadata.metadata_json['simulationType']
        self.assertEqual(simulation_type, 'Normal Simulation')
        self._validate_meta_with_schema(mi_aggr)

    def test_migrate_swat_specific_metadata_all_metadata_partial(self):
        """
        Here we are testing that we can migrate a swat mi resource that has all swat specific
        metadata with missing sub-fields
        """
        mi_res = self._create_swat_resource()
        mi_res.metadata.create_element('ModelMethod',
                                       runoffCalculationMethod='aaa',
                                       petEstimationMethod='ccc')

        s_params = ["Crop rotation"]
        mi_res.metadata.create_element('ModelParameter',
                                       model_parameters=s_params,
                                       other_parameters='',
                                       )

        o_objs = "some other objective"
        mi_res.metadata.create_element('ModelObjective',
                                       swat_model_objectives=[],
                                       other_objectives=o_objs)

        mi_res.metadata.create_element('ModelInput',
                                       warmupPeriodValue='a',
                                       rainfallTimeStepType='Daily',
                                       rainfallTimeStepValue='c',
                                       routingTimeStepType='Daily',
                                       routingTimeStepValue='e',
                                       simulationTimeStepType='Hourly',
                                       simulationTimeStepValue='',
                                       )

        mi_res.metadata.create_element('SimulationType', simulation_type_name='')

        # check that there exists all the swat model specific metadata
        self.assertNotEqual(mi_res.metadata.model_objective, None)
        self.assertNotEqual(mi_res.metadata.simulation_type, None)
        self.assertNotEqual(mi_res.metadata.model_method, None)
        self.assertNotEqual(mi_res.metadata.model_parameter, None)
        self.assertNotEqual(mi_res.metadata.model_input, None)

        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        # migrate the swat resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check the mi aggregation has meta schema
        self.assertNotEqual(mi_aggr.metadata_schema_json, {})
        # check the json metadata in mi aggregation - there should be swat specific metadata
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelMethod'], {})
        model_method = mi_aggr.metadata.metadata_json['modelMethod']
        self.assertEqual(model_method['runoffCalculationMethod'], 'aaa')
        self.assertNotIn('flowRoutingMethod', model_method)
        self.assertEqual(model_method['petEstimationMethod'], 'ccc')
        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelParameter'], {})
        model_parameter = mi_aggr.metadata.metadata_json['modelParameter']
        self.assertEqual(model_parameter['cropRotation'], True)
        self.assertEqual(model_parameter['tillageOperation'], False)
        self.assertEqual(model_parameter['fertilizer'], False)
        self.assertEqual(model_parameter['pointSource'], False)
        self.assertEqual(model_parameter['tileDrainage'], False)
        self.assertEqual(model_parameter['irrigationOperation'], False)
        self.assertEqual(model_parameter['inletOfDrainingWatershed'], False)
        self.assertNotIn('otherParameters', model_parameter)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelObjective'], {})
        model_objective = mi_aggr.metadata.metadata_json['modelObjective']
        self.assertEqual(model_objective['BMPs'], False)
        self.assertEqual(model_objective['hydrology'], False)
        self.assertEqual(model_objective['waterQuality'], False)
        self.assertEqual(model_objective['climateLanduseChange'], False)
        self.assertEqual(model_objective['otherObjectives'], o_objs)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelInput'], {})
        model_input = mi_aggr.metadata.metadata_json['modelInput']
        self.assertEqual(model_input['warmupPeriodValue'], 'a')
        self.assertEqual(model_input['rainfallTimeStepType'], 'Daily')
        self.assertEqual(model_input['rainfallTimeStepValue'], 'c')
        self.assertEqual(model_input['routingTimeStepType'], 'Daily')
        self.assertEqual(model_input['routingTimeStepValue'], 'e')
        self.assertEqual(model_input['simulationTimeStepType'], 'Hourly')

        self.assertNotIn('simulationTimeStepValue', model_input)
        self.assertNotIn('watershedArea', model_input)
        self.assertNotIn('numberOfSubbasins', model_input)
        self.assertNotIn('numberOfHRUs', model_input)
        self.assertNotIn('demResolution', model_input)
        self.assertNotIn('demSourceName', model_input)
        self.assertNotIn('demSourceURL', model_input)
        self.assertNotIn('landUseDataSourceName', model_input)
        self.assertNotIn('landUseDataSourceURL', model_input)
        self.assertNotIn('soilDataSourceName', model_input)
        self.assertNotIn('soilDataSourceURL', model_input)

        self.assertNotIn('simulationType', mi_aggr.metadata.metadata_json)
        self._validate_meta_with_schema(mi_aggr)

    def test_extended_meta(self):
        """
         Here we are testing that we migrate a swat mi resource, the resource abstract is copied to the extended
         metadata of the newly created mi aggregation with key set to 'description'. Also any resource level
         extended metadata gets moved to the mi aggregation level extended metadata.
        """
        mi_res = self._create_swat_resource()
        abstract = 'This is the abstract of the SWAT Model Instance Resource'
        mi_res.metadata.create_element('description', abstract=abstract)
        mi_res.extra_metadata = {"SWATShareModelID": "dcb9b7a11c286a62b7967f13efa0a85d",
                                 "SWATShareModelLastModifiedTime": "2017-06-14T17:53:34.000000 00:00"}
        mi_res.save()
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        # migrate the swat resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 0)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # test that the converted resource contains one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check the resource abstract is copied to mi aggr extra_metadata
        self.assertEqual(cmp_res.metadata.description.abstract, abstract)
        self.assertEqual(mi_aggr.metadata.extra_metadata['description'], abstract)
        # check that all resource level extended metadata moved to mi aggr extended metadata
        self.assertNotIn('SWATShareModelID', cmp_res.extra_metadata)
        self.assertNotIn('SWATShareModelLastModifiedTime', cmp_res.extra_metadata)
        self.assertEqual(mi_aggr.metadata.extra_metadata['SWATShareModelID'], 'dcb9b7a11c286a62b7967f13efa0a85d')
        self.assertEqual(mi_aggr.metadata.extra_metadata['SWATShareModelLastModifiedTime'],
                         '2017-06-14T17:53:34.000000 00:00')
        self._validate_meta_with_schema(mi_aggr)

    def test_executed_by(self):
        """
        Migrate a mi resource that has a link (executed_by) to a composite resource
        If the linked resource has a mp aggregation, a link to the external mp aggregation is established
        """

        # create a mi resource
        mi_res = self._create_swat_resource()
        self.assertEqual(SWATModelInstanceResource.objects.count(), 1)
        mp_res = self._create_mp_resource()
        self.assertEqual(ModelProgramResource.objects.count(), 1)
        upload_folder = ''
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mp_res, file_to_upload, folder=upload_folder)
        # check mp resource has 2 files
        self.assertEqual(mp_res.files.count(), 1)
        # no files in mi resource
        self.assertEqual(mi_res.files.count(), 0)

        # link the mi res to mp resource
        mi_res.metadata.create_element('executedby', model_name=mp_res.short_id)
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        self.assertNotEqual(mi_res.metadata.executed_by, None)
        self.assertNotEqual(mi_res.metadata.model_output, None)

        # run  prepare migration command for preparing mi resource for migration
        call_command(self.prepare_mi_migration_command)
        # run migration command to migrate mp resource
        call_command(self.mp_migration_command)
        self.assertEqual(CompositeResource.objects.count(), 1)
        self.assertEqual(ModelProgramResource.objects.count(), 0)
        mp_aggr = ModelProgramLogicalFile.objects.first()
        self.assertEqual(mp_aggr.folder, "model-program")

        # run  migration command to migrate mi resource
        call_command(self.mi_migration_command)
        self.assertEqual(SWATModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 2)
        cmp_res = CompositeResource.objects.get(short_id=mi_res.short_id)

        # test that the converted mi resource contains one mi aggregation
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertTrue(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertEqual(cmp_res.extra_data[self.EXECUTED_BY_EXTRA_META_KEY], mp_res.short_id)
        # no files in migrated mi resource
        self.assertEqual(cmp_res.files.count(), 0)
        # there should be only one mi aggregation in the migrated mi resource
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertTrue([lf for lf in cmp_res.logical_files if lf.is_model_instance])
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        self.assertEqual(ModelProgramLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertTrue(mi_aggr.metadata.has_model_output)
        self.assertEqual(mi_aggr.metadata.executed_by, mp_aggr)
        # check the mi aggregation has meta schema
        self.assertNotEqual(mi_aggr.metadata_schema_json, {})
        # check that the linked mp aggregation is part of another resource
        self.assertNotEqual(mi_aggr.resource.short_id, mp_aggr.resource.short_id)
        self.assertEqual(mi_aggr.files.count(), 0)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)

    def _create_swat_resource(self, model_instance_type="SWATModelInstanceResource", add_keywords=False):
        res = hydroshare.create_resource(model_instance_type, self.user,
                                         "Testing migrating to composite resource")
        if add_keywords:
            res.metadata.create_element('subject', value='kw-1')
            res.metadata.create_element('subject', value='kw-2')
        return res

    def _create_mp_resource(self, add_keywords=False):
        mp_res = hydroshare.create_resource("ModelProgramResource", self.user,
                                            "Testing migrating to composite resource")
        if add_keywords:
            mp_res.metadata.create_element('subject', value='kw-1')
            mp_res.metadata.create_element('subject', value='kw-2')
        return mp_res

    def _validate_meta_with_schema(self, mi_aggr):
        try:
            jsonschema.Draft4Validator(mi_aggr.metadata_schema_json).validate(mi_aggr.metadata.metadata_json)
        except jsonschema.ValidationError as err:
            self.fail(msg=str(err))

        try:
            mi_aggr.metadata.get_html()
        except Exception as err:
            traceback.print_exception(*sys.exc_info())
            self.fail(msg=str(err))

        try:
            mi_aggr.metadata.get_html_forms()
        except Exception as err:
            traceback.print_exception(*sys.exc_info())
            self.fail(msg=str(err))
