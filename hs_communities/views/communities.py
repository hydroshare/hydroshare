import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.html import escapejs, mark_safe
from django.views.generic import TemplateView

from hs_access_control.models import Community, GroupCommunityRequest, RequestCommunity
from hs_access_control.models.privilege import PrivilegeCodes, UserCommunityPrivilege
from hs_access_control.views import community_json, gcr_json, group_json, user_json, cr_json
from hs_communities.models import Topic

logger = logging.getLogger(__name__)


class CollaborateView(TemplateView):
    template_name = "pages/collaborate.html"


class CommunityView(TemplateView):
    template_name = "hs_communities/community.html"

    def dispatch(self, *args, **kwargs):
        self.template_name = "hs_communities/community.html"
        return super(CommunityView, self).dispatch(*args, **kwargs)

    def hydroshare_denied(self, cid, gid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message

        try:
            community = Community.objects.get(id=cid)
        except Community.DoesNotExist:
            message = "community id {} not found".format(cid)
            logger.error(message)
            return message

        if user.uaccess.owns_community(community):
            if gid is None:
                return ""
            else:
                group = Group.objects.filter(id=gid)
                if group.count() < 1:
                    message = "group id {} not found".format(gid)
                    logger.error(message)
                    return message
                else:
                    return ""

        else:
            message = "user {} ({}) does not own community {} ({})"\
                      .format(user.username, user.id, community.name, community.id)
            logger.error(message)
            return message

    def get_context_data(self, *args, **kwargs):
        message = ''
        context = {}

        if "cid" in kwargs:
            cid = int(kwargs["cid"])
        else:
            cid = None

        if "gid" in kwargs:
            gid = int(kwargs["gid"])
        else:
            gid = None

        if "action" in kwargs:
            action = kwargs["action"]
        else:
            action = None

        logger.debug("cid={} action={} gid={}".format(cid, action, gid))
        denied = self.hydroshare_denied(cid, gid)
        logger.debug("denied is {}".format(denied))
        if denied == "":
            user = self.request.user
            community = Community.objects.get(id=int(cid))
            community_resources = community.public_resources.distinct()
            grpfilter = self.request.GET.get("grp")
            is_admin = 1 if UserCommunityPrivilege.objects.filter(user=user, community=community,
                                                                  privilege=PrivilegeCodes.OWNER).exists() else 0

            context["community_resources"] = community_resources
            context["grpfilter"] = grpfilter
            context["is_admin"] = is_admin
            context["czo_community"] = "CZO National" in community.name

            if action is not None:
                group = Group.objects.get(id=int(gid))
                if action == "approve":  # approve a request from a group
                    gcr = GroupCommunityRequest.objects.get(
                        community=community, group=group)
                    if gcr.redeemed:  # make it possible to approve a formerly declined request.
                        gcr.reset(responder=user)
                    message, worked = gcr.approve(responder=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == "decline":  # decline a request from a group
                    gcr = GroupCommunityRequest.objects.get(
                        community__id=int(cid),
                        group__id=int(kwargs["gid"]))
                    message, worked = gcr.decline(responder=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == "invite":
                    logger.debug("action is invite")
                    try:
                        message, worked = GroupCommunityRequest.create_or_update(
                            requester=user, group=group, community=community)
                        logger.debug("message = '{}' worked='{}'".format(message, worked))
                    except Exception as e:
                        logger.debug(e)

                elif action == 'remove':  # remove a group from this community
                    message, worked = GroupCommunityRequest.remove(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == "retract":  # remove a pending request
                    message, worked = GroupCommunityRequest.retract(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            # build a JSON object that contains the results of the query

            context["denied"] = denied
            context["message"] = message
            context["user"] = user_json(user)
            context["community"] = community_json(community)

            # groups that can be invited are those that are not already invited or members.
            context["groups"] = []
            for g in Group.objects.filter(gaccess__active=True)\
                                  .exclude(invite_g2gcr__community=community)\
                                  .exclude(g2gcp__community=community)\
                                  .order_by("name"):
                context["groups"].append(group_json(g))

            # groups that have shared resources with the community
            raw_groups = community.groups_with_public_resources()
            shared_by_groups = []
            for g in raw_groups:
                res_count = len([r for r in community_resources if r.group_name == g.name])
                shared_by_groups.append({"id": str(g.id), "name": str(g.name), "res_count": str(res_count)})
            context["shared_by_groups"] = shared_by_groups

            context["pending"] = []
            for r in GroupCommunityRequest.objects.filter(
                    community=community, redeemed=False, group_owner__isnull=True).order_by("group__name"):
                context["pending"].append(gcr_json(r))

            # requests that were declined by us
            context["we_declined"] = []
            for r in GroupCommunityRequest.objects.filter(
                    community=community, redeemed=True, approved=False,
                    when_group__lt=F("when_community")).order_by("group__name"):
                context["we_declined"].append(gcr_json(r))

            # requests that were declined by others
            context["they_declined"] = []
            for r in GroupCommunityRequest.objects.filter(
                    community=community, redeemed=True, approved=False,
                    when_group__gt=F("when_community")).order_by("group__name"):
                context["they_declined"].append(gcr_json(r))

            # group requests to be approved
            context["approvals"] = []
            for r in GroupCommunityRequest.objects.filter(
                    community=Community.objects.get(id=int(cid)),
                    group__gaccess__active=True,
                    community_owner__isnull=True,
                    redeemed=False).order_by("group__name"):
                context["approvals"].append(gcr_json(r))

            # group members of community
            context["members"] = []
            for g in Group.objects.filter(g2gcp__community=community).order_by("name"):
                context["members"].append(group_json(g))

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

        # get the list of any pending community create requests by this user
        user_pending_requests = user.uaccess.pending_community_requests()

        if user_is_admin:
            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(cr_json(request))
            context["admin_all_requests"] = admin_all_requests
            context["admin_pending_requests"] = RequestCommunity.pending_requests().count()

        context["communities_list"] = Community.objects.filter(active=True)
        context["user_pending_requests"] = user_pending_requests
        context["user_is_admin"] = user_is_admin

        return context


@method_decorator(login_required, name="dispatch")
class MyCommunitiesView(TemplateView):
    template_name = "hs_communities/my-communities.html"

    def dispatch(self, *args, **kwargs):
        return super(MyCommunitiesView, self).dispatch(*args, **kwargs)

    def group_to_community(self, grp, communities):
        """
        return the community membership information of a group; group can belong to only one community
        :param grp: group object
        :param communities: communities
        :return: tuple id, name of community
        """
        for community in communities:
            if grp.id in [g.id for g in community.member_groups]:
                return community

    def get_context_data(self, **kwargs):
        context = {}
        groups_member_of = []
        user = self.request.user
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        communities = Community.objects.all()
        # for each group set group dynamic attributes
        for group in groups:
            group.is_user_member = user in group.gaccess.members
            if group.is_user_member:
                groups_member_of.append(group)
            group.join_request_waiting_owner_action = group.gaccess.group_membership_requests.filter(
                request_from=user).exists()
            group.join_request_waiting_user_action = group.gaccess.group_membership_requests.filter(
                invitation_to=user).exists()
            group.join_request = None
            if group.join_request_waiting_owner_action or group.join_request_waiting_user_action:
                group.join_request = group.gaccess.group_membership_requests.filter(request_from=user).first() or \
                    group.gaccess.group_membership_requests.filter(invitation_to=user).first()

        communities_member_of = [self.group_to_community(g, Community.objects.all()) for g in groups_member_of]

        # Also list communities that the user owns
        for community in communities:
            is_owner = user in community.owners
            if is_owner and community not in communities_member_of:
                communities_member_of.append(community)

        # get the list of any pending community create requests by this user
        user_pending_requests = user.uaccess.pending_community_requests()

        user_is_admin = False
        if user:
            user_is_admin = user.is_authenticated and user.is_superuser

        if user_is_admin:
            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(cr_json(request))
            context["admin_all_requests"] = admin_all_requests
            context["admin_pending_requests"] = RequestCommunity.pending_requests().count()

        context["communities_list"] = [c for c in communities_member_of if c is not None]
        context["user_pending_requests"] = user_pending_requests
        context["user_is_admin"] = user_is_admin

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
                admin_all_requests.append(cr_json(request))

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

        if not user.is_superuser:
            message = "user with id {} is not a superuser".format(user.id)
            logger.error(message)
            return message

        if rid is not None:
            try:
                RequestCommunity.objects.get(id=rid)
            except RequestCommunity.DoesNotExist:
                message = "community request id {} not found".format(rid)
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
            context["community_request"] = cr_json(req)

            admin_all_requests = []
            for request in RequestCommunity.all_requests().order_by("-date_requested"):
                admin_all_requests.append(cr_json(request))

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
