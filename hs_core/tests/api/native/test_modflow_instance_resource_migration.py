import os
from unittest import TestCase, skip

import json
import jsonschema
from rest_framework.renderers import JSONRenderer
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from django.core.management import call_command

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.management.utils import get_modflow_meta_schema
from hs_core.hydroshare import add_file_to_resource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_file_types.models import ModelInstanceLogicalFile, ModelProgramLogicalFile
from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceResource
from hs_modflow_modelinstance.serializers import MODFLOWModelInstanceMetaDataSerializerMigration
from hs_swat_modelinstance.models import SWATModelInstanceResource
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
        self.MI_FOLDER_NAME = "modflow-instance"
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

    @skip("Not testing at this time")
    def test_generation_of_meta_in_json(self):

        mi_res = self._create_modflow_resource()
        # add modflow specific metadata
        # 1. create stressperiod (this will match with one schema attribute)
        mi_res.metadata.create_element('StressPeriod',
                                       stressPeriodType='Steady',
                                       steadyStateValue='a',
                                       transientStateValueType='Daily',
                                       transientStateValue='b')

        # 2. create StudyArea (this will match with one schema attribute)
        mi_res.metadata.create_element('StudyArea',
                                       totalLength='10',
                                       totalWidth='20',
                                       maximumElevation='100',
                                       minimumElevation='5')

        # 3. create griddimensions (this will match with one schema attribute)
        mi_res.metadata.create_element('GridDimensions',
                                       numberOfLayers='a',
                                       typeOfRows='Regular',
                                       numberOfRows='c',
                                       typeOfColumns='Irregular',
                                       numberOfColumns='e')

        # 4. create groundwaterflow (this will match with one schema attribute)
        mi_res.metadata.create_element('GroundWaterFlow',
                                       flowPackage='BCF6',
                                       flowParameter='Transmissivity')

        # 5. create generic elements (this will match with 4 schema attributes)
        ot_ctl_pkgs = ['LMT6', 'OC']
        mi_res.metadata.create_element('GeneralElements',
                                       modelParameter='BCF6',
                                       modelSolver='DE4',
                                       output_control_package=ot_ctl_pkgs,
                                       subsidencePackage='SUB')

        # 6. create boundary condition meta element (this will match with 3 schema attributes)
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

        # 7. create modelcalibration meta element (this will match with one schema attribute)
        mi_res.metadata.create_element('ModelCalibration',
                                       calibratedParameter='a',
                                       observationType='b',
                                       observationProcessPackage='RVOB',
                                       calibrationMethod='c')

        # 8a. create ModelInput meta element (no matching schema attribute in modflow schema template)
        mi_res.metadata.create_element('ModelInput',
                                       inputType='a',
                                       inputSourceName='b',
                                       inputSourceURL='http://www.RVOB.com')

        # 8b. create another modelinput
        mi_res.metadata.create_element('ModelInput',
                                       inputType='aa',
                                       inputSourceName='bd',
                                       inputSourceURL='http://www.RVOBs.com')

        serializer = MODFLOWModelInstanceMetaDataSerializerMigration(mi_res.metadata)

        meta_json = JSONRenderer().render(serializer.data)
        print(meta_json)
        print("\n")
        data = serializer.data
        data['studyArea'] = data.pop('study_area', None)
        if data['studyArea'] is None:
            data['studyArea'] = {}

        data['modelCalibration'] = data.pop('model_calibration', None)
        if data['modelCalibration'] is None:
            data['modelCalibration'] = {}

        data['groundwaterFlow'] = data.pop('ground_water_flow', None)
        if data['groundwaterFlow'] is None:
            data['groundwaterFlow'] = {}

        data['gridDimensions'] = data.pop('grid_dimensions', None)
        if data['gridDimensions'] is None:
            data['gridDimensions'] = {}

        # TODO: modelInput is currently not part of the MODFLOW json schema
        data['modelInput'] = data.pop('model_inputs', None)
        if data['modelInput'] is None:
            data['modelInput'] = []
        # TODO: stressPeriod attribute in the schema needs to be adjusted to take string values for some of the
        #  properties of this field
        data['stressPeriod'] = data.pop('stress_period', None)
        if data['stressPeriod'] is None:
            data['stressPeriod'] = {}
        general_elements = data.pop('general_elements', None)
        if general_elements is None:
            general_elements = {}
        if general_elements:
            data['modelSolver'] = general_elements['modelSolver']
            data['modelParameter'] = general_elements['modelParameter']
            data['subsidencePackage'] = general_elements['subsidencePackage']
        else:
            data['modelSolver'] = None
            data['modelParameter'] = ""
            data['subsidencePackage'] = None

        if data['stressPeriod']:
            for key in list(data['stressPeriod']):
                new_key = ""
                if key == 'stressPeriodType':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'type'
                elif key == 'steadyStateValue':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'lengthOfSteadyStateStressPeriod'
                elif key == 'transientStateValueType':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'typeOfTransientStateStressPeriod'
                elif key == 'transientStateValue':
                    v = data['stressPeriod'].pop(key)
                    new_key = 'lengthOfTransientStateStressPeriod'
                if new_key:
                    data['stressPeriod'][new_key] = v

        data['outputControlPackage'] = {'OC': False, 'HYD': False, 'GAGE': False, 'LMT6': False, 'MNWI': False}
        if general_elements:
            output_control_pkg = general_elements['output_control_package']
            if output_control_pkg:
                for key in data['outputControlPackage']:
                    for pkg in output_control_pkg:
                        if pkg['description'] == key:
                            data['outputControlPackage'][key] = True
                            break

        print('general_elements:\n')
        print(general_elements)
        print("\n")
        boundary_condition = data.pop('boundary_condition', None)
        if boundary_condition is None:
            boundary_condition = {}
        data['specifiedHeadBoundaryPackages'] = {"BFH": False, "CHD": False, "FHB": False, "otherPackages": ""}
        data['specifiedFluxBoundaryPackages'] = {"RCH": False, "WEL": False, "FHB": False, "otherPackages": ""}
        data['headDependentFluxBoundaryPackages'] = {"DAF": False, "DRN": False, "DRT": False,
                                                     "ETS": False, "EVT": False, "GHB": False,
                                                     "LAK": False, "RES": False, "RIP": False,
                                                     "RIV": False, "SFR": False, "STR": False,
                                                     "UZF": False, "DAFG": False, "MNW1": False,
                                                     "MNW2": False, "otherPackages": ""}
        if boundary_condition:
            for key in data['specifiedHeadBoundaryPackages']:
                for pkg in boundary_condition['specified_head_boundary_packages']:
                    if pkg['description'] == key:
                        data['specifiedHeadBoundaryPackages'][key] = True
                        break

            if boundary_condition['other_specified_head_boundary_packages']:
                data['specifiedHeadBoundaryPackages']["otherPackages"] = boundary_condition['other_specified_head_boundary_packages']

            for key in data['specifiedFluxBoundaryPackages']:
                for pkg in boundary_condition['specified_flux_boundary_packages']:
                    if pkg['description'] == key:
                        data['specifiedFluxBoundaryPackages'][key] = True
                        break

            if boundary_condition['other_specified_flux_boundary_packages']:
                data['specifiedFluxBoundaryPackages']["otherPackages"] = boundary_condition['other_specified_flux_boundary_packages']

            for key in data['headDependentFluxBoundaryPackages']:
                for pkg in boundary_condition['head_dependent_flux_boundary_packages']:
                    if pkg['description'] == key:
                        data['headDependentFluxBoundaryPackages'][key] = True
                        break
            if boundary_condition['other_head_dependent_flux_boundary_packages']:
                data['headDependentFluxBoundaryPackages']["otherPackages"] = boundary_condition['other_head_dependent_flux_boundary_packages']

        meta_json = json.dumps(data, indent=4)
        print(meta_json)
        meta_json_schema = json.loads(get_modflow_meta_schema())
        # print("MODFLOW Meta Schema:\n")
        # print(json_schema)
        try:
            jsonschema.Draft4Validator(meta_json_schema).validate(data)
        except jsonschema.ValidationError as err:
            print("Meta schema validation error:\n")
            print(err)
            # print(err.absolute_schema_path)
            # print(str(err.message))
            # print("path:\n")
            # str(err.schema_path)

        # self.assertEqual(1, 2)

    def test_migrate_no_modflow_specific_metadata(self):
        """
        Here we are testing that we can migrate a modflow mi resource that doesn't have any modflow specific metadata
        """
        mi_res = self._create_modflow_resource()
        self.maxDiff = None
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
        # check the json metadata in mi aggregation
        self.assertEqual(mi_aggr.metadata.metadata_json['studyArea'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['gridDimensions'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['groundwaterFlow'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['modelCalibration'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['stressPeriod'], {})
        self.assertEqual(mi_aggr.metadata.metadata_json['modelInputs'], [])
        self.assertEqual(mi_aggr.metadata.metadata_json['modelParameter'], "")
        self.assertEqual(mi_aggr.metadata.metadata_json['modelSolver'], None)
        self.assertEqual(mi_aggr.metadata.metadata_json['subsidencePackage'], None)
        self.assertNotEqual(mi_aggr.metadata.metadata_json['headDependentFluxBoundaryPackages'], {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['outputControlPackage'], {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['specifiedFluxBoundaryPackages'], {})
        self.assertNotEqual(mi_aggr.metadata.metadata_json['specifiedHeadBoundaryPackages'], {})

    def _create_modflow_resource(self, model_instance_type="MODFLOWModelInstanceResource", add_keywords=False):
        res = hydroshare.create_resource(model_instance_type, self.user,
                                         "Testing migrating to composite resource")
        if add_keywords:
            res.metadata.create_element('subject', value='kw-1')
            res.metadata.create_element('subject', value='kw-2')
        return res
