from django.http import JsonResponse

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound


class FileMetaDataListCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,


class FileMetaDataRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    def get(self, request, pk, pathname):
        return HttpResponseRedirect(url)
        pass

    def post():
        # keywords:123213

        #dataset_name:File Metadata 1

        ## Keyvalue
        # key:12312321
        # value:12312312321

        ## Temporal Coverage
        # start:02/15/2018
        # end:02/21/2018

        ## Spatial Coverage
        # type:point
        # name:21323
        # projection:WGS 84 EPSG:4326
        # east:-80.6836
        # north:35.0300
        # northlimit:
        # eastlimit:
        # southlimit:
        # westlimit:
        # units:Decimal degrees
        pass
