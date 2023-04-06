import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import F, Q
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.html import escapejs, mark_safe
from django.views.generic import TemplateView

from hs_access_control.models import Community, GroupCommunityRequest, RequestCommunity
from hs_access_control.models.privilege import (
    GroupCommunityPrivilege,
    PrivilegeCodes,
    UserCommunityPrivilege,
    UserGroupPrivilege,
)
from hs_access_control.views import (
    community_json,
    group_community_request_json,
    group_json,
    community_request_json,
)

from hs_communities.models import Topic
from hs_core.views import add_generic_context

logger = logging.getLogger(__name__)


class CollaborateView(TemplateView):
    template_name = "pages/collaborate.html"


class CommunityView(TemplateView):
    template_name = "hs_communities/community.html"

    def dispatch(self, *args, **kwargs):
        return super(CommunityView, self).dispatch(*args, **kwargs)

    def hydroshare_denied(self, cid):
        try:
            Community.objects.get(id=cid)
        except Community.DoesNotExist:
            message = "community id {} not found".format(cid)
            logger.error(message)
            return message

        return ''

    def get_context_data(self, *args, **kwargs):
        message = ''
        context = {}
        data = {}   # JSON serializable data to be used in Vue app

        if "community_id" in kwargs:
            cid = int(kwargs["community_id"])
        else:
            cid = None

        denied = self.hydroshare_denied(cid)
        logger.debug("denied is {}".format(denied))
        if denied == "":
            user = self.request.user
            community = Community.objects.get(id=int(cid))
            community_resources = community.public_resources.distinct()
            grpfilter = self.request.GET.get("grp")

            # Only authenticated users can make use of the data below
            if user.is_authenticated:
                is_admin = 1 if UserCommunityPrivilege.objects.filter(user=user, community=community,
                                                                      privilege=PrivilegeCodes.OWNER).exists() else 0
                data["is_admin"] = is_admin
                # data["user"] = user_json(user)
                context["is_admin"] = is_admin

                # Groups that can be invited
                data["groups"] = []

                if is_admin:
                    # Community owners can invite any group
                    groups = Group.objects

                    # forms needed for admin actions
                    hs_core_dublin_context = add_generic_context(self.request, None)
                    context.update(hs_core_dublin_context)
                else:
                    # Other users can invite groups they own
                    groups = user.uaccess.owned_groups

                # exclude groups that are already invited or members.
                for g in groups.filter(gaccess__active=True) \
                        .exclude(Q(invite_g2gcr__community=community) & Q(invite_g2gcr__redeemed=False)) \
                        .exclude(g2gcp__community=community) \
                        .select_related("gaccess") \
                        .order_by("name"):
                    data["groups"].append(group_json(g))

                data["pending"] = []
                for r in GroupCommunityRequest.objects \
                        .filter(community=community, redeemed=False) \
                        .select_related("community", "group") \
                        .order_by("group__name"):
                    data["pending"].append(group_community_request_json(r))

            # Both authenticated and anonymous users can make use of the data below
            context["community_resources"] = community_resources
            context["grpfilter"] = grpfilter
            context["denied"] = denied
            context["message"] = message
            context["czo_community"] = "CZO National" in community.name
            # context["banner"] = community.banner

            # community data is used both by the vue app and the template render
            context["community"] = community_json(community)
            data["community"] = community_json(community)

            # groups that have shared resources with the community
            raw_groups = community.groups_with_public_resources()
            shared_by_groups = []
            for g in raw_groups:
                res_count = len([r for r in community_resources if r.group_name == g.name])
                shared_by_groups.append({"id": str(g.id), "name": str(g.name), "res_count": str(res_count)})
            context["shared_by_groups"] = shared_by_groups

            # group members of community
            data["members"] = []
            for g in Group.objects.filter(g2gcp__community=community).select_related("gaccess").order_by("name"):
                data["members"].append(group_json(g))

            context['data'] = data
            return context

        else:  # non-empty denied means an error.
            context["denied"] = denied
            logger.error(denied)
            return context


class FindCommunitiesView(TemplateView):
    template_name = "hs_communities/find-communities.html"

    def dispatch(self, *args, **kwargs):
        return super(FindCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        user = self.request.user
        user_is_admin = False
        if user:
            user_is_admin = user.is_authenticated and user.is_superuser

        if user.is_authenticated:
            # get the list of any pending community create requests by this user
            user_pending_requests = user.uaccess.pending_community_requests()
            context["user_pending_requests"] = user_pending_requests

        if user_is_admin:
            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(community_request_json(request))
            context["admin_all_requests"] = admin_all_requests
            context["admin_pending_requests"] = RequestCommunity.pending_requests().count()

        context["communities_list"] = Community.objects.filter(active=True)
        context["user_is_admin"] = user_is_admin

        return context


@method_decorator(login_required, name="dispatch")
class MyCommunitiesView(TemplateView):
    template_name = "hs_communities/my-communities.html"

    def dispatch(self, *args, **kwargs):
        return super(MyCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        data = {}   # JSON serializable data to be used in Vue app
        user_groups = []
        user = self.request.user

        # for each group set group dynamic attributes
        user_groups_qs = UserGroupPrivilege.objects\
            .filter(user=user, group__gaccess__active=True) \
            .select_related("group") \
            .only("group")

        for ugp in user_groups_qs:
            group = ugp.group
            group.is_user_member = True
            user_groups.append(group)

        user_in_communities_qs = GroupCommunityPrivilege.objects \
            .filter(group__id__in=[grp.id for grp in user_groups], community__active=True) \
            .select_related("community") \
            .only("community") \
            .distinct("community")

        communities_member_of = [gcp.community for gcp in user_in_communities_qs]

        # Also list communities that the user owns
        user_community_qs = UserCommunityPrivilege.objects \
            .filter(user=user, privilege=PrivilegeCodes.OWNER, community__active=True) \
            .select_related("community") \
            .only("community") \
            .distinct("community")

        for ucp in user_community_qs:
            if ucp.community not in communities_member_of:
                communities_member_of.append(ucp.community)

        # get the list of any pending community create requests by this user
        user_pending_requests = []
        rc_pending_qs = RequestCommunity.pending_requests().filter(requested_by=user)
        for rc in rc_pending_qs:
            user_pending_requests.append(community_request_json(rc))

        # get the list of any declined community create requests by this user
        user_declined_requests = []
        rc_declined_qs = RequestCommunity.declined_requests().filter(requested_by=user)
        for rc in rc_declined_qs:
            user_declined_requests.append(community_request_json(rc))

        user_is_admin = user.is_authenticated and user.is_superuser

        if user_is_admin:
            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(community_request_json(request))
            context["admin_all_requests"] = admin_all_requests
            context["admin_pending_requests"] = RequestCommunity.pending_requests().count()

        context["communities_list"] = communities_member_of
        context["user_is_admin"] = user_is_admin
        context['data'] = data

        data["user_pending_requests"] = user_pending_requests
        data["user_declined_requests"] = user_declined_requests
        return context


class CommunityCreationRequests(TemplateView):
    """A view to serve all pending community creation requests"""

    template_name = 'hs_communities/pending-community-requests.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CommunityCreationRequests, self).dispatch(*args, **kwargs)

    def hydroshare_denied(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message

        if not user.is_superuser:
            message = "user with id {} is not a superuser".format(user.id)
            logger.error(message)
            return message

        return ""

    def get_context_data(self, **kwargs):
        denied = self.hydroshare_denied()

        if denied == "":
            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by('-date_requested'):
                admin_all_requests.append(community_request_json(request))

            return {
                "admin_all_requests": admin_all_requests,
                "admin_pending_requests": RequestCommunity.pending_requests().count(),
                "user_is_admin": self.request.user.is_superuser
            }
        else:
            logger.error(denied)
            return {"denied": denied}


class CommunityCreationRequest(TemplateView):
    """A view to serve a pending community creation request"""

    template_name = 'hs_communities/pending-community-request.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CommunityCreationRequest, self).dispatch(*args, **kwargs)

    def hydroshare_denied(self, rid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message

        if rid is not None:
            try:
                req = RequestCommunity.objects.get(id=rid)
            except RequestCommunity.DoesNotExist:
                message = "community request id {} not found".format(rid)
                logger.error(message)
                return message

        if not user.is_superuser and not user == req.requested_by:
            message = "user with id {} is not a superuser or the user who submitted the request".format(user.id)
            logger.error(message)
            return message

        return ""

    def get_context_data(self, **kwargs):
        context = {}
        if "rid" in kwargs:
            rid = int(kwargs["rid"])
        else:
            rid = None

        denied = self.hydroshare_denied(rid)

        if denied == "" and rid is not None:
            req = RequestCommunity.objects.get(id=int(rid))
            context["community_request"] = community_request_json(req)

            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(community_request_json(request))

            context["admin_all_requests"] = admin_all_requests
            context["admin_pending_requests"] = RequestCommunity.pending_requests().count()
        else:
            context["denied"] = denied
            logger.error(denied)

        context["user_is_admin"] = self.request.user.is_superuser

        return context


@method_decorator(login_required, name="dispatch")
class TopicsView(TemplateView):
    """
    action: CREATE, READ, UPDATE, DELETE
    """

    def get(self, request, *args, **kwargs):
        u = User.objects.get(pk=self.request.user.id)
        if u.username not in [
            "czo_national",
            "czo_sierra",
            "czo_boulder",
            "czo_christina",
            "czo_luquillo",
            "czo_eel",
            "czo_catalina-jemez",
            "czo_reynolds",
            "czo_calhoun",
            "czo_shale-hills",
        ]:
            return redirect("/" % request.path)

        return render(
            request, "pages/topics.html", {"topics_json": self.get_topics_data()}
        )

    def post(self, request, *args, **kwargs):
        u = User.objects.get(pk=self.request.user.id)
        if u.username != "czo_national":
            return redirect("/" % request.path)

        if request.POST.get("action") == "CREATE":
            new_topic = Topic()
            new_topic.name = request.POST.get("name").replace("--", "")
            new_topic.save()
        elif request.POST.get("action") == "UPDATE":
            try:
                update_topic = Topic.objects.get(id=request.POST.get("id"))
                update_topic.name = request.POST.get("name")
                update_topic.save()
            except Exception as e:
                print("TopicsView error updating topic {}".format(e))
        elif request.POST.get("action") == "DELETE":
            try:
                delete_topic = Topic.objects.get(id=request.POST.get("id"))
                delete_topic.delete(keep_parents=False)
            except: # noqa
                print("error")
        else:
            print(
                "TopicsView POST action not recognized should be CREATE UPDATE or DELETE"
            )

        return render(request, "pages/topics.html")

    def get_topics_data(self, **kwargs):
        topics = (
            Topic.objects.all().values_list("id", "name", flat=False).order_by("name")
        )
        topics = list(topics)  # force QuerySet evaluation
        return mark_safe(escapejs(json.dumps(topics)))
