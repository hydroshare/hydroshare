from rest_framework import serializers

from hs_modelinstance.serializers import ModelInstanceMetaDataSerializer
from models import ModelOutput, ExecutedBy, StudyArea, GridDimensions, \
    StressPeriod, GroundWaterFlow, BoundaryCondition, ModelCalibration,\
    ModelInput, GeneralElements, SpecifiedHeadBoundaryPackageChoices, \
    SpecifiedFluxBoundaryPackageChoices, HeadDependentFluxBoundaryPackageChoices, \
    OutputControlPackageChoices, MODFLOWModelInstanceMetaData


class ModelOutputMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelOutput
        fields = ('includes_output',)


class ExecutedByMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutedBy
        fields = ('modelProgramName', 'modelProgramIdentifier')


class StudyAreaMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyArea
        fields = ('totalLength', 'totalWidth', 'maximumElevation', 'minimumElevation')


class GridDimensionsMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridDimensions
        fields = ('numberOfLayers', 'typeOfRows', 'numberOfRows',
                  'typeOfColumns', 'numberOfColumns')


class StressPeriodMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StressPeriod
        fields = ('stressPeriodType', 'steadyStateValue', 'transientStateValueType',
                  'transientStateValue')


class GroundWaterFlowMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroundWaterFlow
        fields = ('flowPackage', 'flowParameter')


class SpecifiedHeadBoundaryPackageChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecifiedHeadBoundaryPackageChoices
        fields = ('description',)


class SpecifiedFluxBoundaryPackageChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecifiedFluxBoundaryPackageChoices
        fields = ('description',)


class HeadDependentFluxBoundaryPackageChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeadDependentFluxBoundaryPackageChoices
        fields = ('description',)


class OutputControlPackageChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutputControlPackageChoices
        fields = ('description',)


class BoundaryConditionMetaDataSerializer(serializers.ModelSerializer):
    specified_head_boundary_packages = SpecifiedHeadBoundaryPackageChoicesMetaDataSerializer(
        required=False, many=True)
    specified_flux_boundary_packages = SpecifiedHeadBoundaryPackageChoicesMetaDataSerializer(
        required=False, many=True)
    head_dependent_flux_boundary_packages = \
        HeadDependentFluxBoundaryPackageChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = BoundaryCondition
        fields = ('specified_head_boundary_packages', 'other_specified_head_boundary_packages',
                  'specified_flux_boundary_packages', 'other_specified_flux_boundary_packages',
                  'head_dependent_flux_boundary_packages',
                  'other_head_dependent_flux_boundary_packages')


class ModelCalibrationMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCalibration
        fields = ('calibratedParameter', 'observationType',
                  'observationProcessPackage', 'calibrationMethod')


class ModelInputMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelInput
        fields = ('inputType', 'inputSourceName', 'inputSourceURL')


class GeneralElementsMetaDataSerializer(serializers.ModelSerializer):
    output_control_package = OutputControlPackageChoicesMetaDataSerializer(required=False,
                                                                           many=True)

    class Meta:
        model = GeneralElements
        fields = ('modelParameter', 'modelSolver', 'output_control_package', 'subsidencePackage')


class MODFLOWModelInstanceMetaDataSerializer(ModelInstanceMetaDataSerializer):
    study_area = StudyAreaMetaDataSerializer(required=False, many=False)
    grid_dimensions = GridDimensionsMetaDataSerializer(required=False, many=False)
    stress_period = StressPeriodMetaDataSerializer(required=False, many=False)
    ground_water_flow = GroundWaterFlowMetaDataSerializer(required=False, many=False)
    boundary_condition = BoundaryConditionMetaDataSerializer(required=False, many=False)
    model_calibration = ModelCalibrationMetaDataSerializer(required=False, many=False)
    model_inputs = ModelInputMetaDataSerializer(required=False, many=True)
    general_elements = GeneralElementsMetaDataSerializer(required=False, many=False)

    class Meta:
        model = MODFLOWModelInstanceMetaData
