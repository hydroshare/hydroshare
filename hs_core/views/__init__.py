import datetime
import json
import logging

from autocomplete_light import shortcuts as autocomplete_light
from dateutil import tz
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import Error, IntegrityError
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from mezzanine.conf import settings
from mezzanine.pages.page_processors import processor_for
from mezzanine.utils.email import send_mail_template, subject_template
from rest_framework import status
from rest_framework.decorators import api_view
from sorl.thumbnail import ImageField as ThumbnailImageField, get_thumbnail

from django_irods.icommands import SessionException
from hs_access_control.emails import CommunityRequestEmailNotification
from hs_access_control.enums import CommunityRequestEvents
from hs_access_control.forms import RequestNewCommunityForm, UpdateCommunityForm
from hs_access_control.models import Community, GroupCommunityRequest, UserGroupPrivilege
from hs_access_control.models import GroupMembershipRequest, GroupResourcePrivilege, PrivilegeCodes
from hs_access_control.views import community_json, group_community_request_json
from hs_core import hydroshare
from hs_core import signals
from hs_core.enums import RelationTypes
from hs_core.hydroshare.resource import (
    METADATA_STATUS_INSUFFICIENT,
    METADATA_STATUS_SUFFICIENT,
    update_quota_usage as update_quota_usage_utility,
)
from hs_core.hydroshare.utils import (
    get_resource_by_shortkey,
    resolve_request,
    resource_modified,
)
from hs_core.models import (
    BaseResource,
    CoreMetaData,
    Subject,
    TaskNotification,
    resource_processor,
)
from hs_core.task_utils import (
    dismiss_task_by_id,
    get_all_tasks,
    get_or_create_task_notification,
    get_resource_delete_task,
    get_task_user_id,
    revoke_task_by_id,
    set_task_delivered_by_id,
)
from hs_core.tasks import (
    copy_resource_task,
    create_new_version_resource_task,
    delete_resource_task,
    replicate_resource_bag_to_user_zone_task,
)
from hs_tools_resource.app_launch_helper import resource_level_tool_urls
from theme.models import UserProfile
from . import apps
from . import debug_resource_view
from . import resource_access_api
from . import resource_folder_hierarchy
from . import resource_folder_rest_api
from . import resource_metadata_rest_api
from . import resource_rest_api
from . import resource_ticket_rest_api
from . import user_rest_api
from .utils import (
    ACTION_TO_AUTHORIZE,
    authorize,
    get_coverage_data_dict,
    get_my_resources_filter_counts,
    get_my_resources_list,
    run_script_to_update_hyrax_input_files,
    send_action_to_take_email,
    upload_from_irods,
)

logger = logging.getLogger(__name__)


def short_url(request, *args, **kwargs):
    try:
        shortkey = kwargs["shortkey"]
    except KeyError:
        raise TypeError("shortkey must be specified...")

    m = hydroshare.utils.get_resource_by_shortkey(shortkey)
    return HttpResponseRedirect(m.get_absolute_url())


def verify(request, *args, **kwargs):
    _, pk, email = signing.loads(kwargs["token"]).split(":")
    u = User.objects.get(pk=pk)
    if u.email == email:
        if not u.is_active:
            u.is_active = True
            u.save()
            u.groups.add(Group.objects.get(name="Hydroshare Author"))
        from django.contrib.auth import login

        u.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, u)
        return HttpResponseRedirect("/account/update/")
    else:
        from django.contrib import messages

        messages.error(request, "Your verification token was invalid.")

    return HttpResponseRedirect("/")


def get_tasks_by_user(request):
    user_id = get_task_user_id(request)
    task_list = get_all_tasks(user_id)
    return JsonResponse({"tasks": task_list})


def get_task(request, task_id):
    task_dict = get_or_create_task_notification(task_id)
    return JsonResponse(task_dict)


def abort_task(request, task_id):
    if request.user.is_authenticated:
        if TaskNotification.objects.filter(
            task_id=task_id, username=request.user.username
        ).exists():
            task_dict = revoke_task_by_id(task_id)
            return JsonResponse(task_dict)
        else:
            return JsonResponse(
                {"error": "not authorized to revoke the task"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        return JsonResponse(
            {"error": "not authorized to revoke the task"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@login_required
def dismiss_task(request, task_id):
    user_id = get_task_user_id(request)
    if TaskNotification.objects.filter(task_id=task_id, username=user_id).exists():
        task_dict = dismiss_task_by_id(task_id)
        if task_dict:
            return JsonResponse(task_dict)
        else:
            return JsonResponse(
                {"error": "requested task does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
    else:
        return JsonResponse(
            {"error": "not authorized to dismiss the task"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


def set_task_delivered(request, task_id):
    if request.user.is_authenticated:
        if TaskNotification.objects.filter(
            task_id=task_id, username=request.user.username
        ).exists():
            task_dict = set_task_delivered_by_id(task_id)
            if task_dict:
                return JsonResponse(task_dict)
            else:
                return JsonResponse(
                    {"error": "requested task does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return JsonResponse(
                {"error": "not authorized to deliver the task"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    elif TaskNotification.objects.filter(
        task_id=task_id, username=request.session.session_key
    ).exists():
        # dismiss the task entry for delivered tasks for anonymous users
        task_dict = dismiss_task_by_id(task_id)
        if task_dict:
            return JsonResponse(task_dict)
        else:
            return JsonResponse(
                {"error": "requested task does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )
    else:
        return JsonResponse(
            {"error": "not authorized to deliver the task"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@login_required
def change_quota_holder(request, shortkey):
    new_holder_uname = request.POST.get("new_holder_username", "")
    ajax_response_data = {"status": "error", "message": ""}

    if not new_holder_uname:
        ajax_response_data["message"] = "Please select a user."
        return JsonResponse(ajax_response_data)
    new_holder_u = User.objects.filter(username=new_holder_uname).first()
    if not new_holder_u:
        ajax_response_data["message"] = (
            "Unable to change quota holder. "
            "Please verify that the selected user still has access to this resource."
        )
        return JsonResponse(ajax_response_data)

    res = hydroshare.utils.get_resource_by_shortkey(shortkey)
    try:
        res.set_quota_holder(request.user, new_holder_u)

        # send notification to the new quota holder
        context = {
            "request": request,
            "user": request.user,
            "new_quota_holder": new_holder_u,
            "resource_uuid": res.short_id,
        }
        subject_template_name = "email/quota_holder_change_subject.txt"
        subject = subject_template(subject_template_name, context)
        send_mail_template(
            subject,
            "email/quota_holder_change",
            settings.DEFAULT_FROM_EMAIL,
            new_holder_u.email,
            context=context,
        )
    except PermissionDenied:
        ajax_response_data[
            "message"
        ] = "You do not have permission to change the quota holder for this resource."
        return JsonResponse(ajax_response_data)
    except hydroshare.utils.QuotaException as ex:
        msg = (
            "Failed to change quota holder to {0} since {0} does not have "
            "enough quota to hold this new resource. The exception quota message "
            "reported for {0} is: ".format(new_holder_u.username) + str(ex)
        )
        ajax_response_data["message"] = msg
        return JsonResponse(ajax_response_data)

    ajax_response_data["status"] = "success"
    return JsonResponse(ajax_response_data)


@swagger_auto_schema(method="post", auto_schema=None)
@api_view(["POST"])
def update_quota_usage(request, username):
    req_user = request.user
    if req_user.username != settings.IRODS_SERVICE_ACCOUNT_USERNAME:
        return HttpResponseForbidden(
            "only iRODS service account is authorized to " "perform this action"
        )
    if not req_user.is_authenticated:
        return HttpResponseForbidden("You are not authenticated to perform this action")

    try:
        _ = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseBadRequest("user to update quota for is not valid")

    try:
        update_quota_usage_utility(username)
        return HttpResponse(
            "quota for user {} has been updated".format(username), status=200
        )
    except ValidationError as ex:
        err_msg = "quota for user {} failed to update: {}".format(username, str(ex))
        return HttpResponse(err_msg, status=500)


def extract_files_with_paths(request):
    res_files = []
    full_paths = {}
    for key in list(request.FILES.keys()):
        full_path = request.POST.get(key, None)
        f = request.FILES[key]
        res_files.append(f)
        if full_path:
            full_paths[f] = full_path
    return res_files, full_paths


def add_files_to_resource(request, shortkey, *args, **kwargs):
    """
    This view function is called by AJAX in the folder implementation
    :param request: AJAX request
    :param shortkey: resource uuid
    :param args:
    :param kwargs:
    :return: HTTP response with status code indicating success or failure
    """
    resource, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    if resource.raccess.published and not user.is_superuser:
        msg = {"validation_error": "Only admin can add files to a published resource"}
        return JsonResponse(msg, status=500)

    res_files, full_paths = extract_files_with_paths(request)
    auto_aggregate = request.POST.get("auto_aggregate", "true").lower() == "true"
    extract_metadata = request.GET.get("extract-metadata", "No")
    extract_metadata = True if extract_metadata.lower() == "yes" else False
    file_folder = request.POST.get("file_folder", "")
    if file_folder == "data/contents":
        file_folder = ""
    elif file_folder.startswith("data/contents/"):
        file_folder = file_folder[len("data/contents/") :]

    try:
        hydroshare.utils.resource_file_add_pre_process(
            resource=resource,
            files=res_files,
            user=request.user,
            extract_metadata=extract_metadata,
            folder=file_folder,
        )

    except hydroshare.utils.ResourceFileSizeException as ex:
        msg = {"file_size_error": str(ex)}
        return JsonResponse(msg, status=500)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        msg = {"validation_error": str(ex)}
        return JsonResponse(msg, status=500)

    aggregations_pre = [aggr for aggr in resource.logical_files]
    aggr_count_pre = len(aggregations_pre)

    try:
        hydroshare.utils.resource_file_add_process(
            resource=resource,
            files=res_files,
            user=request.user,
            extract_metadata=extract_metadata,
            folder=file_folder,
            full_paths=full_paths,
            auto_aggregate=auto_aggregate,
        )

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        msg = {"validation_error": str(ex)}
        return JsonResponse(msg, status=500)

    aggregations_post = [aggr for aggr in resource.logical_files]
    aggr_count_post = len(aggregations_post)

    res_public_status = "public" if resource.raccess.public else "not public"
    res_discoverable_status = (
        "discoverable" if resource.raccess.discoverable else "not discoverable"
    )

    show_meta_status = False
    if "meta-status" not in request.session:
        request.session["meta-status"] = ""

    if "meta-status-res-id" not in request.session:
        request.session["meta-status-res-id"] = resource.short_id
        show_meta_status = True
    elif request.session["meta-status-res-id"] != resource.short_id:
        request.session["meta-status-res-id"] = resource.short_id
        show_meta_status = True

    if resource.can_be_public_or_discoverable:
        metadata_status = METADATA_STATUS_SUFFICIENT
    else:
        metadata_status = METADATA_STATUS_INSUFFICIENT

    if request.session["meta-status"] != metadata_status:
        request.session["meta-status"] = metadata_status
        show_meta_status = True

    response_data = {
        "res_public_status": res_public_status,
        "res_discoverable_status": res_discoverable_status,
        "number_new_aggregations": aggr_count_post - aggr_count_pre,
        "metadata_status": metadata_status,
        "show_meta_status": show_meta_status,
    }

    return JsonResponse(data=response_data, status=200)


def _get_resource_sender(element_name, resource):
    core_metadata_element_names = [
        el_name.lower() for el_name in CoreMetaData.get_supported_element_names()
    ]

    if element_name in core_metadata_element_names:
        sender_resource = BaseResource().__class__
    else:
        sender_resource = resource.__class__

    return sender_resource


def get_supported_file_types_for_resource_type(request, resource_type, *args, **kwargs):
    resource_cls = hydroshare.check_resource_type(resource_type)
    if request.is_ajax:
        # TODO: use try catch
        ajax_response_data = {
            "file_types": json.dumps(resource_cls.get_supported_upload_file_types())
        }
        return HttpResponse(json.dumps(ajax_response_data))
    else:
        return HttpResponseRedirect(request.META["HTTP_REFERER"])


def is_multiple_file_upload_allowed(request, resource_type, *args, **kwargs):
    resource_cls = hydroshare.check_resource_type(resource_type)
    if request.is_ajax:
        # TODO: use try catch
        ajax_response_data = {
            "allow_multiple_file": resource_cls.allow_multiple_file_upload()
        }
        return HttpResponse(json.dumps(ajax_response_data))
    else:
        return HttpResponseRedirect(request.META["HTTP_REFERER"])


def get_relevant_tools(request, shortkey, *args, **kwargs):
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    relevant_tools = resource_level_tool_urls(res, request)
    return HttpResponse(json.dumps(relevant_tools))


def update_key_value_metadata(request, shortkey, *args, **kwargs):
    """
    This one view function is for CRUD operation for resource key/value arbitrary metadata.
    key/value data in request.POST is assigned to the resource.extra_metadata field
    """
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    post_data = request.POST.copy()
    resource_mode = post_data.pop("resource-mode", None)
    extra_metadata = post_data.dict()
    extra_metadata_copy = extra_metadata.copy()
    for key in extra_metadata_copy:
        if not key:
            extra_metadata.pop(key)

    res.extra_metadata = extra_metadata
    is_update_success = True
    err_message = ""
    try:
        res.save()
    except Error as ex:
        is_update_success = False
        err_message = str(ex)

    if is_update_success:
        resource_modified(res, request.user, overwrite_bag=False)
        res_metadata = res.metadata
        res_metadata.set_dirty(True)

    if request.is_ajax():
        if is_update_success:
            ajax_response_data = {
                "status": "success",
                "is_dirty": res.metadata.is_dirty
                if hasattr(res.metadata, "is_dirty")
                else False,
            }
        else:
            ajax_response_data = {"status": "error", "message": err_message}
        return HttpResponse(json.dumps(ajax_response_data))

    if resource_mode is not None:
        request.session["resource-mode"] = "edit"

    if is_update_success:
        messages.success(request, "Metadata update successful")
    else:
        messages.error(request, err_message)

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


res_id = openapi.Parameter(
    "id", openapi.IN_PATH, description="Id of the resource", type=openapi.TYPE_STRING
)


@swagger_auto_schema(
    method="get",
    operation_description="Gets all key/value metadata for the resource",
    responses={200: "key/value metadata"},
    manual_parameters=[res_id],
)
@swagger_auto_schema(
    method="post",
    operation_description="Updates key/value metadata for the resource",
    responses={200: ""},
    manual_parameters=[res_id],
)
@api_view(["POST", "GET"])
def update_key_value_metadata_public(request, id):
    """
    Update resource key/value metadata pair

    Metadata to be updated should be included as key/value pairs in the REST request

    :param request:
    :param id: id of the resource to be updated
    :return: HttpResponse with status code
    """
    if request.method == "GET":
        res, _, _ = authorize(
            request, id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
        )
        return HttpResponse(status=200, content=json.dumps(res.extra_metadata))

    res, _, _ = authorize(
        request, id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )

    post_data = request.data.copy()
    res.extra_metadata = post_data

    is_update_success = True

    try:
        res.save()
    except Error:
        is_update_success = False

    if is_update_success:
        resource_modified(res, request.user, overwrite_bag=False)

    if is_update_success:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)


def add_metadata_element(request, shortkey, element_name, *args, **kwargs):
    """This function is normally for adding/creating new resource level metadata elements.
    However, for the metadata element 'subject' (keyword) this function allows for creating,
    updating and deleting metadata elements.
    """
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )

    is_add_success = False
    err_msg = "Failed to create metadata element '{}'. {}."
    element = None
    sender_resource = _get_resource_sender(element_name, res)
    if element_name.lower() == "subject" and len(request.POST["value"]) == 0:
        # seems the user wants to delete all keywords - no need for pre-check in signal handler
        if res.raccess.published:
            err_msg = err_msg.format(
                element_name, "Published resource needs to have at least one subject"
            )
        else:
            res.metadata.subjects.all().delete()
            is_add_success = True
            res.update_public_and_discoverable()
            resource_modified(res, request.user, overwrite_bag=False)
    else:
        handler_response = signals.pre_metadata_element_create.send(
            sender=sender_resource, element_name=element_name, request=request
        )
        for receiver, response in handler_response:
            if "is_valid" in response:
                if response["is_valid"]:
                    element_data_dict = response["element_data_dict"]
                    if element_name == "subject":
                        # using set() to remove any duplicate keywords
                        keywords = set(
                            [k.strip() for k in element_data_dict["value"].split(",")]
                        )
                        keyword_maxlength = Subject._meta.get_field("value").max_length
                        keywords_to_add = []
                        for kw in keywords:
                            if len(kw) > keyword_maxlength:
                                kw = kw[:keyword_maxlength]

                            # skip any duplicate keywords (case insensitive)
                            if (
                                kw not in keywords_to_add
                                and kw.lower() not in keywords_to_add
                            ):
                                keywords_to_add.append(kw)

                        if len(keywords_to_add) > 0:
                            res.metadata.subjects.all().delete()
                            for kw in keywords_to_add:
                                res.metadata.create_element(element_name, value=kw)
                        is_add_success = True
                    else:
                        try:
                            element = res.metadata.create_element(
                                element_name, **element_data_dict
                            )
                            res.refresh_from_db()
                            is_add_success = True
                        except ValidationError as exp:
                            err_msg = err_msg.format(element_name, str(exp))
                            request.session["validation_error"] = err_msg
                            logger.warning(err_msg)
                        except Error as exp:
                            # some database error occurred
                            err_msg = err_msg.format(element_name, str(exp))
                            request.session["validation_error"] = err_msg
                            logger.warning(err_msg)
                        except Exception as exp:
                            # some other error occurred
                            err_msg = err_msg.format(element_name, str(exp))
                            request.session["validation_error"] = err_msg
                            logger.warning(err_msg)

                    if is_add_success:
                        resource_modified(res, request.user, overwrite_bag=False)
                elif "errors" in response:
                    err_msg = err_msg.format(element_name, response["errors"])

    if request.is_ajax():
        if is_add_success:
            res_public_status = "public" if res.raccess.public else "not public"
            res_discoverable_status = (
                "discoverable" if res.raccess.discoverable else "not discoverable"
            )
            if res.can_be_public_or_discoverable:
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT

            if element_name == "subject":
                ajax_response_data = {
                    "status": "success",
                    "element_name": element_name,
                    "metadata_status": metadata_status,
                    "res_public_status": res_public_status,
                    "res_discoverable_status": res_discoverable_status,
                }
            else:
                ajax_response_data = {
                    "status": "success",
                    "element_type": getattr(element, 'type', None),
                    "element_name": element_name,
                    "spatial_coverage": get_coverage_data_dict(res),
                    "temporal_coverage": get_coverage_data_dict(res, "temporal"),
                    "has_logical_temporal_coverage": res.has_logical_temporal_coverage,
                    "has_logical_spatial_coverage": res.has_logical_spatial_coverage,
                    "metadata_status": metadata_status,
                    "res_public_status": res_public_status,
                    "res_discoverable_status": res_discoverable_status,
                }
                if element is not None:
                    ajax_response_data["element_id"] = element.id

            ajax_response_data["is_dirty"] = (
                res.metadata.is_dirty if hasattr(res.metadata, "is_dirty") else False
            )

            return JsonResponse(ajax_response_data)
        else:
            ajax_response_data = {"status": "error", "message": err_msg}
            return JsonResponse(ajax_response_data)

    if "resource-mode" in request.POST:
        request.session["resource-mode"] = "edit"

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def get_resource_metadata(request, shortkey, *args, **kwargs):
    """Returns resource level metadata that is needed to update UI
    Only the following resource level metadata is returned for now:
    title
    abstract
    keywords
    creators
    spatial coverage
    temporal coverage
    """
    resource, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    res_metadata = dict()
    res_metadata["title"] = resource.metadata.title.value
    description = resource.metadata.description
    if description:
        res_metadata["abstract"] = description.abstract
    else:
        res_metadata["abstract"] = None
    creators = []
    for creator in resource.metadata.creators.all():
        creators.append(model_to_dict(creator))
    res_metadata["creators"] = creators
    res_metadata["keywords"] = [sub.value for sub in resource.metadata.subjects.all()]
    res_metadata["spatial_coverage"] = get_coverage_data_dict(resource)
    res_metadata["temporal_coverage"] = get_coverage_data_dict(
        resource, coverage_type="temporal"
    )
    return JsonResponse(res_metadata, status=200)


def update_metadata_element(
    request, shortkey, element_name, element_id, *args, **kwargs
):
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    sender_resource = _get_resource_sender(element_name, res)
    handler_response = signals.pre_metadata_element_update.send(
        sender=sender_resource,
        element_name=element_name,
        element_id=element_id,
        request=request,
    )
    is_update_success = False
    err_msg = "Failed to update metadata element '{}'. {}."
    for receiver, response in handler_response:
        if "is_valid" in response:
            if response["is_valid"]:
                element_data_dict = response["element_data_dict"]
                try:
                    res.metadata.update_element(
                        element_name, element_id, **element_data_dict
                    )
                    res.refresh_from_db()
                    post_handler_response = signals.post_metadata_element_update.send(
                        sender=sender_resource,
                        element_name=element_name,
                        element_id=element_id,
                    )
                    is_update_success = True
                    # this is how we handle if a post_metadata_element_update receiver
                    # is not implemented in the resource type's receivers.py
                    element_exists = True
                    for receiver, response in post_handler_response:
                        if "element_exists" in response:
                            element_exists = response["element_exists"]

                except ValidationError as exp:
                    err_msg = err_msg.format(element_name, exp.message)
                    request.session["validation_error"] = err_msg
                    logger.warning(err_msg)
                except Error as exp:
                    # some database error occurred
                    err_msg = err_msg.format(element_name, str(exp))
                    request.session["validation_error"] = err_msg
                    logger.warning(err_msg)
                # TODO: it's brittle to embed validation logic at this level.
                if element_name == "title":
                    res.update_public_and_discoverable()
                if is_update_success:
                    resource_modified(res, request.user, overwrite_bag=False)
            elif "errors" in response:
                err_msg = err_msg.format(element_name, response["errors"])

    if request.is_ajax():
        if is_update_success:
            res_public_status = "public" if res.raccess.public else "not public"
            res_discoverable_status = (
                "discoverable" if res.raccess.discoverable else "not discoverable"
            )
            if res.can_be_public_or_discoverable:
                metadata_status = METADATA_STATUS_SUFFICIENT
            else:
                metadata_status = METADATA_STATUS_INSUFFICIENT
            if (
                element_name.lower() == "site"
                and res.resource_type == "CompositeResource"
            ):
                # get the spatial coverage element
                spatial_coverage_dict = get_coverage_data_dict(res)
                ajax_response_data = {
                    "status": "success",
                    "element_name": element_name,
                    "spatial_coverage": spatial_coverage_dict,
                    "has_logical_temporal_coverage": res.has_logical_temporal_coverage,
                    "has_logical_spatial_coverage": res.has_logical_spatial_coverage,
                    "metadata_status": metadata_status,
                    "res_public_status": res_public_status,
                    "res_discoverable_status": res_discoverable_status,
                    "element_exists": element_exists,
                }
            else:
                ajax_response_data = {
                    "status": "success",
                    "element_name": element_name,
                    "metadata_status": metadata_status,
                    "res_public_status": res_public_status,
                    "res_discoverable_status": res_discoverable_status,
                    "element_exists": element_exists,
                }

            ajax_response_data["is_dirty"] = (
                res.metadata.is_dirty if hasattr(res.metadata, "is_dirty") else False
            )

            return JsonResponse(ajax_response_data)
        else:
            ajax_response_data = {"status": "error", "message": err_msg}
            return JsonResponse(ajax_response_data)

    if "resource-mode" in request.POST:
        request.session["resource-mode"] = "edit"

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@swagger_auto_schema(method="get", auto_schema=None)
@api_view(["GET"])
def file_download_url_mapper(request, shortkey):
    """maps the file URIs in resourcemap document to django_irods download view function"""
    try:
        res, _, _ = authorize(
            request,
            shortkey,
            needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
            raises_exception=False,
        )
    except ObjectDoesNotExist:
        return HttpResponse("resource not found", status=status.HTTP_404_NOT_FOUND)
    except PermissionDenied:
        return HttpResponse(
            "access not authorized", status=status.HTTP_401_UNAUTHORIZED
        )

    path_split = request.path.split("/")[2:]  # strip /resource/
    public_file_path = "/".join(path_split)

    istorage = res.get_irods_storage()
    url_download = (
        True if request.GET.get("url_download", "false").lower() == "true" else False
    )
    zipped = True if request.GET.get("zipped", "false").lower() == "true" else False
    aggregation = (
        True if request.GET.get("aggregation", "false").lower() == "true" else False
    )
    return HttpResponseRedirect(
        istorage.url(public_file_path, url_download, zipped, aggregation)
    )


def delete_metadata_element(
    request, shortkey, element_name, element_id, *args, **kwargs
):
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )

    res.metadata.delete_element(element_name, element_id)
    res.refresh_from_db()
    res.update_public_and_discoverable()
    resource_modified(res, request.user, overwrite_bag=False)
    request.session["resource-mode"] = "edit"
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def delete_author(request, shortkey, element_id, *args, **kwargs):
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    try:
        res.metadata.delete_element("creator", element_id)
        resource_modified(res, request.user, overwrite_bag=False)
        ajax_response_data = {
            "status": "success",
            "message": "Author was deleted successfully",
        }
    except Error as exp:
        ajax_response_data = {"status": "error", "message": str(exp)}
    return JsonResponse(ajax_response_data)


def delete_file(request, shortkey, f, *args, **kwargs):
    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    try:
        hydroshare.delete_resource_file(shortkey, f, user)  # calls resource_modified
    except ValidationError as err:
        request.session["validation_error"] = str(err)
        logger.warning(str(err))
    finally:
        request.session["resource-mode"] = "edit"

    if res.can_be_public_or_discoverable:
        request.session["meta-status"] = METADATA_STATUS_SUFFICIENT
    else:
        request.session["meta-status"] = METADATA_STATUS_INSUFFICIENT

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def delete_multiple_files(request, shortkey, *args, **kwargs):
    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE
    )
    # file_ids is a string of file ids separated by comma
    f_ids = request.POST["file_ids"]
    f_id_list = f_ids.split(",")
    for f_id in f_id_list:
        f_id = f_id.strip()
        try:
            hydroshare.delete_resource_file(
                shortkey, f_id, user
            )  # calls resource_modified
        except ValidationError as err:
            request.session["resource-mode"] = "edit"
            request.session["validation_error"] = str(err)
            logger.warning(str(err))
            return HttpResponseRedirect(request.META["HTTP_REFERER"])
        except ObjectDoesNotExist as ex:
            # Since some specific resource types such as feature resource type delete all other
            # dependent content files together when one file is deleted, we make this specific
            # ObjectDoesNotExist exception as legitimate in delete_multiple_files() without
            # raising this specific exception
            logger.warning(str(ex))
            continue

    request.session["resource-mode"] = "edit"

    if res.can_be_public_or_discoverable:
        request.session["meta-status"] = METADATA_STATUS_SUFFICIENT
    else:
        request.session["meta-status"] = METADATA_STATUS_INSUFFICIENT

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def delete_resource(request, shortkey, usertext, *args, **kwargs):
    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE
    )
    if usertext != "DELETE":
        return HttpResponse(
            "'usertext' path parameter must be provided with value 'DELETE'",
            status=status.HTTP_400_BAD_REQUEST,
        )
    if res.metadata.relations.all().filter(type=RelationTypes.isReplacedBy).exists():
        return HttpResponse(
            "An obsoleted resource in the middle of the obsolescence chain cannot be deleted.",
            status=status.HTTP_400_BAD_REQUEST,
        )

    res_title = res.metadata.title
    if request.is_ajax():
        task_id = get_resource_delete_task(shortkey)
        if not task_id:
            # make resource being deleted not discoverable to inform solr to remove this resource from solr index
            # deletion of a discoverable resource corrupts SOLR.
            # Fix by making the resource undiscoverable.
            # This has the side-effect of deleting the resource from SOLR.
            res.set_discoverable(False)
            res.extra_data["to_be_deleted"] = True
            res.save()
            task = delete_resource_task.apply_async((shortkey, user.username))
            task_id = task.task_id
        task_dict = get_or_create_task_notification(
            task_id, name="resource delete", payload=shortkey, username=user.username
        )
        signals.pre_delete_resource.send(
            sender=type(res),
            request=request,
            user=user,
            resource_shortkey=shortkey,
            resource=res,
            resource_title=res_title,
            resource_type=res.resource_type,
            **kwargs,
        )
        return JsonResponse(task_dict)
    else:
        try:
            # make resource being deleted not discoverable to inform solr to remove this resource from solr index
            res.set_discoverable(False)
            hydroshare.delete_resource(shortkey, request_username=request.user.username)
            signals.pre_delete_resource.send(
                sender=type(res),
                request=request,
                user=user,
                resource_shortkey=shortkey,
                resource=res,
                resource_title=res_title,
                resource_type=res.resource_type,
                **kwargs,
            )
            return HttpResponseRedirect("/my-resources/")
        except ValidationError as ex:
            request.session["validation_error"] = str(ex)
            logger.warning(str(ex))
            return HttpResponseRedirect(request.META["HTTP_REFERER"])


def rep_res_bag_to_irods_user_zone(request, shortkey, *args, **kwargs):
    """
    This function needs to be called via AJAX. The function replicates resource bag to iRODS user zone on
    users.hydroshare.org which is federated with hydroshare zone under the iRODS user account corresponding to a
    HydroShare user. This function should only be called or exposed to be called from web interface when a
    corresponding iRODS user account on hydroshare user Zone exists. The purpose of this function is to allow
    HydroShare resource bag that a HydroShare user has access to be copied to HydroShare user's iRODS space in
    HydroShare user zone so that users can do analysis or computations on the resource
    Args:
        request: an AJAX request
        shortkey: UUID of the resource to be copied to the login user's iRODS user space

    Returns:
        JSON list that indicates status of resource replication, i.e., success or error
    """

    res, authorized, user = authorize(
        request,
        shortkey,
        needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
        raises_exception=False,
    )
    if not authorized:
        return JsonResponse(
            {"error": "You are not authorized to replicate this resource."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    task = replicate_resource_bag_to_user_zone_task.apply_async(
        (shortkey, user.username)
    )
    task_id = task.task_id
    task_dict = get_or_create_task_notification(
        task_id, name="resource copy to user zone", username=user.username
    )
    return JsonResponse(task_dict)


def list_referenced_content(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    # subfolders could be named contents
    return JsonResponse(
        {
            "filenames": [
                x.url.split("contents", 1)[-1]
                for x in list(res.logical_files)
                if "url" in x.extra_data
            ]
        }
    )


def copy_resource(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    if request.is_ajax():
        task = copy_resource_task.apply_async((shortkey, None, user.username))
        task_id = task.task_id
        task_dict = get_or_create_task_notification(
            task_id, name="resource copy", payload=shortkey, username=user.username
        )
        return JsonResponse(task_dict)
    else:
        try:
            response_url = copy_resource_task(
                shortkey, new_res_id=None, request_username=user.username
            )
            return HttpResponseRedirect(response_url)
        except hydroshare.utils.ResourceCopyException:
            return HttpResponseRedirect(res.get_absolute_url())


res_id = openapi.Parameter(
    "id",
    openapi.IN_PATH,
    description="Id of the resource to be copied",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="post",
    operation_description="Copy a resource",
    responses={202: "Returns the resource ID of the newly created resource"},
    manual_parameters=[res_id],
)
@api_view(["POST"])
def copy_resource_public(request, pk):
    """
    Copy a resource

    :param request:
    :param pk: id of the resource to be copied
    """
    response = copy_resource(request, pk)
    return HttpResponse(response.url.split("/")[2], status=202)


def create_new_version_resource(request, shortkey, *args, **kwargs):
    res, authorized, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.CREATE_RESOURCE_VERSION
    )
    if res.locked_time:
        # cannot create new version for this resource since the resource is locked by another
        # user
        request.session["resource_creation_error"] = (
            "Failed to create a new version for "
            "this resource since another user is "
            "creating a new version for this "
            "resource synchronously."
        )
        return HttpResponseRedirect(res.get_absolute_url())
    # lock the resource to prevent concurrent new version creation since only one new version for an
    # obsoleted resource is allowed
    res.locked_time = datetime.datetime.now(tz.UTC)
    res.save()
    if request.is_ajax():
        task = create_new_version_resource_task.apply_async((shortkey, user.username))
        task_id = task.task_id
        task_dict = get_or_create_task_notification(
            task_id, name="resource version", payload=shortkey, username=user.username
        )
        return JsonResponse(task_dict)
    else:
        try:
            response_url = create_new_version_resource_task(shortkey, user.username)
            return HttpResponseRedirect(response_url)
        except hydroshare.utils.ResourceVersioningException as ex:
            request.session[
                "resource_creation_error"
            ] = "Failed to create a new version of " "this resource: " + str(ex)
            return HttpResponseRedirect(res.get_absolute_url())


res_id = openapi.Parameter(
    "id",
    openapi.IN_PATH,
    description="Id of the resource to be versioned",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="post",
    operation_description="Create a new version of a resource",
    responses={202: "Returns the resource ID of the new version"},
    manual_parameters=[res_id],
)
@api_view(["POST"])
def create_new_version_resource_public(request, pk):
    """
    Create a new version of a resource

    :param request:
    :param pk: id of the resource to be versioned
    :return: HttpResponse with status code
    """
    redirect = create_new_version_resource(request, pk)
    return HttpResponse(redirect.url.split("/")[2], status=202)


def publish(request, shortkey, *args, **kwargs):
    if not request.user.is_superuser:
        raise ValidationError("Resource can only be published by an admin user")
    try:
        hydroshare.publish_resource(request.user, shortkey)
    except ValidationError as exp:
        request.session["validation_error"] = str(exp)
        logger.warning(str(exp))
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def submit_for_review(request, shortkey, *args, **kwargs):
    # only resource owners are allowed to submit for review
    res, _, _ = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG
    )

    missing = res.metadata.get_required_missing_elements("published")
    if missing:
        message = f"""This resource doesn't meet the minimum metadata standards for publication
                and adherence to community guidelines. {' '.join(missing)}
                """
        messages.error(request, message)
        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    try:
        hydroshare.submit_resource_for_review(request, shortkey)
    except ValidationError as exp:
        request.session["validation_error"] = str(exp)
        logger.warning(str(exp))
    else:
        message = """Congratulations!
                Your resource is under review for appropriate minimum metadata and to ensure that it adheres to
                community guidelines.
                The review process will likely be complete within 1 business day, but not exceed 2 business days.
                You will receive a notification via email once the review process has concluded.
                If you decide that you no longer wish to have this resource reviewed for publication,
                please contact help@cuahsi.org"""
        messages.success(request, message)
    return HttpResponseRedirect(request.META["HTTP_REFERER"])


def set_resource_flag(request, shortkey, *args, **kwargs):
    # only resource owners are allowed to change resource flags
    ajax_response_data = {"status": "error", "message": ""}
    flag = resolve_request(request).get("flag", None)
    res, authorized, user = authorize(
        request,
        shortkey,
        needed_permission=ACTION_TO_AUTHORIZE.SET_RESOURCE_FLAG,
        raises_exception=False,
    )
    if not authorized:
        # for published resource above authorize call will return false
        # need to then check permission to change shareable flag
        if flag in ("make_shareable", "make_not_shareable"):
            if not user.uaccess.can_change_resource_shareable_flag(res):
                raise PermissionDenied
        else:
            raise PermissionDenied

    message = None

    if flag == "make_public":
        message = _set_resource_sharing_status(
            user, res, flag_to_set="public", flag_value=True
        )
    elif flag == "make_private" or flag == "make_not_discoverable":
        message = _set_resource_sharing_status(
            user, res, flag_to_set="discoverable", flag_value=False
        )
    elif flag == "make_discoverable":
        message = _set_resource_sharing_status(
            user, res, flag_to_set="discoverable", flag_value=True
        )
    elif flag == "make_not_shareable":
        message = _set_resource_sharing_status(
            user, res, flag_to_set="shareable", flag_value=False
        )
    elif flag == "make_shareable":
        message = _set_resource_sharing_status(
            user, res, flag_to_set="shareable", flag_value=True
        )
    elif flag == "make_require_lic_agreement":
        res.set_require_download_agreement(user, value=True)
    elif flag == "make_not_require_lic_agreement":
        res.set_require_download_agreement(user, value=False)
    elif flag == "enable_private_sharing_link":
        res.set_private_sharing_link(user, value=True)
    elif flag == "remove_private_sharing_link":
        res.set_private_sharing_link(user, value=False)
    else:
        message = "Invalid resource flag"
    if message is not None:
        ajax_response_data["message"] = message
    else:
        ajax_response_data["status"] = "success"

    return JsonResponse(ajax_response_data)


res_id = openapi.Parameter(
    "id",
    openapi.IN_PATH,
    description="Id of the resource to be flagged",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="post",
    operation_description="Set resource flag to 'Public'",
    responses={202: "Returns the resource ID of the new version"},
    manual_parameters=[res_id],
)
@api_view(["POST"])
def set_resource_flag_public(request, pk):
    """
    Set resource flag to "Public"

    :param request:
    :param pk: id of the resource to be modified
    :return: HttpResponse with status code
    """
    http_request = request._request
    http_request.data = request.data.copy()
    js_response = set_resource_flag(http_request, pk)
    data = json.loads(js_response.content)
    if data["status"] == "error":
        return HttpResponse(data["message"], status=400)
    return HttpResponse(status=202)


def share_resource_with_user(request, shortkey, privilege, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""
    return _share_resource(request, shortkey, privilege, user_id, user_or_group="user")


def share_resource_with_group(request, shortkey, privilege, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""
    return _share_resource(
        request, shortkey, privilege, group_id, user_or_group="group"
    )


def _share_resource(request, shortkey, privilege, user_or_group_id, user_or_group):
    """
    share resource with a user or group
    :param request:
    :param shortkey: id of the resource to share with
    :param privilege: access privilege need for the resource
    :param user_or_group_id: id of the user or group with whom the resource to be shared
    :param user_or_group: indicates if the resource to be shared with a user or group. A value of 'user' will share
                          the resource with a user whose id is provided with the parameter 'user_or_group_id'.
                          Any other value for this parameter assumes resource to be shared with a group.
    :return:
    """

    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    user_to_share_with = None
    group_to_share_with = None
    status_code = 200
    if user_or_group == "user":
        user_to_share_with = hydroshare.utils.user_from_id(user_or_group_id)
    else:
        group_to_share_with = hydroshare.utils.group_from_id(user_or_group_id)

    status = "success"
    err_message = ""
    if privilege == "view":
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == "edit":
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == "owner":
        if user_or_group != "user":
            status_code = 400
            err_message = "Group can't have owner privilege over a resource"
            access_privilege = PrivilegeCodes.NONE
        else:
            access_privilege = PrivilegeCodes.OWNER
    else:
        status_code = 400
        err_message = "Not a valid privilege"
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        try:
            if user_or_group == "user":
                user.uaccess.share_resource_with_user(
                    res, user_to_share_with, access_privilege
                )
            else:
                user.uaccess.share_resource_with_group(
                    res, group_to_share_with, access_privilege
                )
        except PermissionDenied as exp:
            status = "error"
            err_message = str(exp)
    else:
        status = "error"

    from hs_core.models import get_access_object

    if user_or_group == "user":
        user_can_undo = request.user.uaccess.can_undo_share_resource_with_user(
            res, user_to_share_with
        )
        user_to_share_with.can_undo = user_can_undo

        ajax_response_data = {
            "status": status,
            "error_msg": err_message,
            "user": get_access_object(user_to_share_with, "user", privilege),
        }
    else:
        group_can_undo = request.user.uaccess.can_undo_share_resource_with_group(
            res, group_to_share_with
        )
        group_to_share_with.can_undo = group_can_undo

        ajax_response_data = {
            "status": status,
            "error_msg": err_message,
            "user": get_access_object(group_to_share_with, "group", privilege),
        }

    return HttpResponse(json.dumps(ajax_response_data), status=status_code)


def unshare_resource_with_user(request, shortkey, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    user_to_unshare_with = hydroshare.utils.user_from_id(user_id)
    ajax_response_data = {"status": "success"}
    try:
        user.uaccess.unshare_resource_with_user(res, user_to_unshare_with)
        if user not in res.raccess.view_users:
            # user has no explict access to the resource - redirect to resource listing page
            ajax_response_data["redirect_to"] = "/my-resources/"

    except PermissionDenied as exp:
        ajax_response_data["status"] = "error"
        ajax_response_data["message"] = str(exp)

    return JsonResponse(ajax_response_data)


def unshare_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    group_to_unshare_with = hydroshare.utils.group_from_id(group_id)
    ajax_response_data = {"status": "success"}
    try:
        user.uaccess.unshare_resource_with_group(res, group_to_unshare_with)
        if user not in res.raccess.view_users:
            # user has no explicit access to the resource - redirect to resource listing page
            ajax_response_data["redirect_to"] = "/my-resources/"
    except PermissionDenied as exp:
        ajax_response_data["status"] = "error"
        ajax_response_data["message"] = str(exp)

    return JsonResponse(ajax_response_data)


def undo_share_resource_with_user(request, shortkey, user_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    user_to_unshare_with = hydroshare.utils.user_from_id(user_id)
    ajax_response_data = {"status": "success"}
    try:
        user.uaccess.undo_share_resource_with_user(res, user_to_unshare_with)
        undo_user_privilege = res.raccess.get_effective_privilege(user_to_unshare_with)
        if undo_user_privilege == PrivilegeCodes.VIEW:
            undo_user_privilege = "view"
        elif undo_user_privilege == PrivilegeCodes.CHANGE:
            undo_user_privilege = "edit"
        elif undo_user_privilege == PrivilegeCodes.OWNER:
            undo_user_privilege = "owner"
        else:
            undo_user_privilege = "none"
        ajax_response_data["undo_user_privilege"] = undo_user_privilege

        if user not in res.raccess.view_users:
            # user has no explict access to the resource - redirect to resource listing page
            ajax_response_data["redirect_to"] = "/my-resources/"

    except PermissionDenied as exp:
        ajax_response_data["status"] = "error"
        ajax_response_data["message"] = str(exp)

    return JsonResponse(ajax_response_data)


def undo_share_resource_with_group(request, shortkey, group_id, *args, **kwargs):
    """this view function is expected to be called by ajax"""

    res, _, user = authorize(
        request, shortkey, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE
    )
    group_to_unshare_with = hydroshare.utils.group_from_id(group_id)
    ajax_response_data = {"status": "success"}
    try:
        user.uaccess.undo_share_resource_with_group(res, group_to_unshare_with)
        if group_to_unshare_with in res.raccess.edit_groups:
            undo_group_privilege = "edit"
        elif group_to_unshare_with in res.raccess.view_groups:
            undo_group_privilege = "view"
        else:
            undo_group_privilege = "none"
        ajax_response_data["undo_group_privilege"] = undo_group_privilege

        if user not in res.raccess.view_users:
            # user has no explicit access to the resource - redirect to resource listing page
            ajax_response_data["redirect_to"] = "/my-resources/"
    except PermissionDenied as exp:
        ajax_response_data["status"] = "error"
        ajax_response_data["message"] = str(exp)

    return JsonResponse(ajax_response_data)


def verify_account(request, *args, **kwargs):
    context = {"username": request.GET["username"], "email": request.GET["email"]}
    return render(request, "pages/verify-account.html", context)


@processor_for("resend-verification-email")
def resend_verification_email(request):
    u = get_object_or_404(
        User, username=request.GET["username"], email=request.GET["email"]
    )
    try:
        token = signing.dumps("verify_user_email:{0}:{1}".format(u.pk, u.email))
        u.email_user(
            "Please verify your new Hydroshare account.",
            """
This is an automated email from Hydroshare.org. If you requested a Hydroshare account, please
go to http://{domain}/verify/{token}/ and verify your account.
""".format(
                domain=Site.objects.get_current().domain, token=token
            ),
        )

        context = {"is_email_sent": True}
        return render(request, "pages/verify-account.html", context)
    except: # noqa
        pass  # FIXME should log this instead of ignoring it.


class FilterForm(forms.Form):
    start = forms.IntegerField(required=False)
    published = forms.BooleanField(required=False)
    edit_permission = forms.BooleanField(required=False)
    owner = forms.CharField(required=False)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    from_date = forms.DateTimeField(required=False)


class GroupForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)
    purpose = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    url = forms.URLField(required=False)
    picture = ThumbnailImageField()
    privacy_level = forms.CharField(required=True)
    auto_approve = forms.BooleanField(required=False)
    requires_explanation = forms.BooleanField(required=False)

    def clean_privacy_level(self):
        data = self.cleaned_data["privacy_level"]
        if data not in ("public", "private", "discoverable"):
            raise forms.ValidationError("Invalid group privacy level.")
        return data

    def _set_privacy_level(self, group, privacy_level):
        if privacy_level == "public":
            group.gaccess.public = True
            group.gaccess.discoverable = True
        elif privacy_level == "private":
            group.gaccess.public = False
            group.gaccess.discoverable = False
        elif privacy_level == "discoverable":
            group.gaccess.discoverable = True
            group.gaccess.public = False

        group.gaccess.save()


class GroupCreateForm(GroupForm):
    def save(self, request):
        frm_data = self.cleaned_data

        new_group = request.user.uaccess.create_group(title=frm_data["name"],
                                                      description=frm_data["description"],
                                                      purpose=frm_data["purpose"],
                                                      email=frm_data["email"],
                                                      url=frm_data["url"],
                                                      auto_approve=frm_data["auto_approve"],
                                                      requires_explanation=frm_data["requires_explanation"]
                                                      )
        if 'picture' in request.FILES:
            # resize uploaded image
            img = request.FILES["picture"]
            img.image = get_thumbnail(img, "x150", crop="center")
            new_group.gaccess.picture = img

        privacy_level = frm_data["privacy_level"]
        self._set_privacy_level(new_group, privacy_level)
        return new_group


class GroupUpdateForm(GroupForm):
    def update(self, group_to_update, request):
        frm_data = self.cleaned_data
        group_to_update.name = frm_data["name"]
        group_to_update.save()
        group_to_update.gaccess.description = frm_data["description"]
        group_to_update.gaccess.purpose = frm_data["purpose"]
        group_to_update.gaccess.email = frm_data["email"]
        group_to_update.gaccess.url = frm_data["url"]
        group_to_update.gaccess.auto_approve = frm_data["auto_approve"]
        group_to_update.gaccess.requires_explanation = frm_data["requires_explanation"]
        if "picture" in request.FILES:
            # resize uploaded image
            img = request.FILES["picture"]
            img.image = get_thumbnail(img, "x150", crop="center")
            group_to_update.gaccess.picture = img

        privacy_level = frm_data["privacy_level"]
        self._set_privacy_level(group_to_update, privacy_level)


class PatchedChoiceWidget(autocomplete_light.ChoiceWidget):
    """Patching the render() function of ChoiceWidget class to work with Django 3.2"""

    def __init__(
        self,
        autocomplete=None,
        widget_js_attributes=None,
        autocomplete_js_attributes=None,
        extra_context=None,
        registry=None,
        widget_template=None,
        widget_attrs=None,
        *args,
        **kwargs,
    ):
        super(PatchedChoiceWidget, self).__init__(
            autocomplete,
            widget_js_attributes,
            autocomplete_js_attributes,
            extra_context,
            registry,
            widget_template,
            widget_attrs,
            *args,
            **kwargs,
        )

    def render(self, name, value, attrs=None, renderer=None):
        """Adding the 'renderer' parameter to fix the exception
        'render() got an unexpected keyword argument 'renderer'"""

        return super(PatchedChoiceWidget, self).render(name, value, attrs)


@processor_for(BaseResource)
def add_generic_context(request, page):
    user = request.user
    user_zone_account_exist = hydroshare.utils.get_user_zone_status_info(user)

    class AddUserForm(forms.Form):
        user = forms.ModelChoiceField(
            User.objects.filter(is_active=True).all(),
            widget=PatchedChoiceWidget(
                autocomplete="UserAutocomplete", attrs={"id": "user"}
            ),
        )

    class AddUserContriForm(forms.Form):
        user = forms.ModelChoiceField(
            User.objects.filter(is_active=True).all(),
            widget=PatchedChoiceWidget(
                autocomplete="UserAutocomplete", attrs={"id": "user"}
            ),
        )

    class AddUserInviteForm(forms.Form):
        user = forms.ModelChoiceField(
            User.objects.filter(is_active=True).all(),
            widget=PatchedChoiceWidget(
                autocomplete="UserAutocomplete", attrs={"id": "user"}
            ),
        )

    class AddUserHSForm(forms.Form):
        user = forms.ModelChoiceField(
            User.objects.filter(is_active=True).all(),
            widget=PatchedChoiceWidget(
                autocomplete="UserAutocomplete", attrs={"id": "user"}
            ),
        )

    class AddGroupForm(forms.Form):
        group = forms.ModelChoiceField(
            Group.objects.filter(gaccess__active=True)
            .exclude(name="Hydroshare Author")
            .all(),
            widget=PatchedChoiceWidget(autocomplete="GroupAutocomplete"),
        )

    return {
        "add_view_contrib_user_form": AddUserContriForm(),
        "add_view_invite_user_form": AddUserInviteForm(),
        "add_view_hs_user_form": AddUserHSForm(),
        "add_view_user_form": AddUserForm(),
        # Reuse the same class AddGroupForm() leads to duplicated IDs.
        "add_view_group_form": AddGroupForm(),
        "add_edit_group_form": AddGroupForm(),
        "user_zone_account_exist": user_zone_account_exist,
    }


@login_required
def create_resource(request, *args, **kwargs):
    # Note: This view function must be called by ajax

    ajax_response_data = {"status": "error", "message": ""}
    resource_type = request.POST["resource-type"]
    res_title = request.POST["title"]
    resource_files, full_paths = extract_files_with_paths(request)
    auto_aggregate = request.POST.get("auto_aggregate", "true").lower() == "true"

    url_key = "page_redirect_url"
    try:
        _, res_title, metadata = hydroshare.utils.resource_pre_create_actions(
            resource_type=resource_type,
            files=resource_files,
            resource_title=res_title,
            page_redirect_url_key=url_key,
            requesting_user=request.user,
            **kwargs,
        )
    except hydroshare.utils.ResourceFileSizeException as ex:
        ajax_response_data["message"] = str(ex)
        return JsonResponse(ajax_response_data)

    except hydroshare.utils.ResourceFileValidationException as ex:
        ajax_response_data["message"] = str(ex)
        return JsonResponse(ajax_response_data)

    except Exception as ex:
        ajax_response_data["message"] = str(ex)
        return JsonResponse(ajax_response_data)

    try:
        resource = hydroshare.create_resource(
            resource_type=request.POST["resource-type"],
            owner=request.user,
            title=res_title,
            metadata=metadata,
            files=resource_files,
            content=res_title,
            full_paths=full_paths,
            auto_aggregate=auto_aggregate,
        )
    except SessionException as ex:
        ajax_response_data["message"] = ex.stderr
        return JsonResponse(ajax_response_data)
    except Exception as ex:
        ajax_response_data["message"] = str(ex)
        return JsonResponse(ajax_response_data)

    try:
        hydroshare.utils.resource_post_create_actions(
            request=request,
            resource=resource,
            user=request.user,
            metadata=metadata,
            **kwargs,
        )
    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session["validation_error"] = str(ex)
        ajax_response_data["message"] = str(ex)
        ajax_response_data["status"] = "success"
        ajax_response_data["file_upload_status"] = "error"
        ajax_response_data["resource_url"] = resource.get_absolute_url()
        return JsonResponse(ajax_response_data)

    request.session["just_created"] = True
    if not ajax_response_data["message"]:
        if resource.files.all():
            ajax_response_data["file_upload_status"] = "success"
        ajax_response_data["status"] = "success"
        ajax_response_data["resource_url"] = resource.get_absolute_url()

    return JsonResponse(ajax_response_data)


@login_required
def create_user_group(request, *args, **kwargs):
    group_form = GroupCreateForm(request.POST, request.FILES)
    if group_form.is_valid():
        try:
            new_group = group_form.save(request)
            messages.success(request, "Group creation was successful.")
            return HttpResponseRedirect(reverse("group", args=[new_group.id]))
        except IntegrityError as ex:
            if group_form.cleaned_data["name"] in str(ex):
                message = "Group name '{}' already exists".format(
                    group_form.cleaned_data["name"]
                )
                messages.error(request, "Group creation errors: {}.".format(message))
            else:
                messages.error(request, "Group creation errors:{}.".format(str(ex)))
    else:
        messages.error(
            request, "Group creation errors:{}.".format(group_form.errors.as_json)
        )

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def update_user_community(request, community_id, *args, **kwargs):
    """Updates metadata for a community"""

    community_to_update = hydroshare.utils.community_from_id(community_id)

    community_form = UpdateCommunityForm(request.POST, request.FILES)
    if community_form.is_valid():
        try:
            community_form.update(community_to_update, request)
            messages.success(request, "Community update was successful.")
        except PermissionDenied:
            err_msg = "You don't have permission to update community"
            messages.error(request, err_msg)
        except Exception as ex:
            messages.error(request, f"Community update errors:{str(ex)}.")

    else:
        messages.error(request, "Community update errors:{}.".format(community_form.errors.as_json))

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def update_user_group(request, group_id, *args, **kwargs):
    user = request.user
    group_to_update = hydroshare.utils.group_from_id(group_id)

    if user.uaccess.can_change_group_flags(group_to_update):
        group_form = GroupUpdateForm(request.POST, request.FILES)
        if group_form.is_valid():
            try:
                group_form.update(group_to_update, request)
                messages.success(request, "Group update was successful.")
            except IntegrityError as ex:
                if group_form.cleaned_data["name"] in str(ex):
                    message = "Group name '{}' already exists".format(
                        group_form.cleaned_data["name"]
                    )
                    messages.error(request, "Group update errors: {}.".format(message))
                else:
                    messages.error(request, "Group update errors:{}.".format(str(ex)))
        else:
            messages.error(
                request, "Group update errors:{}.".format(group_form.errors.as_json)
            )
    else:
        messages.error(
            request,
            "Group update errors: You don't have permission to update this group",
        )

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def delete_user_group(request, group_id, *args, **kwargs):
    """This one is not really deleting the group object, rather setting the active status
    to False (delete) which can be later restored (undelete) )"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, False)
        messages.success(request, "Group delete was successful.")
    except PermissionDenied:
        messages.error(
            request,
            "Group delete errors: You don't have permission to delete" " this group.",
        )

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def restore_user_group(request, group_id, *args, **kwargs):
    """This one is for setting the active status of the group back to True"""
    try:
        hydroshare.set_group_active_status(request.user, group_id, True)
        messages.success(request, "Group restore was successful.")
    except PermissionDenied:
        messages.error(
            request,
            "Group restore errors: You don't have permission to restore" " this group.",
        )

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def share_group_with_user(request, group_id, user_id, privilege, *args, **kwargs):
    requesting_user = request.user
    group_to_share = hydroshare.utils.group_from_id(group_id)
    user_to_share_with = hydroshare.utils.user_from_id(user_id)
    if privilege == "view":
        access_privilege = PrivilegeCodes.VIEW
    elif privilege == "edit":
        access_privilege = PrivilegeCodes.CHANGE
    elif privilege == "owner":
        access_privilege = PrivilegeCodes.OWNER
    else:
        access_privilege = PrivilegeCodes.NONE

    if access_privilege != PrivilegeCodes.NONE:
        if requesting_user.uaccess.can_share_group(group_to_share, access_privilege):
            try:
                requesting_user.uaccess.share_group_with_user(
                    group_to_share, user_to_share_with, access_privilege
                )
                messages.success(request, "User successfully added to the group")
            except PermissionDenied as ex:
                messages.error(request, str(ex))
        else:
            messages.error(request, "You don't have permission to add users to group")
    else:
        messages.error(request, "Invalid privilege for sharing group with user")

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def unshare_group_with_user(request, group_id, user_id, *args, **kwargs):
    """
    Remove a user from a group

    :param request: group owner who is removing the user from the group
    :param group_id: id of the user being removed from the group
    :param user_id: id of the group from which the user to be removed
    :return:
    """
    requesting_user = request.user
    group_to_unshare = hydroshare.utils.group_from_id(group_id)
    user_to_unshare_with = hydroshare.utils.user_from_id(user_id)

    try:
        requesting_user.uaccess.unshare_group_with_user(
            group_to_unshare, user_to_unshare_with
        )
        if requesting_user == user_to_unshare_with:
            success_msg = "You successfully left the group."
        else:
            success_msg = "User successfully removed from the group."
        messages.success(request, success_msg)
    except PermissionDenied as ex:
        messages.error(request, str(ex))

    if requesting_user == user_to_unshare_with:
        return HttpResponseRedirect(reverse("my_groups"))
    else:
        return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def make_group_membership_request(request, group_id, user_id=None, *args, **kwargs):
    """
    Allows either an owner of the group to invite a user to join a group or a user to make a request
    to join a group
    :param request: the user who is making the request
    :param group_id: ID of the group for which the join request/invitation to me made
    :param user_id: needed only when an owner is inviting a user to join a group. This is the id of the user the owner
                    is inviting
    :return:
    """
    requesting_user = request.user
    group_to_join = hydroshare.utils.group_from_id(group_id)
    user_to_join = None
    if request.method == "POST":
        explanation = request.POST.get("explanation", None)
    else:
        explanation = None
    if user_id is not None:
        user_to_join = hydroshare.utils.user_from_id(user_id)
    try:
        membership_request = requesting_user.uaccess.create_group_membership_request(
            group_to_join, user_to_join, explanation=explanation
        )
        if user_to_join is not None:
            message = "Group membership invitation was successful"
            # send mail to the user who was invited to join group

            send_action_to_take_email(
                request,
                user=user_to_join,
                action_type="group_membership",
                group=group_to_join,
                membership_request=membership_request,
                explanation=explanation,
            )
        else:
            message = "You are now a member of this group"
            # membership_request is None in case where group allows auto approval of membership
            # request. no need send email notification to group owners for membership approval
            if membership_request is not None:
                message = "Group membership request was successful"
                # send mail to all owners of the group for approval of the request
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(
                        request,
                        user=requesting_user,
                        action_type="group_membership",
                        group=group_to_join,
                        group_owner=grp_owner,
                        membership_request=membership_request,
                        explanation=explanation,
                    )
            else:
                # send mail to all owners of the group to let them know that someone has
                # joined this group
                for grp_owner in group_to_join.gaccess.owners:
                    send_action_to_take_email(
                        request,
                        user=requesting_user,
                        action_type="group_auto_membership",
                        group=group_to_join,
                        group_owner=grp_owner,
                        explanation=explanation,
                    )
        return JsonResponse({
            "status": "success",
            "message": message
        })
    except PermissionDenied as ex:
        return JsonResponse({
            "status": "error",
            "message": str(ex),
        })


def group_membership(request, uidb36, token, membership_request_id, **kwargs):
    """
    View for the link in the verification email that was sent to a user
    when they request/invite to join a group.
    User is logged in and the request to join a group is accepted. Then the user is redirected to the group
    profile page of the group for which the membership got accepted.

    :param uidb36: ID of the user to whom the email was sent (part of the link in the email)
    :param token: token that was part of the link in the email
    :param membership_request_id: ID of the GroupMembershipRequest object (part of the link in the email)
    """
    membership_request = GroupMembershipRequest.objects.filter(
        id=membership_request_id
    ).first()
    if membership_request is None:
        messages.error(request, "This group membership link is not valid")
    elif membership_request.redeemed:
        messages.error(
            request, "This group membership link has previously been redeemed"
        )
    elif not membership_request.group_to_join.gaccess.active:
        messages.error(
            request,
            "The group associated with this group membership link is no longer active.",
        )
    else:
        user = authenticate(uidb36=uidb36, token=token, is_active=True)
        if user is None:
            messages.error(
                request,
                "The link you clicked has expired. Please ask to "
                "join the group again.",
            )
        else:
            user.uaccess.act_on_group_membership_request(
                membership_request, accept_request=True
            )
            auth_login(request, user)
            # send email to notify membership acceptance
            _send_email_on_group_membership_acceptance(membership_request)
            if membership_request.invitation_to is not None:
                message = "You just joined the group '{}'".format(
                    membership_request.group_to_join.name
                )
            else:
                message = "User '{}' just joined the group '{}'".format(
                    membership_request.request_from.first_name,
                    membership_request.group_to_join.name,
                )

            messages.info(request, message)
            # redirect to group profile page
            return HttpResponseRedirect(
                "/group/{}/".format(membership_request.group_to_join.id)
            )
    return redirect("/")


def metadata_review(request, shortkey, action, uidb36=None, token=None, **kwargs):
    """
    View for the link in the verification email that was sent to a user
    when they request publication/metadata review.
    User is logged in and the request for review is approved. Then the user is redirected to the resource landing page
    for the resource that they just approved.

    :param uidb36: ID of the user to whom the email was sent (part of the link in the email)
    :param token: token that was part of the link in the email
    """
    if uidb36:
        user = authenticate(uidb36=uidb36, token=token, is_active=True)
        if user is None:
            messages.error(
                request,
                "The link you clicked has expired. Please manually navigate to the resouce "
                "to complete the metadata review.",
            )
    else:
        user = request.user

    res = hydroshare.utils.get_resource_by_shortkey(shortkey)
    if not res.raccess.review_pending:
        messages.error(
            request,
            f"This resource does not have a pending metadata review for you to { action }.",
        )
    else:
        res.raccess.alter_review_pending_flags(initiating_review=False)
        if action == "approve":
            hydroshare.publish_resource(user, shortkey)
            messages.success(
                request,
                "Publication request was accepted. "
                "An email will be sent notifiying the resource owner(s) once the DOI activates.",
            )
        else:
            messages.warning(
                request,
                "Publication request was rejected. Please send an email to the resource owner indicating why.",
            )
        res.metadata.dates.all().filter(type="reviewStarted").delete()
    return HttpResponseRedirect(f"/resource/{ res.short_id }/")


def spam_allowlist(request, shortkey, action, **kwargs):
    """
    Allow a resource to be discoverable even if it matches spam patterns
    """
    user = request.user
    if not user.is_superuser:
        return HttpResponseForbidden(
            "not authorized to perform this action"
        )

    res = hydroshare.utils.get_resource_by_shortkey(shortkey)
    if action == "allow":
        res.spam_allowlisted = True
        res.save()
        messages.success(
            request,
            "Resource has been allowlisted. "
            "This means that it can show in Discover even if it contains spam patterns.",
        )
    else:
        res.spam_allowlisted = False
        res.save()
        messages.warning(
            request,
            "Resource has been removed from allowlist. "
            "It will not show in Discover if it contains spam patterns.",
        )
    # update the index
    signals.post_spam_whitelist_change.send(sender=BaseResource, instance=res)
    return HttpResponseRedirect(f"/resource/{ res.short_id }/")


@login_required
def act_on_group_membership_request(
    request, membership_request_id, action, *args, **kwargs
):
    """
    Take action (accept or decline) on group membership request

    :param request: requesting user is either owner of the group taking action on a request from a user
                    or a user taking action on a invitation to join a group from a group owner
    :param membership_request_id: id of the membership request object (an instance of GroupMembershipRequest)
                                  to act on
    :param action: need to have a value of either 'accept' or 'decline'
    :return:
    """

    accept_request = action == "accept"
    user_acting = request.user

    try:
        membership_request = GroupMembershipRequest.objects.get(
            pk=membership_request_id
        )
    except ObjectDoesNotExist:
        messages.error(request, "No matching group membership request was found")
    else:
        if membership_request.group_to_join.gaccess.active:
            try:
                user_acting.uaccess.act_on_group_membership_request(
                    membership_request, accept_request
                )
                if accept_request:
                    message = "Membership request accepted"
                    messages.success(request, message)
                    # send email to notify membership acceptance
                    _send_email_on_group_membership_acceptance(membership_request)
                else:
                    message = "Membership request declined"
                    messages.success(request, message)

            except PermissionDenied as ex:
                messages.error(request, str(ex))
        else:
            messages.error(request, "Group is not active")

    return HttpResponseRedirect(request.META["HTTP_REFERER"])


@login_required
def get_file(request, *args, **kwargs):
    from django_irods.icommands import Session as RodsSession

    name = kwargs["name"]
    session = RodsSession("./", "/usr/bin")
    session.runCmd("iinit")
    session.runCmd("iget", [name, "tempfile." + name])
    return HttpResponse(open(name), content_type="x-binary/octet-stream")


processor_for(BaseResource)(resource_processor)


def get_metadata_terms_page(request, *args, **kwargs):
    return render(request, "pages/metadata_terms.html")


uid = openapi.Parameter(
    "user_identifier",
    openapi.IN_PATH,
    description="email, username, or id of the user for which data is needed",
    type=openapi.TYPE_STRING,
)


@swagger_auto_schema(
    method="get",
    operation_description="Get user data",
    responses={200: "Returns JsonResponse containing user data"},
    manual_parameters=[uid],
)
@api_view(["GET"])
def hsapi_get_user(request, user_identifier):
    """
    Get user data

    :param user_identifier: id of the user for which data is needed
    :return: JsonResponse containing user data
    """
    return get_user_or_group_data(request, user_identifier, "false")


@swagger_auto_schema(
    method="post",
    operation_description="Check user password for Keycloak Migration",
    responses={200: "Password is valid", 400: "Password is invalid"},
    manual_parameters=[uid],
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT,
                                properties={'password': openapi.Schema(type=openapi.TYPE_STRING,
                                                                       description="raw password to validate")}
                                )
)
@swagger_auto_schema(
    method="get",
    operation_description="Get user data for Keycloak Migration",
    responses={200: "Returns JsonResponse containing user data"},
    manual_parameters=[uid],
)
@api_view(["GET", "POST"])
def hsapi_get_user_for_keycloak(request, user_identifier):
    """
    Get user data

    :param user_identifier: id of the user for which data is needed
    :return: JsonResponse containing user data
    """

    if not request.user.is_superuser:
        msg = {"message": "Unauthorized"}
        return JsonResponse(msg, status=401)

    if request.method == "POST":
        return hsapi_post_user_for_keycloak(request, user_identifier)

    user: User = hydroshare.utils.user_from_id(user_identifier)
    user_profile = UserProfile.objects.filter(user=user).first()
    user_attributes = {}
    if user_profile.organization:
        user_attributes['cuahsi-organizations'] = [org for org in user_profile.organization.split(";")]
    if user_profile.state and user_profile.state.strip() and user_profile.state != 'Unspecified':
        user_attributes['cuahsi-region'] = [user_profile.state.strip()]
    if user_profile.country and user_profile.country != 'Unspecified':
        user_attributes['cuahsi-country'] = [user_profile.country]
    if user_profile.user_type and user_profile.user_type.strip() and user_profile.user_type != 'Unspecified':
        user_attributes['cuahsi-user-type'] = [user_profile.user_type.strip()]
    if user_profile.subject_areas:
        user_attributes['cuahsi-subject-areas'] = [subject for subject in user_profile.subject_areas]
    keycloak_dict = {
        "username": user.username,
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "enabled": True,
        "emailVerified": user.is_active,
        "attributes": user_attributes,
        "roles": [
            "hydroshare-imported"
        ],
    }
    return JsonResponse(keycloak_dict)


def hsapi_post_user_for_keycloak(request, user_identifier):
    """
    Check the user password
    """
    password = json.loads(request.body.decode('utf-8'))['password']
    user: User = hydroshare.utils.user_from_id(user_identifier)
    return HttpResponse() if user.check_password(password) else HttpResponseBadRequest()


@login_required
def get_user_or_group_data(request, user_or_group_id, is_group, *args, **kwargs):
    """
    This view function must be called as an AJAX call

    :param user_or_group_id: id of the user or group for which data is needed
    :param is_group : (string) 'false' if the id is for a group, 'true' if id is for a user
    :return: JsonResponse() containing user data
    """
    user_data = {}
    if is_group == "false":
        user = hydroshare.utils.user_from_id(user_or_group_id)
        user_data["name"] = hydroshare.utils.get_user_party_name(user)
        user_data["email"] = user.email
        user_data["url"] = "{domain}/user/{uid}/".format(
            domain=hydroshare.utils.current_site_url(), uid=user.pk
        )
        if user.userprofile.phone_1:
            user_data["phone"] = user.userprofile.phone_1
        elif user.userprofile.phone_2:
            user_data["phone"] = user.userprofile.phone_2
        else:
            user_data["phone"] = ""

        address = ""
        if user.userprofile.state and user.userprofile.state.lower() != "unspecified":
            address = user.userprofile.state
        if (
            user.userprofile.country
            and user.userprofile.country.lower() != "unspecified"
        ):
            if len(address) > 0:
                address += ", " + user.userprofile.country
            else:
                address = user.userprofile.country

        user_data["address"] = address
        user_data["organization"] = (
            user.userprofile.organization if user.userprofile.organization else ""
        )
        user_data["website"] = (
            user.userprofile.website if user.userprofile.website else ""
        )
        user_data["identifiers"] = user.userprofile.identifiers
        user_data["type"] = user.userprofile.user_type
        user_data["date_joined"] = user.date_joined
        user_data["subject_areas"] = user.userprofile.subject_areas
        if user.userprofile.state:
            user_data["state"] = user.userprofile.state
        if user.userprofile.country:
            user_data["country"] = user.userprofile.country
    else:
        group = hydroshare.utils.group_from_id(user_or_group_id)
        user_data["organization"] = group.name
        user_data["url"] = "{domain}/user/{uid}/".format(
            domain=hydroshare.utils.current_site_url(), uid=group.pk
        )
        user_data["description"] = group.gaccess.description

    return JsonResponse(user_data)


def _send_email_on_group_membership_acceptance(membership_request):
    """
    Sends email notification of group membership acceptance

    :param membership_request: an instance of GroupMembershipRequest class
    :return:
    """

    if membership_request.invitation_to is not None:
        # user accepted invitation from the group owner
        # here we are sending email to group owner who invited
        email_msg = """Dear {}
        <p>Your invitation to user '{}' to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(
            membership_request.request_from.first_name,
            membership_request.invitation_to.first_name,
            membership_request.group_to_join.name,
        )
    else:
        # group owner accepted user request
        # here wre are sending email to the user whose request to join got accepted
        email_msg = """Dear {}
        <p>Your request to join the group '{}' has been accepted.</p>
        <p>Thank you</p>
        <p>The HydroShare Team</p>
        """.format(
            membership_request.request_from.first_name,
            membership_request.group_to_join.name,
        )

    send_mail(
        subject="HydroShare group membership",
        message=email_msg,
        html_message=email_msg,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[membership_request.request_from.email],
    )


def _share_resource_with_user(request, frm, resource, requesting_user, privilege):
    if frm.is_valid():
        try:
            requesting_user.uaccess.share_resource_with_user(
                resource, frm.cleaned_data["user"], privilege
            )
        except PermissionDenied as exp:
            messages.error(request, str(exp))
    else:
        messages.error(request, frm.errors.as_json())


def _unshare_resource_with_users(
    request, requesting_user, users_to_unshare_with, resource, privilege
):
    users_to_keep = list(User.objects.in_bulk(users_to_unshare_with).values())
    owners = set(resource.raccess.owners.all())
    editors = set(resource.raccess.edit_users.all()) - owners
    viewers = set(resource.raccess.view_users.all()) - editors - owners

    if privilege == "owner":
        all_shared_users = owners
    elif privilege == "edit":
        all_shared_users = editors
    elif privilege == "view":
        all_shared_users = viewers
    else:
        all_shared_users = []

    go_to_resource_listing_page = False
    for user in all_shared_users:
        if user not in users_to_keep:
            try:
                # requesting user is the resource owner or requesting_user is self unsharing
                # COUCH: no need for undo_share; doesn't do what is intended 11/19/2016
                requesting_user.uaccess.unshare_resource_with_user(resource, user)

                if requesting_user == user and not resource.raccess.public:
                    go_to_resource_listing_page = True
            except PermissionDenied as exp:
                messages.error(request, str(exp))
                break
    return go_to_resource_listing_page


def _set_resource_sharing_status(user, resource, flag_to_set, flag_value):
    """
    Set flags 'public', 'discoverable', 'shareable'

    This routine generates appropriate messages for the REST API and thus differs from
    AbstractResource.set_public, set_discoverable, which raise exceptions.
    """

    if flag_to_set == "shareable":  # too simple to deserve a method in AbstractResource
        if resource.raccess.shareable != flag_value:
            resource.raccess.shareable = flag_value
            resource.raccess.save()
            return None

    elif flag_to_set == "discoverable":
        try:
            resource.set_discoverable(flag_value, user)  # checks access control
        except ValidationError as v:
            return str(v)

    elif flag_to_set == "public":
        try:
            resource.set_public(flag_value, user)  # checks access control
        except ValidationError as v:
            return str(v)
    else:
        return "Unrecognized resource flag {}".format(flag_to_set)
    return None


class FindGroupsView(TemplateView):
    template_name = (
        "pages/find-groups.html"
    )

    def dispatch(self, *args, **kwargs):
        return super(FindGroupsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        def get_groups_with_members(ugp_queryset):
            group_seen = []
            groups = []
            for ugp in ugp_queryset:
                if ugp.group.id not in group_seen:
                    group = ugp.group
                    group.members = []
                    group_seen.append(group.id)
                    groups.append(group)
                else:
                    group = groups[group_seen.index(ugp.group.id)]
                if ugp.user.is_active:
                    group.members.append(ugp.user)
            groups = sorted(groups, key=lambda _group: _group.name)
            return groups

        if self.request.user.is_authenticated:
            u = User.objects.get(pk=self.request.user.id)

            gmr_waiting_owner_action = GroupMembershipRequest.objects \
                .filter(request_from=u, group_to_join__gaccess__active=True, redeemed=False) \
                .values_list("group_to_join__id", flat=True)

            gmr_waiting_user_action = GroupMembershipRequest.objects \
                .filter(invitation_to=u, group_to_join__gaccess__active=True, redeemed=False) \
                .values_list("group_to_join__id", flat=True)

            gmr_pending = GroupMembershipRequest.objects \
                .filter(group_to_join__gaccess__active=True, redeemed=False) \
                .filter(Q(request_from=u) | Q(invitation_to=u)).select_related("group_to_join")

            ugp_qs = UserGroupPrivilege.objects \
                .filter(group__gaccess__active=True) \
                .exclude(group__name="Hydroshare Author") \
                .select_related("group", "user", "group__gaccess", "user__userprofile")

            # for ech group collect members of the group - not using 'group.gaccess.members'
            # as this results in N+1 query
            groups = get_groups_with_members(ugp_qs)
            for g in groups:
                g.is_user_member = u in g.members
                g.join_request = None
                if g.is_user_member:
                    g.join_request_waiting_owner_action = False
                    g.join_request_waiting_user_action = False
                else:
                    g.join_request_waiting_owner_action = g.id in gmr_waiting_owner_action
                    g.join_request_waiting_user_action = g.id in gmr_waiting_user_action

                    if (
                        g.join_request_waiting_owner_action
                        or g.join_request_waiting_user_action
                    ):
                        g.join_request = None
                        for gmr in gmr_pending:
                            if g.id == gmr.group_to_join.id:
                                g.join_request = gmr
                                break

            return {"profile_user": u, "groups": groups}
        else:
            # for anonymous user
            ugp_qs = UserGroupPrivilege.objects \
                .filter(Q(group__gaccess__active=True)
                        & (Q(group__gaccess__discoverable=True) | Q(group__gaccess__public=True))) \
                .exclude(group__name="Hydroshare Author") \
                .select_related("group", "user", "group__gaccess", "user__userprofile")

            groups = get_groups_with_members(ugp_qs)
            return {"groups": groups}


class MyGroupsView(TemplateView):
    template_name = "pages/my-groups.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MyGroupsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        def get_groups_with_ownership(ugp_queryset, user):
            group_seen = []
            groups = []
            for ugp in ugp_queryset:
                if ugp.group.id not in group_seen:
                    group = ugp.group
                    group_seen.append(group.id)
                    group.is_group_owner = False
                    group.member_count = 1
                    groups.append(group)
                else:
                    group = groups[group_seen.index(ugp.group.id)]
                    group.member_count += 1
                if ugp.user == user:
                    group.is_group_owner = ugp.privilege == PrivilegeCodes.OWNER

            groups = sorted(groups, key=lambda _group: _group.name)
            return groups

        u = User.objects.select_related("uaccess").get(pk=self.request.user.id)

        groups = u.uaccess.my_groups

        # for each group object, set a dynamic attribute to know if the user owns the group
        ugp_qs = UserGroupPrivilege.objects \
            .filter(group_id__in=[g.id for g in groups]) \
            .select_related("group", "user", "group__gaccess")

        groups = get_groups_with_ownership(ugp_qs, u)

        active_groups = [g for g in groups if g.gaccess.active]
        inactive_groups = [g for g in groups if not g.gaccess.active]

        my_pending_requests = GroupMembershipRequest.objects \
            .filter(request_from=u, redeemed=False) \
            .exclude(group_to_join__gaccess__active=False) \
            .select_related("invitation_to", "group_to_join")

        group_membership_requests = GroupMembershipRequest.objects \
            .filter(invitation_to=u, redeemed=False) \
            .exclude(group_to_join__gaccess__active=False) \
            .select_related("request_from", "request_from__userprofile", "group_to_join")

        return {
            "profile_user": u,
            "groups": active_groups,
            "inactive_groups": inactive_groups,
            "my_pending_requests": my_pending_requests,
            "group_membership_requests": group_membership_requests,
        }


class AddUserForm(forms.Form):
    user = forms.ModelChoiceField(
        User.objects.all(), widget=PatchedChoiceWidget("UserAutocomplete")
    )


@login_required
def request_new_community(request, *args, **kwargs):
    """ A view function to server request for creating a new community """

    community_form = RequestNewCommunityForm(request.POST, request.FILES)
    if community_form.is_valid():
        try:
            new_community_request = community_form.save(request)
            new_community_name = new_community_request.community_to_approve.name
            msg = f"New community ({new_community_name}) request was successful."
            messages.success(request, msg)
            # send email to hydroshare support
            CommunityRequestEmailNotification(request=request, community_request=new_community_request,
                                              on_event=CommunityRequestEvents.CREATED).send()
            return HttpResponseRedirect(reverse('my_communities'))
        except PermissionDenied:
            err_msg = "You don't have permission to request new community"
            messages.error(request, err_msg)
        except Exception as ex:
            messages.error(request, f"Community request errors:{str(ex)}.")

    else:
        messages.error(request, "Community request errors:{}.".format(community_form.errors.as_json))

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


# Any HydroShare user (whether authenticated or not) can access the landing page for a public or discoverable Group.
# When they do, they will see the Group’s metadata.
# For public groups, anyone will be able to see the Group’s public and published resources and group membership.
# For discoverable Groups, the list of resources and membership will only be accessible to Group members.
class GroupView(TemplateView):
    template_name = "pages/group.html"

    def hydroshare_denied(self, gid):
        try:
            g = Group.objects.select_related("gaccess").get(pk=gid)
        except Group.DoesNotExist:
            message = "group id {} not found".format(gid)
            logger.error(message)
            return message

        if not (g.gaccess.public or g.gaccess.discoverable):
            if not self.request.user.is_authenticated:
                message = 'You need to sign in to access the contents of this private Group'
                return message

            u = User.objects.get(pk=self.request.user.id)
            if u not in g.gaccess.members:
                message = 'Only Group members can access the content of this private Group'
                return message

        return ''

    def dispatch(self, *args, **kwargs):
        return super(GroupView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        data = {}  # JSON serializable data to be used in Vue app
        message = ""
        group_id = kwargs["group_id"]
        denied = self.hydroshare_denied(group_id)

        if denied == "":
            group = Group.objects.select_related("gaccess").get(pk=group_id)
            data["is_group_private"] = 0 if group.gaccess.public or group.gaccess.discoverable else 1
            data["denied"] = denied  # empty string means ok
            data["message"] = message
            data["gid"] = group_id

            # communities joined
            data["joined"] = []
            for c in Community.objects.filter(c2gcp__group=group).order_by('name'):
                data["joined"].append(community_json(c))

            # pending requests from this group
            data["pending"] = []
            for r in GroupCommunityRequest.objects.filter(
                    group=group, redeemed=False) \
                    .select_related("community", "group", "group__gaccess", "group_owner",
                                    "group_owner__uaccess", "group_owner__userprofile") \
                    .order_by("community__name"):
                data["pending"].append(group_community_request_json(r))

            # Communities that can be joined.
            data["available_to_join"] = []
            for c in Community.objects.filter(active=True) \
                    .exclude(closed=True) \
                    .exclude(Q(invite_c2gcr__group=group) & Q(invite_c2gcr__redeemed=False)) \
                    .exclude(c2gcp__group=group) \
                    .order_by("name"):
                data["available_to_join"].append(community_json(c))
        else:  # non-empty denied means an error.
            data["denied"] = denied
            context["denied"] = denied
            return context

        group_resources = []
        # for each of the resources this group has access to, set resource dynamic
        # attributes (grantor - group member who granted access to the resource) and (date_granted)
        view_resources = group.gaccess.view_resources
        res_ids = [res.short_id for res in view_resources]
        grp_qs = GroupResourcePrivilege.objects \
            .filter(group=group, resource__short_id__in=res_ids) \
            .select_related("grantor", "resource")

        for res in view_resources:
            for grp in grp_qs:
                if res.short_id == grp.resource.short_id:
                    res.grantor = grp.grantor
                    res.date_granted = grp.start
                    group_resources.append(res)
                    break

        group_resources = sorted(
            group_resources, key=lambda x: x.date_granted, reverse=True
        )

        context["group"] = group
        context["view_users"] = group.gaccess.get_users_with_explicit_access(PrivilegeCodes.VIEW)

        if self.request.user.is_authenticated:
            group_members = group.gaccess.members
            u = User.objects.select_related("uaccess").get(pk=self.request.user.id)
            u.is_group_owner = u.uaccess.owns_group(group)
            u.is_group_editor = group in u.uaccess.edit_groups
            u.is_group_viewer = group.gaccess.public or group.gaccess.discoverable or group in u.uaccess.view_groups
            u.is_group_member = u in group_members

            group.join_request_waiting_owner_action = group.gaccess.group_membership_requests \
                .filter(request_from=u).exists()

            group.join_request_waiting_user_action = group.gaccess.group_membership_requests \
                .filter(invitation_to=u).exists()

            group.join_request = group.gaccess.group_membership_requests.filter(invitation_to=u).first()

            # This will exclude requests from inactive users made for themselves
            # as well as invitations from inactive users to others
            group.gaccess.active_group_membership_requests = group.gaccess.group_membership_requests.filter(
                Q(request_from__is_active=True),
                Q(invitation_to=None) | Q(invitation_to__is_active=True),
            )

            if u.is_group_member:
                context["group_resources"] = group_resources
            elif group.gaccess.public:
                # If the group is public, anyone can see the group's public and published resources and group membership
                group_resources = [r for r in group_resources if r.raccess.public or r.raccess.discoverable]
                context["group_resources"] = group_resources

            context["profile_user"] = u
            context["add_view_user_form"] = AddUserForm()
            data["is_group_owner"] = u.is_group_owner
        else:
            # If the group is public, anonymous users can see discoverable and public resources shared with the group
            if group.gaccess.public:
                public_group_resources = [r for r in group_resources if r.raccess.public or r.raccess.discoverable]
                context["group_resources"] = public_group_resources

        context["data"] = data
        return context


@login_required
def my_resources_filter_counts(request, *args, **kwargs):
    """
    View for counting resources that belong to a given user.
    """
    _ = request.GET.getlist("filter", default=None)
    u = User.objects.select_related("uaccess").get(pk=request.user.id)

    filter_counts = get_my_resources_filter_counts(u)

    return JsonResponse({"filter_counts": filter_counts})


@login_required
def my_resources(request, *args, **kwargs):
    """
    View for listing resources that belong to a given user.

    Renders either a full my-resources page, or just a table of new resources
    """

    if not request.is_ajax():
        filter = request.GET.getlist("f", default=[])
    else:
        filter = [request.GET["new_filter"]]
    u = User.objects.select_related("uaccess").get(pk=request.user.id)

    if not filter:
        # add default filters
        filter = ["owned", "discovered", "favorites"]

    if "shared" in filter:
        filter.remove("shared")
        filter.append("viewable")
        filter.append("editable")

    resource_collection = get_my_resources_list(u, annotate=True, filter=filter)

    context = {"collection": resource_collection}

    if not request.is_ajax():
        return render(request, "pages/my-resources.html", context)
    else:
        from django.template.loader import render_to_string

        trows = render_to_string("includes/my-resources-trows.html", context, request)
        return JsonResponse(
            {
                "trows": trows,
            }
        )


def get_non_preferred_paths(request, shortkey):
    try:
        resource, _, _ = authorize(request, shortkey,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    except ObjectDoesNotExist:
        err_message = f"No resource was found for id:{shortkey}"
        data = {"status": "ERROR", "error": err_message}
        return JsonResponse(data)
    except PermissionDenied:
        err_message = "You don't have permission for this resource"
        data = {"status": "ERROR", "error": err_message}
        return JsonResponse(data)

    try:
        non_preferred_paths = resource.get_non_preferred_path_names()
    except Exception as ex:
        data = {"status": "ERROR", "error": str(ex)}
        return JsonResponse(data)

    data = {"status": "SUCCESS", "non_preferred_paths": non_preferred_paths}
    return JsonResponse(data)
