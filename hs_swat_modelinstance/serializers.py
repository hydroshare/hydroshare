from rest_framework import serializers

from hs_modelinstance.serializers import ModelInstanceMetaDataSerializer
from models import ModelObjective, SimulationType, ModelMethod, ModelParameter, ModelInput, \
     ModelObjectiveChoices, ModelParametersChoices, SWATModelInstanceMetaData


class ModelObjectiveChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelObjectiveChoices
        fields = ('description',)


class ModelParametersChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelParametersChoices
        fields = ('description',)


class ModelObjectiveMetaDataSerializer(serializers.ModelSerializer):
    swat_model_objectives = ModelObjectiveChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = ModelObjective
        fields = ('swat_model_objectives', 'other_objectives')


class SimulationTypeMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationType
        fields = ('simulation_type_name',)


class ModelMethodMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMethod
        fields = ('runoffCalculationMethod', 'flowRoutingMethod', 'petEstimationMethod')


class ModelParameterMetaDataSerializer(serializers.ModelSerializer):
    model_parameters = ModelParametersChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = ModelParameter
        fields = ('model_parameters', 'other_parameters')


class ModelInputMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelInput
        fields = ('warmupPeriodValue', 'rainfallTimeStepType', 'rainfallTimeStepValue',
                  'routingTimeStepType', 'routingTimeStepValue', 'simulationTimeStepType',
                  'simulationTimeStepValue', 'watershedArea', 'numberOfSubbasins', 'numberOfHRUs',
                  'demResolution', 'demSourceName', 'demSourceURL', 'landUseDataSourceName',
                  'landUseDataSourceURL', 'soilDataSourceName', 'soilDataSourceURL')


class SWATModelInstanceMetaDataSerializer(ModelInstanceMetaDataSerializer):
    model_objective = ModelObjectiveMetaDataSerializer(required=False, many=False)
    simulation_type = SimulationTypeMetaDataSerializer(required=False, many=False)
    model_method = ModelMethodMetaDataSerializer(required=False, many=False)
    model_parameter = ModelParameterMetaDataSerializer(required=False, many=False)
    model_input = ModelInputMetaDataSerializer(required=False, many=False)

    class Meta:
        model = SWATModelInstanceMetaData
