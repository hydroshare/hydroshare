from rest_framework.views import APIView
from rest_framework.response import Response

from .models import University


class ListUniversities(APIView):
    """
    View to list all known universities in the system
    """

    def get(self, request, format=None, query=None):
        """
        Return a list of all vocabulary items
        :return:
        """

        if query:
            filtered_unis = University.objects.filter(name__icontains=query)
            universities = [uni.name for uni in filtered_unis]
        else:
            universities = [uni.name for uni in University.objects.all()]

        return Response(universities)