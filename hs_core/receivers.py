"""Signal receivers for the hs_core app."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete, post_delete
from django.db import models
from django.dispatch import receiver
from django_s3.storage import S3Storage
from hs_access_control.models.privilege import UserResourcePrivilege, GroupResourcePrivilege, UserGroupPrivilege
from hs_access_control.models.resource import ResourceAccess
from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update, \
    pre_delete_resource, post_add_geofeature_aggregation, post_add_generic_aggregation, \
    post_add_netcdf_aggregation, post_add_raster_aggregation, post_add_timeseries_aggregation, \
    post_add_reftimeseries_aggregation, post_remove_file_aggregation, post_raccess_change, \
    post_delete_file_from_resource, post_add_csv_aggregation
from hs_core.tasks import update_web_services
from hs_core.models import BaseResource, Creator, Contributor, Party, UserResource
from django.conf import settings

from hs_labels.models import FlagCodes, UserResourceFlags
from .forms import SubjectsForm, AbstractValidationForm, CreatorValidationForm, \
    ContributorValidationForm, RelationValidationForm, RightsValidationForm, \
    LanguageValidationForm, ValidDateValidationForm, FundingAgencyValidationForm, \
    CoverageSpatialForm, CoverageTemporalForm, IdentifierForm, TitleValidationForm, \
    GeospatialRelationValidationForm
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def update_party_instance(sender, instance, created, **kwargs):
    """Updates party (creator/contributor) db record when an associated user record gets updated"""

    user = instance

    def update_active_user_flag(party):
        if party.is_active_user != user.is_active:
            party.is_active_user = user.is_active
            party.save()

    if not created:
        for creator in Creator.objects.filter(hydroshare_user_id=user.id).all():
            update_active_user_flag(creator)

        for contributor in Contributor.objects.filter(hydroshare_user_id=user.id).all():
            update_active_user_flag(contributor)


@receiver(pre_metadata_element_create, sender=BaseResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    """Select proper form class based on element_name.

    This handler is executed only when a metadata element is added as part of editing a resource
    """
    element_name = kwargs['element_name']
    request = kwargs['request']
    if element_name == "subject":   # keywords
        element_form = SubjectsForm(data=request.POST)
    elif element_name == "description":   # abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "creator":
        try:
            post_data_dict = Party.get_post_data_with_identifiers(request=request)
        except Exception as ex:
            return {'is_valid': False, 'element_data_dict': None,
                    "errors": {"identifiers": [str(ex)]}}

        element_form = CreatorValidationForm(post_data_dict)

    elif element_name == "contributor":
        try:
            post_data_dict = Party.get_post_data_with_identifiers(request=request)
        except Exception as ex:
            return {'is_valid': False, 'element_data_dict': None,
                    "errors": {"identifiers": [str(ex)]}}
        element_form = ContributorValidationForm(post_data_dict)

    elif element_name == "citation":
        return {'is_valid': True, 'element_data_dict': {'value': request.POST.get('content').strip()}}

    elif element_name == 'relation':
        element_form = RelationValidationForm(request.POST)
    elif element_name == 'geospatialrelation':
        element_form = GeospatialRelationValidationForm(request.POST)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'fundingagency':
        element_form = FundingAgencyValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            if request.POST['type'].lower() == 'point' or request.POST['type'].lower() == 'box':
                element_form = CoverageSpatialForm(data=request.POST)
            else:
                element_form = CoverageTemporalForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)
    elif element_name == 'identifier':
        element_form = IdentifierForm(data=request.POST)
    else:
        raise Exception("Invalid metadata element name:{}".format(element_name))

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(pre_metadata_element_update, sender=BaseResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    """Select proper form class based on element_name.

    This handler is executed only when a metadata element is added as part of editing a resource
    """
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    repeatable_elements = {'creator': CreatorValidationForm,
                           'contributor': ContributorValidationForm,
                           'relation': RelationValidationForm,
                           'geospatialrelation': GeospatialRelationValidationForm
                           }
    if element_name == 'title':
        element_form = TitleValidationForm(request.POST)
    elif element_name == "description":   # abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "fundingagency":
        element_form = FundingAgencyValidationForm(request.POST)
    elif element_name == "citation":
        return {'is_valid': True, 'element_data_dict': {'value': request.POST.get('content').strip()}}
    elif element_name in repeatable_elements:
        # since element_name is a repeatable element (e.g creator) and data for the element
        # is displayed on the landing page using formset, the data coming from a single element
        # form in the request for update needs to be parsed to match with element field names
        element_validation_form = repeatable_elements[element_name]
        form_data = {}
        for field_name in element_validation_form().fields:
            if element_name.lower() == "creator" or element_name.lower() == "contributor":
                try:
                    post_data_dict = Party.get_post_data_with_identifiers(request=request)
                except Exception as ex:
                    return {'is_valid': False, 'element_data_dict': None,
                            "errors": {"identifiers": [str(ex)]}}

                # for creator or contributor who is not a hydroshare user the 'hydroshare_user_id'
                # key might be missing in the POST form data
                if field_name == 'hydroshare_user_id':
                    matching_key = [key for key in request.POST if '-' + field_name in key]
                    if matching_key:
                        matching_key = matching_key[0]
                    else:
                        continue
                elif field_name == 'identifiers':
                    matching_key = 'identifiers'
                else:
                    matching_key = [key for key in request.POST if '-' + field_name in key][0]

                form_data[field_name] = post_data_dict[matching_key]
            else:
                matching_key = [key for key in request.POST if '-' + field_name in key][0]
                form_data[field_name] = request.POST[matching_key]

        element_form = element_validation_form(form_data)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)
    elif element_name == 'identifier':
        element_form = IdentifierForm(data=request.POST)
    else:
        raise Exception("Invalid metadata element name:{}".format(element_name))

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(post_add_generic_aggregation)
@receiver(post_add_csv_aggregation)
@receiver(post_add_geofeature_aggregation)
@receiver(post_add_raster_aggregation)
@receiver(post_add_netcdf_aggregation)
@receiver(post_add_timeseries_aggregation)
@receiver(post_add_reftimeseries_aggregation)
@receiver(post_remove_file_aggregation)
@receiver(pre_delete_resource)
@receiver(post_delete_file_from_resource)
@receiver(post_raccess_change)
def hs_update_web_services(sender, **kwargs):
    """Signal to update resource web services."""

    if settings.HSWS_ACTIVATED:
        rid = None
        if "resource" in kwargs:
            rid = kwargs.get("resource").short_id
        elif "resource_id" in kwargs:
            rid = kwargs.get('resource_id')
        if rid:
            update_web_services.apply_async((
                settings.HSWS_URL,
                settings.HSWS_API_TOKEN,
                settings.HSWS_TIMEOUT,
                settings.HSWS_PUBLISH_URLS,
                rid
            ), countdown=1)


@receiver(pre_delete, sender=User)
def pre_delete_user_handler(sender, instance, **kwargs):
    # before delete the user, update the quota holder for all of the user's resources
    user = instance
    for res in BaseResource.objects.filter(quota_holder=user):
        other_owners = None
        if hasattr(res, 'raccess') and res.raccess is not None:
            other_owners = res.raccess.owners.exclude(pk=user.pk)
        if other_owners:
            res.quota_holder = other_owners.first()
        else:
            logger.error("Resource:{} has no owner after deleting user:{}".format(res.short_id,
                                                                                  user.username))
            res.quota_holder = None
        res.save()
    istorage = S3Storage()
    if istorage.bucket_exists(user.username):
        # delete the bucket for the user
        istorage.delete_bucket(user.username)


@receiver(post_save, sender=ResourceAccess)
def resource_access_post_save_handler(sender, instance, **kwargs):
    """Update status in denormalized metadata when resource sharing 
    status (public, discoverable, published) changes"""
    try:
        resource = instance.resource
        resource.update_denormalized_metadata_field('status')
    except Exception as ex:
        logger.error(f"Error updating status in denormalized metadata: {str(ex)}")


@receiver(post_save, sender=UserResourcePrivilege)
def update_user_resource_permission(sender, instance, **kwargs):
    """Update UserResource when user permissions change on a resource"""

    # Calculate effective user privilege on the resource (combines user and group permissions)
    effective_privilege = instance.resource.raccess.get_effective_privilege(instance.user)
    UserResource.objects.update_or_create(
        user=instance.user,
        resource=instance.resource,
        defaults={
            'permission': effective_privilege,
        }
    )


@receiver(post_delete, sender=UserResourcePrivilege)
def remove_user_resource_permission(sender, instance, **kwargs):
    """
    Update UserResource when user permission is removed from a resource.
    Check if user still has access to the resource via group permissions on the resource.
    """
    from hs_access_control.models.privilege import PrivilegeCodes

    # Calculate effective user privilege on the resource (group permissions may still exist)
    effective_privilege = instance.resource.raccess.get_effective_privilege(instance.user)

    try:
        ur = UserResource.objects.get(user=instance.user, resource=instance.resource)
        if effective_privilege == PrivilegeCodes.NONE:
            # No permissions left - remove entry if the resource is not favorited/discovered by the user
            if not (ur.is_favorite or ur.is_discovered):
                ur.delete()
            else:
                ur.permission = PrivilegeCodes.NONE
                ur.save()
        else:
            # Still has group-based permissions on the resource
            ur.permission = effective_privilege
            ur.save()
    except UserResource.DoesNotExist:
        pass


@receiver(post_save, sender=UserResourceFlags)
def update_user_resource_flags(sender, instance, **kwargs):
    """Update UserResource table when flags change"""
    defaults = {}

    if instance.kind == FlagCodes.FAVORITE:
        defaults['is_favorite'] = True
    elif instance.kind == FlagCodes.MINE:
        defaults['is_discovered'] = True

    # Calculate user effective privilege on the resource (includes both user and group permissions)
    effective_privilege = instance.resource.raccess.get_effective_privilege(instance.user)
    defaults['permission'] = effective_privilege

    UserResource.objects.update_or_create(
        user=instance.user,
        resource=instance.resource,
        defaults=defaults
    )


@receiver(post_delete, sender=UserResourceFlags)
def remove_user_resource_flags(sender, instance, **kwargs):
    """Update UserResource table when flags are removed"""
    from hs_access_control.models.privilege import PrivilegeCodes

    try:
        ur = UserResource.objects.get(user=instance.user, resource=instance.resource)

        # Update the appropriate flag
        if instance.kind == FlagCodes.FAVORITE:
            ur.is_favorite = False
        elif instance.kind == FlagCodes.MINE:
            ur.is_discovered = False

        # Check if UserResource record should be removed entirely
        if (ur.permission == PrivilegeCodes.NONE and 
            not ur.is_favorite and not ur.is_discovered):
            ur.delete()
        else:
            ur.save()

    except UserResource.DoesNotExist:
        # No UserResource entry exists, nothing to update
        pass


def update_group_based_user_resources(group, resource):
    """
    Helper function to update UserResource table entries for all users in a group
    when group permissions on a resource change.
    """
    from hs_access_control.models.privilege import PrivilegeCodes

    # Get all active users in the group
    users_in_group = User.objects.filter(
        u2ugp__group=group,
        is_active=True
    ).distinct()

    for user in users_in_group:
        # Calculate effective permission for this user on the resource
        # This combines direct user permissions and via group permissions
        effective_permission = resource.raccess.get_effective_privilege(user)

        if effective_permission < PrivilegeCodes.NONE:  # User has some permission
            UserResource.objects.update_or_create(
                user=user,
                resource=resource,
                defaults={'permission': effective_permission}
            )
        else:
            # User has no effective permission on the resource, check if UserResource record should be removed
            try:
                ur = UserResource.objects.get(user=user, resource=resource)
                if not (ur.is_favorite or ur.is_discovered):
                    ur.delete()
                else:
                    ur.permission = PrivilegeCodes.NONE
                    ur.save()
            except UserResource.DoesNotExist:
                pass


@receiver(post_save, sender=GroupResourcePrivilege)
def update_group_resource_permission(sender, instance, **kwargs):
    """
    Update UserResource table for all users in group when group permission on a resource changes
    """
    update_group_based_user_resources(instance.group, instance.resource)


@receiver(post_delete, sender=GroupResourcePrivilege)  
def remove_group_resource_permission(sender, instance, **kwargs):
    """
    Update UserResource table for all users in group when group permission on a resource is removed
    """
    update_group_based_user_resources(instance.group, instance.resource)


@receiver(post_save, sender=UserGroupPrivilege)
def update_user_group_membership(sender, instance, **kwargs):
    """
    Update UserResource table for user when they join/leave a group or privilege on a resource changes
    """
    from hs_access_control.models.privilege import PrivilegeCodes

    # Get all resources that the group has access to
    group_resources = GroupResourcePrivilege.objects.filter(
        group=instance.group
    ).select_related('resource', 'resource__raccess')

    # Pre-fetch user's direct privileges on all these resources to avoid N+1 queries
    resource_ids = [grp.resource_id for grp in group_resources]
    user_res_privileges_dict = {
        urp.resource_id: urp.privilege 
        for urp in UserResourcePrivilege.objects.filter(
            user=instance.user, 
            resource_id__in=resource_ids
        )
    }

    # Pre-fetch user's group privileges on all these resources to avoid N+1 queries
    user_group_res_privileges = GroupResourcePrivilege.objects.filter(
        resource_id__in=resource_ids,
        group__gaccess__active=True,
        group__g2ugp__user=instance.user
    ).values('resource_id').annotate(
        min_privilege=models.Min('privilege')
    )
    user_group_res_privileges_dict = {ugrp['resource_id']: ugrp['min_privilege'] for ugrp in user_group_res_privileges}

    for grp in group_resources:
        # Calculate effective permission for this user on each resource
        # Using pre-fetched data instead of making individual queries
        user_res_priv = user_res_privileges_dict.get(grp.resource_id, PrivilegeCodes.NONE)
        group_res_priv = user_group_res_privileges_dict.get(grp.resource_id, PrivilegeCodes.NONE)

        # Apply resource flags (immutable check)
        if grp.resource.raccess.immutable:
            if user_res_priv == PrivilegeCodes.CHANGE:
                user_res_priv = PrivilegeCodes.VIEW
            if group_res_priv == PrivilegeCodes.CHANGE:
                group_res_priv = PrivilegeCodes.VIEW

        # Apply superuser privileges
        if instance.user.is_superuser:
            effective_permission = PrivilegeCodes.OWNER
        else:
            effective_permission = min(user_res_priv, group_res_priv)

        if effective_permission < PrivilegeCodes.NONE:  # User has some permission
            UserResource.objects.update_or_create(
                user=instance.user,
                resource=grp.resource,
                defaults={'permission': effective_permission}
            )
        else:
            # User has no effective permission on the resource, check if UserResource record should be removed
            try:
                ur = UserResource.objects.get(
                    user=instance.user, 
                    resource=grp.resource
                )
                if not (ur.is_favorite or ur.is_discovered):
                    ur.delete()
                else:
                    ur.permission = PrivilegeCodes.NONE
                    ur.save()
            except UserResource.DoesNotExist:
                pass


@receiver(post_delete, sender=UserGroupPrivilege)
def remove_user_group_membership(sender, instance, **kwargs):
    """
    Update UserResource table for user when they are removed from a group
    """
    from hs_access_control.models.privilege import PrivilegeCodes

    # Get all resources that the group has access to
    group_resources = GroupResourcePrivilege.objects.filter(
        group=instance.group
    ).select_related('resource', 'resource__raccess')

    if not group_resources:
        return

    # Get resource IDs for bulk queries
    resource_ids = [grp.resource.id for grp in group_resources]

    # Pre-fetch user privileges for all resources
    user_res_privileges = {}
    if not instance.user.is_superuser:
        user_priv_qs = UserResourcePrivilege.objects.filter(
            user=instance.user,
            resource_id__in=resource_ids
        ).values('resource_id', 'privilege')
        for priv in user_priv_qs:
            user_res_privileges[priv['resource_id']] = priv['privilege']

    # Pre-fetch group privileges for all resources (excluding the removed group)
    user_group_res_privileges = {}
    if not instance.user.is_superuser:
        # Get user's groups excluding the one they were removed from
        user_groups = instance.user.uaccess.my_groups.exclude(id=instance.group.id)
        if user_groups.exists():
            group_priv_qs = GroupResourcePrivilege.objects.filter(
                resource_id__in=resource_ids,
                group__in=user_groups
            ).values('resource_id').annotate(
                min_privilege=models.Min('privilege')
            )
            for priv in group_priv_qs:
                user_group_res_privileges[priv['resource_id']] = priv['min_privilege']

    for grp in group_resources:
        # Skip immutable resources if user is not superuser
        if grp.resource.raccess.immutable and not instance.user.is_superuser:
            continue

        # Calculate effective permission manually to avoid N+1 queries
        if instance.user.is_superuser:
            effective_permission = PrivilegeCodes.OWNER
        else:
            user_priv = user_res_privileges.get(grp.resource.id, PrivilegeCodes.NONE)
            group_priv = user_group_res_privileges.get(grp.resource.id, PrivilegeCodes.NONE)
            effective_permission = min(user_priv, group_priv)

        if effective_permission < PrivilegeCodes.NONE:  # User still has some permission
            UserResource.objects.update_or_create(
                user=instance.user,
                resource=grp.resource,
                defaults={'permission': effective_permission}
            )
        else:
            # User has no effective permission on the resource, check if UserResource record should be removed
            try:
                ur = UserResource.objects.get(
                    user=instance.user, 
                    resource=grp.resource
                )
                if not (ur.is_favorite or ur.is_discovered):
                    ur.delete()
                else:
                    ur.permission = PrivilegeCodes.NONE
                    ur.save()
            except UserResource.DoesNotExist:
                pass
