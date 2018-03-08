from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import generics, serializers, status

from hs_core.models import BaseResource
from hs_rest_api.permissions import CanEditResourceMetadata
from hs_publication.models import PublicationQueue


class PublicationQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationQueue
        fields = ('resource', 'created_at', 'updated_at', 'status', 'note')


class PublicationQueueCreate(generics.CreateAPIView):
    permission_classes = (CanEditResourceMetadata,)

    def post(self, request, pk):
        try:
            res = BaseResource.objects.get(short_id=pk)
        except Exception as e:
            return Response({"error": "Resource does not exist."}, status=status.HTTP_404_NOT_FOUND)

        try:
            PublicationQueue.objects.get(resource=res.id)
            return Response({"error": "Publication request already exists."}, status=status.HTTP_409_CONFLICT)
        except PublicationQueue.DoesNotExist:
            pq = PublicationQueue.objects.create(resource=res)
            return Response(PublicationQueueSerializer(pq).data)