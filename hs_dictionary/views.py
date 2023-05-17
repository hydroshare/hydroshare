from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import University, SubjectArea
from drf_yasg.utils import swagger_auto_schema
from functools import reduce


class ListUniversities(APIView):
    """
    View to list all known universities in the system
    """

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, format=None, query=None):
        """
        Return a list of all vocabulary items
        :return:
        """
        terms = request.GET.get('term', '')
        term_list = terms.split(' ')

        if len(term_list):
            universities = University.objects.filter(
                reduce(lambda x, y: x & y, [Q(name__icontains=word) for word in term_list])
            ).values_list('name', flat=True)
        else:
            universities = []

        if len(universities) > 50:
            universities = ['Too many items to list, please continue typing...']

        return Response(universities)


class ListSubjectAreas(APIView):
    """
    View to list all known subject areas in the system
    """

    @swagger_auto_schema(auto_schema=None)
    def get(self, request, format=None, query=None):
        """
        Return a list of all vocabulary items
        :return:
        """
        terms = request.GET.get('term', '')
        term_list = terms.split(' ')

        if len(term_list):
            subject_areas = SubjectArea.objects.filter(
                reduce(lambda x, y: x & y, [Q(name__icontains=word) for word in term_list])
            ).values_list('name', flat=True)
        else:
            subject_areas = []

        if len(subject_areas) > 50:
            subject_areas = ['Too many items to list, please continue typing...']

        return Response(subject_areas)
