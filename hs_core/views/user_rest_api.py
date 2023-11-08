from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from theme.models import UserProfile
from rest_framework import serializers
from theme.views import check_organization_terms


class UserSerializerIn(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    organization = serializers.ListField(required=False)
    state = serializers.CharField(max_length=150, required=False)
    country = serializers.CharField(max_length=150, required=False)
    user_type = serializers.CharField(max_length=150, required=False)
    orcid = serializers.CharField(max_length=150, required=False)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    organization = serializers.ListField()
    state = serializers.CharField(max_length=150)
    country = serializers.CharField(max_length=150)
    user_type = serializers.CharField(max_length=150)
    orcid = serializers.CharField(max_length=150, required=False)


class UserInfo(APIView):

    def _user_info(self, user):
        user_info = {"username": user.username}

        if user.email:
            user_info['email'] = user.email
        if user.first_name:
            user_info['first_name'] = user.first_name
        if user.id:
            user_info['id'] = user.id
        if user.last_name:
            user_info['last_name'] = user.last_name

        user_profile = UserProfile.objects.filter(user=user).first()
        if user_profile.title:
            user_info['title'] = user_profile.title
        if user_profile.organization:
            user_info['organization'] = user_profile.organization
            user_info['organizations'] = [org for org in user_profile.organization.split(";")]
        if user_profile.state and user_profile.state.strip() and user_profile.state != 'Unspecified':
            user_info['state'] = user_profile.state.strip()
        if user_profile.country and user_profile.country != 'Unspecified':
            user_info['country'] = user_profile.country
        if user_profile.user_type and user_profile.user_type.strip() and user_profile.user_type != 'Unspecified':
            user_info['user_type'] = user_profile.user_type.strip()
        if "ORCID" in user_profile.identifiers:
            user_info['orcid'] = user_profile.identifiers["ORCID"]
        if user_profile.subject_areas:
            user_info['subject_areas'] = [subject for subject in user_profile.subject_areas]

        return user_info

    @swagger_auto_schema(operation_description="Get information about the autorized user",
                         responses={200: UserSerializer})
    def get(self, request):
        '''
        Get information about the logged in user

        :param request:
        :return: HttpResponse response containing **user_info**
        '''
        if not request.user.is_authenticated:
            raise PermissionDenied

        user_info = self._user_info(request.user)
        return Response(user_info)

    @swagger_auto_schema(operation_description="Update information for the authorized user",
                         request_body=UserSerializerIn)
    def put(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        user: User = request.user
        user_info: dict = request.data

        if "first_name" in user_info:
            user.first_name = user_info["first_name"]
        if "last_name" in user_info:
            user.last_name = user_info["last_name"]

        user_profile: UserProfile = UserProfile.objects.filter(user=user).first()
        if "organization" in user_info:
            user_profile.organization = ";".join(user_info["organization"])
            check_organization_terms(user_info["organization"])
        if "state" in user_info:
            user_profile.state = user_info["state"]
        if "country" in user_info:
            user_profile.country = user_info["country"]
        if "user_type" in user_info:
            user_profile.user_type = user_info["user_type"]
        if "orcid" in user_info:
            user_profile.identifiers["ORCID"] = user_info["orcid"]

        with transaction.atomic():
            if "last_name" in user_info or "first_name" in user_info:
                user.save()
            if "organization" in user_info or "state" in user_info \
                    or "country" in user_info or "user_type" in user_info:
                user_profile.save()

        return self.get(request)
