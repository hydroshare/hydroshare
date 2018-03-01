from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render

from hs_core import hydroshare
from hs_core import utils
from hs_core.utils import authorize, ACTION_TO_AUTHORIZE


def publish_resource(user, pk):
    """
    Formally publishes a resource in HydroShare. Triggers the creation of a DOI for the resource,
    and triggers the exposure of the resource to the HydroShare DataONE Member Node. The user must
    be an owner of a resource or an administrator to perform this action.

    Parameters:
        user - requesting user to publish the resource who must be one of the owners of the resource
        pk - Unique HydroShare identifier for the resource to be formally published.

    Returns:    The id of the resource that was published

    Return Type:    string

    Raises:
    Exceptions.NotAuthorized - The user is not authorized
    Exceptions.NotFound - The resource identified by pid does not exist
    Exception.ServiceFailure - The service is unable to process the request
    and other general exceptions

    Note:  This is different than just giving public access to a resource via access control rule
    """
    resource = utils.get_resource_by_shortkey(pk)

    # TODO: whether a resource can be published is not considered in can_be_published
    # TODO: can_be_published is currently an alias for can_be_public_or_discoverable
    if not resource.can_be_published:
        raise ValidationError("This resource cannot be published since it does not have required "
                              "metadata or content files or this resource type is not allowed "
                              "for publication.")

    # append pending to the doi field to indicate DOI is not activated yet. Upon successful
    # activation, "pending" will be removed from DOI field
    resource.doi = get_resource_doi(pk, 'pending')
    resource.save()

    response = deposit_res_metadata_with_crossref(resource)
    if not response.status_code == status.HTTP_200_OK:
        # resource metadata deposition failed from CrossRef - set failure flag to be retried in a
        # crontab celery task
        resource.doi = get_resource_doi(pk, 'failure')
        resource.save()

    resource.set_public(True)  # also sets discoverable to True
    resource.raccess.immutable = True
    resource.raccess.shareable = False
    resource.raccess.published = True
    resource.raccess.save()

    # change "Publisher" element of science metadata to CUAHSI
    md_args = {'name': 'Consortium of Universities for the Advancement of Hydrologic Science, '
                       'Inc. (CUAHSI)',
               'url': 'https://www.cuahsi.org'}
    resource.metadata.create_element('Publisher', **md_args)

    # create published date
    resource.metadata.create_element('date', type='published', start_date=resource.updated)

    # add doi to "Identifier" element of science metadata
    md_args = {'name': 'doi',
               'url': get_activated_doi(resource.doi)}
    resource.metadata.create_element('Identifier', **md_args)

    utils.resource_modified(resource, user, overwrite_bag=False)

    return pk


def publish(request, shortkey, *args, **kwargs):
    # only resource owners are allowed to change resource flags (e.g published)
    res, _, _ = authorize(request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG)

    try:
        hydroshare.publish_resource(request.user, shortkey)
    except ValidationError as exp:
        request.session['validation_error'] = exp.message
    else:
        request.session['just_published'] = True
    return HttpResponseRedirect(request.META['HTTP_REFERER'])