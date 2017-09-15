from django.db.models import Q

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
        terms = request.GET.get('term', None)
        term_list = terms.split(' ')

        if len(term_list):
            filtered_unis = University.objects.filter(
                reduce(lambda x, y: x & y, [Q(name__icontains=word) for word in term_list])
            )
            universities = [uni.name for uni in filtered_unis]
        else:
            universities = []

        if len(universities) > 50:
            universities = ['Too many items to list, please continue typing...']

        return Response(universities)
