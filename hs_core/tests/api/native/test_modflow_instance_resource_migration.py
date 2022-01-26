import os
import traceback
import sys
from unittest import TestCase

import jsonschema
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hydroshare import add_file_to_resource
from hs_core.models import ResourceFile
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile
from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource


class TestMODFLOWInstanceResourceMigration(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestMODFLOWInstanceResourceMigration, self).setUp()

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
        self.mi_migration_command = "migrate_modflow_instance_resources"
        self.mp_migration_command = "migrate_model_program_resources"
        self.prepare_mi_migration_command = "prepare_model_instance_resources_for_migration"
        self.MIGRATED_FROM_EXTRA_META_KEY = "MIGRATED_FROM"
        self.MIGRATING_RESOURCE_TYPE = "MODFLOW Instance Resource"
        self.EXECUTED_BY_EXTRA_META_KEY = "EXECUTED_BY_RES_ID"
        self.MI_FOLDER_NAME = "modflow-model-instance"
        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()

    def tearDown(self):
        super(TestMODFLOWInstanceResourceMigration, self).tearDown()
        self.user.delete()
        self.hs_group.delete()
        CompositeResource.objects.all().delete()
        MODFLOWModelInstanceResource.objects.all().delete()
        ModelInstanceResource.objects.all().delete()
        ModelProgramResource.objects.all().delete()

    def test_migrate_no_modflow_specific_metadata(self):
        """
        Here we are testing that we can migrate a modflow mi resource that doesn't have any modflow specific metadata
        """
        mi_res = self._create_modflow_resource()
        # check that there are no model specific metadata
        self.assertEqual(mi_res.metadata.study_area, None)
        self.assertEqual(mi_res.metadata.grid_dimensions, None)
        self.assertEqual(mi_res.metadata.stress_period, None)
        self.assertEqual(mi_res.metadata.ground_water_flow, None)
        self.assertEqual(mi_res.metadata.boundary_condition, None)
        self.assertEqual(mi_res.metadata.model_calibration, None)
        self.assertEqual(list(mi_res.metadata.model_inputs), [])
        self.assertEqual(mi_res.metadata.general_elements, None)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)

        # migrate the modflow resource
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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
        # check the json metadata in mi aggregation - there should not me any modflow specific metadata
        self.assertEqual(mi_aggr.metadata.metadata_json, {})
        json_meta_fields = ['studyArea', 'gridDimensions', 'groundwaterFlow', 'modelCalibration', 'stressPeriod',
                            'modelInputs', 'modelParameter', 'modelSolver', 'subsidencePackage',
                            'headDependentFluxBoundaryPackages', 'outputControlPackage',
                            'specifiedFluxBoundaryPackages', 'specifiedHeadBoundaryPackages']
        for meta_field in json_meta_fields:
            self.assertTrue(meta_field not in mi_aggr.metadata.metadata_json)

    def test_migrate_modflow_specific_metadata_only_studyArea(self):
        """
        Here we are testing that we can migrate a modflow mi resource that has only one modflow specific
        metadata 'study area'
        """
        mi_res = self._create_modflow_resource()
        mi_res.metadata.create_element('StudyArea',
                                       totalLength='10',
                                       totalWidth='20',
                                       maximumElevation='100',
                                       minimumElevation='5')

        # check that there are no model specific metadata
        self.assertNotEqual(mi_res.metadata.study_area, None)
        self.assertEqual(mi_res.metadata.grid_dimensions, None)
        self.assertEqual(mi_res.metadata.stress_period, None)
        self.assertEqual(mi_res.metadata.ground_water_flow, None)
        self.assertEqual(mi_res.metadata.boundary_condition, None)
        self.assertEqual(mi_res.metadata.model_calibration, None)
        self.assertEqual(list(mi_res.metadata.model_inputs), [])
        self.assertEqual(mi_res.metadata.general_elements, None)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        # migrate the modflow resource
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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

        # check the json metadata in mi aggregation
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['studyArea'], {})
        study_area = mi_aggr.metadata.metadata_json['studyArea']
        self.assertEqual(study_area['totalWidth'], '20')
        self.assertEqual(study_area['totalLength'], '10')
        self.assertEqual(study_area['maximumElevation'], '100')
        self.assertEqual(study_area['minimumElevation'], '5')
        # no other metadata should be part of the JSON metadata
        json_meta_fields = ['gridDimensions', 'groundwaterFlow', 'modelCalibration', 'stressPeriod',
                            'modelInputs', 'modelParameter', 'modelSolver', 'subsidencePackage',
                            'headDependentFluxBoundaryPackages', 'outputControlPackage',
                            'specifiedFluxBoundaryPackages', 'specifiedHeadBoundaryPackages']
        for meta_field in json_meta_fields:
            self.assertTrue(meta_field not in mi_aggr.metadata.metadata_json)

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

    def test_migrate_modflow_specific_metadata_all_metadata(self):
        """
        Here we are testing that we can migrate a modflow mi resource that has all modflow specific
        metadata
        """
        mi_res = self._create_modflow_resource()
        mi_res.metadata.create_element('StudyArea',
                                       totalLength='10',
                                       totalWidth='20',
                                       maximumElevation='100',
                                       minimumElevation='5')

        mi_res.metadata.create_element('StressPeriod',
                                       stressPeriodType='Steady',
                                       steadyStateValue='a',
                                       transientStateValueType='Daily',
                                       transientStateValue='10')

        mi_res.metadata.create_element('GridDimensions',
                                       numberOfLayers='10',
                                       typeOfRows='Regular',
                                       numberOfRows=20,
                                       typeOfColumns='Irregular',
                                       numberOfColumns='50')

        mi_res.metadata.create_element('GroundWaterFlow',
                                       flowPackage='BCF6',
                                       flowParameter='Transmissivity',
                                       unsaturatedZonePackage=True,
                                       seawaterIntrusionPackage=False,
                                       horizontalFlowBarrierPackage=True)

        ot_ctl_pkgs = ['LMT6', 'OC']
        mi_res.metadata.create_element('GeneralElements',
                                       modelParameter='BCF6',
                                       modelSolver='DE4',
                                       output_control_package=ot_ctl_pkgs,
                                       subsidencePackage='SUB')

        spec_hd_bd_pkgs = ['CHD', 'FHB']
        spec_fx_bd_pkgs = ['RCH', 'WEL']
        hd_dep_fx_pkgs = ['MNW2', 'GHB', 'LAK']
        mi_res.metadata.create_element('BoundaryCondition',
                                       specified_head_boundary_packages=spec_hd_bd_pkgs,
                                       specified_flux_boundary_packages=spec_fx_bd_pkgs,
                                       head_dependent_flux_boundary_packages=hd_dep_fx_pkgs,
                                       other_specified_head_boundary_packages='JMS',
                                       other_specified_flux_boundary_packages='MMM',
                                       other_head_dependent_flux_boundary_packages='JLG')

        mi_res.metadata.create_element('ModelCalibration',
                                       calibratedParameter='a',
                                       observationType='b',
                                       observationProcessPackage='RVOB',
                                       calibrationMethod='c')

        mi_res.metadata.create_element('ModelInput',
                                       inputType='aa',
                                       inputSourceName='aaa',
                                       inputSourceURL='http://www.RVOB1.com')

        # 8b. create another modelinput
        mi_res.metadata.create_element('ModelInput',
                                       inputType='bb',
                                       inputSourceName='bbb',
                                       inputSourceURL='http://www.RVOB2.com')

        # check that there are all model specific metadata
        self.assertNotEqual(mi_res.metadata.study_area, None)
        self.assertNotEqual(mi_res.metadata.grid_dimensions, None)
        self.assertNotEqual(mi_res.metadata.stress_period, None)
        self.assertNotEqual(mi_res.metadata.ground_water_flow, None)
        self.assertNotEqual(mi_res.metadata.boundary_condition, None)
        self.assertNotEqual(mi_res.metadata.model_calibration, None)
        self.assertNotEqual(list(mi_res.metadata.model_inputs), [])
        self.assertNotEqual(mi_res.metadata.general_elements, None)

        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        # migrate the modflow resource
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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

        # check the json metadata in mi aggregation
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['studyArea'], {})
        study_area = mi_aggr.metadata.metadata_json['studyArea']
        self.assertEqual(study_area['totalWidth'], '20')
        self.assertEqual(study_area['totalLength'], '10')
        self.assertEqual(study_area['maximumElevation'], '100')
        self.assertEqual(study_area['minimumElevation'], '5')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['stressPeriod'], {})
        stress_period = mi_aggr.metadata.metadata_json['stressPeriod']
        self.assertEqual(stress_period['type'], 'Steady')
        self.assertEqual(stress_period['lengthOfSteadyStateStressPeriod'], 'a')
        self.assertEqual(stress_period['typeOfTransientStateStressPeriod'], 'Daily')
        self.assertEqual(stress_period['lengthOfTransientStateStressPeriod'], '10')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['gridDimensions'], {})
        grid_dimensions = mi_aggr.metadata.metadata_json['gridDimensions']
        self.assertEqual(grid_dimensions['numberOfLayers'], '10')
        self.assertEqual(grid_dimensions['typeOfRows'], 'Regular')
        self.assertEqual(grid_dimensions['numberOfRows'], '20')
        self.assertEqual(grid_dimensions['typeOfColumns'], 'Irregular')
        self.assertEqual(grid_dimensions['numberOfColumns'], '50')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['groundwaterFlow'], {})
        ground_water_flow = mi_aggr.metadata.metadata_json['groundwaterFlow']
        self.assertEqual(ground_water_flow['flowPackage'], 'BCF6')
        self.assertEqual(ground_water_flow['flowParameter'], 'Transmissivity')
        self.assertTrue(ground_water_flow['unsaturatedZonePackage'])
        self.assertFalse(ground_water_flow['seawaterIntrusionPackage'])
        self.assertTrue(ground_water_flow['horizontalFlowBarrierPackage'])

        self.assertEqual(mi_aggr.metadata.metadata_json['modelSolver'], 'DE4')
        self.assertEqual(mi_aggr.metadata.metadata_json['modelParameter'], 'BCF6')
        self.assertEqual(mi_aggr.metadata.metadata_json['subsidencePackage'], 'SUB')

        for key in mi_aggr.metadata.metadata_json['outputControlPackage']:
            if key in ['LMT6', 'OC']:
                self.assertTrue(mi_aggr.metadata.metadata_json['outputControlPackage'][key])
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['outputControlPackage'][key])

        for key in mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages']:
            if key in spec_hd_bd_pkgs:
                self.assertTrue(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key])
            elif key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key], 'JMS')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages']:
            if key in spec_fx_bd_pkgs:
                self.assertTrue(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key])
            elif key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key], 'MMM')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages']:
            if key in hd_dep_fx_pkgs:
                self.assertTrue(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'][key])
            elif key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'][key], 'JLG')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'][key])

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelCalibration'], {})
        model_calibration = mi_aggr.metadata.metadata_json['modelCalibration']
        self.assertEqual(model_calibration['observationType'], 'b')
        self.assertEqual(model_calibration['calibrationMethod'], 'c')
        self.assertEqual(model_calibration['calibratedParameter'], 'a')
        self.assertEqual(model_calibration['observationProcessPackage'], 'RVOB')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelInputs'], [])
        for mi_item in mi_aggr.metadata.metadata_json['modelInputs']:
            self.assertIn(mi_item['inputType'], ['aa', 'bb'])
            self.assertIn(mi_item['inputSourceName'], ['aaa', 'bbb'])
            self.assertIn(mi_item['inputSourceURL'], ['http://www.RVOB1.com', 'http://www.RVOB2.com'])

        mi_item_1, mi_item_2 = mi_aggr.metadata.metadata_json['modelInputs']
        self.assertNotEqual(mi_item_1['inputType'], mi_item_2['inputType'])
        self.assertNotEqual(mi_item_1['inputSourceName'], mi_item_2['inputSourceName'])
        self.assertNotEqual(mi_item_1['inputSourceURL'], mi_item_2['inputSourceURL'])

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

    def test_migrate_modflow_specific_metadata_all_metadata_partial(self):
        """
        Here we are testing that we can migrate a modflow mi resource that has all modflow specific
        metadata with missing sub-fields
        """
        mi_res = self._create_modflow_resource()
        mi_res.metadata.create_element('StudyArea',
                                       totalLength='10',
                                       totalWidth=' '
                                       )

        mi_res.metadata.create_element('StressPeriod',
                                       stressPeriodType='Steady',
                                       steadyStateValue='a',
                                       )

        mi_res.metadata.create_element('GridDimensions',
                                       numberOfLayers='10',
                                       typeOfRows='Regular',
                                       typeOfColumns='',
                                       numberOfRows=''
                                       )

        mi_res.metadata.create_element('GroundWaterFlow',
                                       flowPackage='BCF6',
                                       flowParameter='Transmissivity',
                                       unsaturatedZonePackage=True
                                       )

        mi_res.metadata.create_element('GeneralElements',
                                       modelParameter='BCF6',
                                       modelSolver='DE4',
                                       output_control_package=[]
                                       )

        spec_hd_bd_pkgs = ['CHD', 'FHB']
        mi_res.metadata.create_element('BoundaryCondition',
                                       specified_head_boundary_packages=spec_hd_bd_pkgs,
                                       other_specified_head_boundary_packages='JMS',
                                       other_specified_flux_boundary_packages='MMM',
                                       specified_flux_boundary_packages=[]
                                       )

        mi_res.metadata.create_element('ModelCalibration',
                                       calibratedParameter='a',
                                       observationType='b',
                                       calibrationMethod='',
                                       observationProcessPackage='ADV2'
                                       )

        # create multiple modelinput meta elements
        mi_res.metadata.create_element('ModelInput',
                                       inputType='aa',
                                       inputSourceName='aaa'
                                       )

        mi_res.metadata.create_element('ModelInput',
                                       inputType='bb',
                                       inputSourceName='bbb',
                                       inputSourceURL=' '
                                       )

        mi_res.metadata.create_element('ModelInput',
                                       inputType='cc',
                                       inputSourceName='ccc',
                                       inputSourceURL='http://www.RVOB2.com')

        # check that there are all model specific metadata
        self.assertNotEqual(mi_res.metadata.study_area, None)
        self.assertNotEqual(mi_res.metadata.grid_dimensions, None)
        self.assertNotEqual(mi_res.metadata.stress_period, None)
        self.assertNotEqual(mi_res.metadata.ground_water_flow, None)
        self.assertNotEqual(mi_res.metadata.boundary_condition, None)
        self.assertNotEqual(mi_res.metadata.model_calibration, None)
        self.assertNotEqual(list(mi_res.metadata.model_inputs), [])
        self.assertNotEqual(mi_res.metadata.general_elements, None)

        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        # migrate the modflow resource
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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

        # check the json metadata in mi aggregation
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['studyArea'], {})
        study_area = mi_aggr.metadata.metadata_json['studyArea']
        self.assertNotIn('totalWidth', study_area)
        self.assertEqual(study_area['totalLength'], '10')
        self.assertNotIn('maximumElevation', study_area)
        self.assertNotIn('minimumElevation', study_area)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['stressPeriod'], {})
        stress_period = mi_aggr.metadata.metadata_json['stressPeriod']
        self.assertEqual(stress_period['type'], 'Steady')
        self.assertEqual(stress_period['lengthOfSteadyStateStressPeriod'], 'a')
        self.assertNotIn('typeOfTransientStateStressPeriod', stress_period)
        self.assertNotIn('lengthOfTransientStateStressPeriod', stress_period)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['gridDimensions'], {})
        grid_dimensions = mi_aggr.metadata.metadata_json['gridDimensions']
        self.assertEqual(grid_dimensions['numberOfLayers'], '10')
        self.assertEqual(grid_dimensions['typeOfRows'], 'Regular')
        self.assertNotIn('numberOfRows', grid_dimensions)
        self.assertNotIn('typeOfColumns', grid_dimensions)
        self.assertNotIn('numberOfColumns', grid_dimensions)

        self.assertNotEqual(mi_aggr.metadata.metadata_json['groundwaterFlow'], {})
        ground_water_flow = mi_aggr.metadata.metadata_json['groundwaterFlow']
        self.assertEqual(ground_water_flow['flowPackage'], 'BCF6')
        self.assertEqual(ground_water_flow['flowParameter'], 'Transmissivity')
        self.assertTrue(ground_water_flow['unsaturatedZonePackage'])
        self.assertFalse(ground_water_flow['seawaterIntrusionPackage'])
        self.assertFalse(ground_water_flow['horizontalFlowBarrierPackage'])

        self.assertEqual(mi_aggr.metadata.metadata_json['modelSolver'], 'DE4')
        self.assertEqual(mi_aggr.metadata.metadata_json['modelParameter'], 'BCF6')
        self.assertNotIn('subsidencePackage', mi_aggr.metadata.metadata_json)

        self.assertNotIn('outputControlPackage', mi_aggr.metadata.metadata_json)
        for key in mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages']:
            if key in spec_hd_bd_pkgs:
                self.assertTrue(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key])
            elif key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key], 'JMS')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages']:
            if key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key], 'MMM')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages']:
            self.assertFalse(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'][key])

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelCalibration'], {})
        model_calibration = mi_aggr.metadata.metadata_json['modelCalibration']
        self.assertEqual(model_calibration['observationType'], 'b')
        self.assertNotIn('calibrationMethod', model_calibration)
        self.assertEqual(model_calibration['calibratedParameter'], 'a')
        self.assertEqual(model_calibration['observationProcessPackage'], 'ADV2')

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelInputs'], [])
        for mi_item in mi_aggr.metadata.metadata_json['modelInputs']:
            self.assertIn(mi_item['inputType'], ['aa', 'bb', 'cc'])
            self.assertIn(mi_item['inputSourceName'], ['aaa', 'bbb', 'ccc'])
            if 'inputSourceURL' in mi_item:
                self.assertIn(mi_item['inputSourceURL'], ['http://www.RVOB2.com'])

        input_types = set([mi_item['inputType'] for mi_item in mi_aggr.metadata.metadata_json['modelInputs']])
        self.assertEqual(len(input_types), 3)
        input_src_names = set([mi_item['inputSourceName'] for mi_item in mi_aggr.metadata.metadata_json['modelInputs']])
        self.assertEqual(len(input_src_names), 3)
        input_src_urls = set([mi_item['inputSourceURL'] for mi_item in
                              mi_aggr.metadata.metadata_json['modelInputs'] if 'inputSourceURL' in mi_item])
        self.assertEqual(len(input_src_urls), 1)

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

    def test_migrate_modflow_specific_metadata_all_metadata_with_default(self):
        """
        Here we are testing that we can migrate a modflow mi resource that has all modflow specific
        metadata with only default values for sub-fields
        """
        mi_res = self._create_modflow_resource()
        mi_res.metadata.create_element('StudyArea')

        mi_res.metadata.create_element('StressPeriod')

        mi_res.metadata.create_element('GridDimensions')

        mi_res.metadata.create_element('GroundWaterFlow')

        mi_res.metadata.create_element('GeneralElements')

        mi_res.metadata.create_element('BoundaryCondition')

        mi_res.metadata.create_element('ModelCalibration')

        # create multiple modelinput meta elements
        mi_res.metadata.create_element('ModelInput')

        mi_res.metadata.create_element('ModelInput',
                                       inputType='bb',
                                       inputSourceName='bbb',
                                       inputSourceURL=' '
                                       )

        mi_res.metadata.create_element('ModelInput',
                                       inputType='cc',
                                       inputSourceName='ccc',
                                       inputSourceURL='http://www.RVOB2.com')

        # check that there are all model specific metadata
        self.assertNotEqual(mi_res.metadata.study_area, None)
        self.assertNotEqual(mi_res.metadata.grid_dimensions, None)
        self.assertNotEqual(mi_res.metadata.stress_period, None)
        self.assertNotEqual(mi_res.metadata.ground_water_flow, None)
        self.assertNotEqual(mi_res.metadata.boundary_condition, None)
        self.assertNotEqual(mi_res.metadata.model_calibration, None)
        self.assertNotEqual(list(mi_res.metadata.model_inputs), [])
        self.assertNotEqual(mi_res.metadata.general_elements, None)

        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        # migrate the modflow resource
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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

        # check the json metadata in mi aggregation
        self.assertNotEqual(mi_aggr.metadata.metadata_json, {})
        self.assertEqual(mi_aggr.metadata.metadata_json['studyArea'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['stressPeriod'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['gridDimensions'], {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['groundwaterFlow'], {})

        self.assertNotIn('modelSolver', mi_aggr.metadata.metadata_json)
        self.assertNotIn('modelParameter', mi_aggr.metadata.metadata_json)
        self.assertNotIn('subsidencePackage', mi_aggr.metadata.metadata_json)
        self.assertNotIn('outputControlPackage', mi_aggr.metadata.metadata_json)
        self.assertIn('specifiedHeadBoundaryPackages', mi_aggr.metadata.metadata_json)
        self.assertIn('specifiedFluxBoundaryPackages', mi_aggr.metadata.metadata_json)
        self.assertIn('headDependentFluxBoundaryPackages', mi_aggr.metadata.metadata_json)

        for key in mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages']:
            if key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key], '')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages']:
            if key == 'otherPackages':
                self.assertEqual(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key], '')
            else:
                self.assertFalse(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'][key])

        for key in mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages']:
            self.assertFalse(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'][key])

        self.assertEqual(mi_aggr.metadata.metadata_json['modelCalibration'], {})

        self.assertNotEqual(mi_aggr.metadata.metadata_json['modelInputs'], [])
        for mi_item in mi_aggr.metadata.metadata_json['modelInputs']:
            if 'inputType' in mi_item:
                self.assertIn(mi_item['inputType'], ['bb', 'cc'])
            if 'inputSourceName' in mi_item:
                self.assertIn(mi_item['inputSourceName'], ['bbb', 'ccc'])
            if 'inputSourceURL' in mi_item:
                self.assertIn(mi_item['inputSourceURL'], ['http://www.RVOB2.com'])

        input_types = set([mi_item['inputType'] for mi_item in mi_aggr.metadata.metadata_json['modelInputs']
                           if 'inputType' in mi_item])
        self.assertEqual(len(input_types), 2)
        input_src_names = set([mi_item['inputSourceName'] for mi_item in mi_aggr.metadata.metadata_json['modelInputs']
                               if 'inputSourceName' in mi_item])
        self.assertEqual(len(input_src_names), 2)
        input_src_urls = set([mi_item['inputSourceURL'] for mi_item in
                              mi_aggr.metadata.metadata_json['modelInputs'] if 'inputSourceURL' in mi_item])
        self.assertEqual(len(input_src_urls), 1)

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

    def test_executed_by(self):
        """
        Migrate a mi resource that has a link (executed_by) to a composite resource
        If the linked resource has a mp aggregation, a link to the external mp aggregation is established
        """

        # create a mi resource
        mi_res = self._create_modflow_resource()
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
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
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
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

    def test_migrate_modflow_resource_with_file_1(self):
        """
        Migrate a modflow mi resource that has only one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to modflow mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_file_2(self):
        """
        Migrate a modflow mi resource that has more than one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=False)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        self.assertEqual(mi_res.files.count(), 2)
        # run  migration command
        call_command(self.mi_migration_command)

        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        self.assertEqual(cmp_res.files.count(), 2)
        for res_file in cmp_res.files.all():
            self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertFalse(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_file_3(self):
        """
        Migrate a modflow mi resource that has a readme file only and no mi specific metadata
        A folder based mi aggregation is created in the migrated composite resource
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource()
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # upload a file to modflow mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource does not contain any aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        # check the readme file was not moved to folder
        res_file = cmp_res.files.first()
        self.assertEqual(res_file.file_folder, "")
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should be one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_4(self):
        """
        Migrate a modflow mi resource that has a readme file and 2 other files, and has mi specific metadata
        When converted to composite resource, it should have a mi aggregation (based on folder)
        and should have aggregation level metadata
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource()
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 2nd file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)

        # upload a 3rd file to mi resource
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 3)

        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 3)
        # check resource files folder
        for res_file in cmp_res.files.all():
            if res_file.file_name != "readme.txt":
                self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")

        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_folder_1(self):
        """
        Migrate a modflow mi resource that has only one file in one folder
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original folder is moved into the aggregation folder.
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to modflow mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_folder_2(self):
        """
        Migrate a modflow mi resource that has 2 folders - each containing one file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Both folders should be moved into the
        new aggregation folder.
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_2)
        self.assertEqual(mi_res.files.count(), 2)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        expected_file_folders = ["{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1),
                                 "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_2)]
        for res_file in cmp_res.files.all():
            self.assertIn(res_file.file_folder, expected_file_folders)

        res_file_1 = cmp_res.files.all()[0]
        res_file_2 = cmp_res.files.all()[1]
        self.assertNotEqual(res_file_1.file_folder, res_file_2.file_folder)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 2)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_folder_3(self):
        """
        Migrate a modflow mi resource that has 2 folders - one folder is empty and the other one has a file
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Only ehe folder containing a file will be be moved into the
        new aggregation folder.
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'folder-1'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        upload_folder_2 = 'folder-2'
        ResourceFile.create_folder(mi_res, upload_folder_2)

        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        res_file = cmp_res.files.first()
        expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_folder_4(self):
        """
        Migrate a modflow mi resource that has 3 folders - one folder contains a file the other one is a nested folder (both
        parent and child each has a file)
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original 3 folders will be moved into the
        new aggregation folder.
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource 'data' folder
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder_1 = 'data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_1)
        # upload a file to mi resource 'contents' folder
        file_path = 'hs_core/tests/data/cea.tif'
        upload_folder_2 = 'contents'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_2)

        # upload a file to mi resource 'contents/data' folder
        file_path = 'hs_core/tests/data/netcdf_valid.nc'
        upload_folder_3 = 'contents/data'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder_3)
        self.assertEqual(mi_res.files.count(), 3)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 3)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check the res files moved to the mi aggregation folder
        # check the folder for each of the files in composite resource
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'test.txt':
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_1)
            elif res_file.file_name == 'cea.tif':
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_2)
            else:
                expected_file_folder = "{}/{}".format(self.MI_FOLDER_NAME, upload_folder_3)

            self.assertEqual(res_file.file_folder, expected_file_folder)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 3)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_with_folder_5(self):
        """
        Migrate a modflow mi resource that has only one file in a folder. The folder name is 'model-instance'
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. The original folder will be moved into the new aggregation folder.
        The newly created aggregation folder name should be 'model-instance-1'
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create modflow model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a file to mi resource
        file_path = 'hs_core/tests/data/test.txt'
        upload_folder = self.MI_FOLDER_NAME
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))

        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 1)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)
        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)
        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.files.count(), 1)
        expected_aggr_folder_name = "{}-1".format(self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.folder, expected_aggr_folder_name)
        self.assertEqual(mi_aggr.aggregation_name, expected_aggr_folder_name)
        res_file = cmp_res.files.first()
        expected_file_folder = "{}-1/{}".format(self.MI_FOLDER_NAME, upload_folder)
        self.assertEqual(res_file.file_folder, expected_file_folder)

        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def test_migrate_modflow_resource_missing_file_in_irods(self):
        """
        Migrate a modflow mi resource that has 2 files in db but only one file in iRODS
        When converted to composite resource, it should have a mi aggregation (based on the folder)
        and should have aggregation level metadata. Only the resource file that is in iRODS will be part of the
        mi aggregation.
        """

        # create a modflow mi resource
        mi_res = self._create_modflow_resource(add_keywords=True)
        self.assertTrue(mi_res.metadata.subjects)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 1)
        self.assertEqual(CompositeResource.objects.count(), 0)
        # create Model instance metadata
        mi_res.metadata.create_element('modeloutput', includes_output=True)
        # upload a readme file to mi resource
        file_path = 'hs_core/tests/data/readme.txt'
        upload_folder = ''
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 1)
        text_res_file = mi_res.files.first()

        # upload a file to mi resource
        file_path = 'hs_core/tests/data/cea.tif'
        file_to_upload = UploadedFile(file=open(file_path, 'rb'),
                                      name=os.path.basename(file_path))
        add_file_to_resource(mi_res, file_to_upload, folder=upload_folder)
        self.assertEqual(mi_res.files.count(), 2)
        # delete the text file from iRODS
        istorage = mi_res.get_irods_storage()
        istorage.delete(text_res_file.public_path)
        # as pre the DB the Mi resource still have 2 files
        self.assertEqual(mi_res.files.count(), 2)

        # run  migration command
        call_command(self.mi_migration_command)
        self.assertEqual(MODFLOWModelInstanceResource.objects.count(), 0)
        self.assertEqual(CompositeResource.objects.count(), 1)
        # test that the converted resource contains one mi aggregations
        cmp_res = CompositeResource.objects.first()
        self.assertEqual(cmp_res.files.count(), 2)
        self.assertEqual(mi_res.short_id, cmp_res.short_id)
        # check the res file moved to the mi aggregation folder
        for res_file in cmp_res.files.all():
            if res_file.file_name == 'cea.tif':
                self.assertEqual(res_file.file_folder, self.MI_FOLDER_NAME)
            else:
                self.assertEqual(res_file.file_folder, "")

        self.assertFalse(self.EXECUTED_BY_EXTRA_META_KEY in cmp_res.extra_data)
        self.assertEqual(cmp_res.extra_metadata[self.MIGRATED_FROM_EXTRA_META_KEY], self.MIGRATING_RESOURCE_TYPE)
        self.assertTrue(cmp_res.metadata.subjects)

        # there should one mi aggregation
        self.assertEqual(len(list(cmp_res.logical_files)), 1)
        self.assertEqual(ModelInstanceLogicalFile.objects.count(), 1)

        # check mi aggregation is folder based
        mi_aggr = ModelInstanceLogicalFile.objects.first()
        self.assertEqual(mi_aggr.folder, self.MI_FOLDER_NAME)
        self.assertEqual(mi_aggr.files.count(), 1)
        self.assertTrue(mi_aggr.metadata.has_model_output)
        # check that the resource level keywords copied to the mi aggregation
        self.assertTrue(mi_aggr.metadata.keywords)
        self.assertEqual(len(mi_aggr.metadata.keywords), cmp_res.metadata.subjects.count())
        # check that mi_aggr metadata is set to dirty
        self.assertTrue(mi_aggr.metadata.is_dirty)

    def _create_modflow_resource(self, model_instance_type="MODFLOWModelInstanceResource", add_keywords=False):
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
