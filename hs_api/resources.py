from rest_framework import serializers
from hs_core.models import BaseResource

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseResource
        fields = ('root_path',)

class ResourceListItemSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)