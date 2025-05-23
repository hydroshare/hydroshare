"""Signal receivers for the hs_core app."""
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_s3.storage import S3Storage
from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update, \
    pre_delete_resource, post_add_geofeature_aggregation, post_add_generic_aggregation, \
    post_add_netcdf_aggregation, post_add_raster_aggregation, post_add_timeseries_aggregation, \
    post_add_reftimeseries_aggregation, post_remove_file_aggregation, post_raccess_change, \
    post_delete_file_from_resource, post_add_csv_aggregation
from hs_core.tasks import update_web_services
from hs_core.models import BaseResource, Creator, Contributor, Party
from django.conf import settings
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
