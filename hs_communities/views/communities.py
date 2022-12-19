import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe, escapejs
from django.views.generic import TemplateView

from hs_access_control.management.utilities import community_from_name_or_id
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import UserCommunityPrivilege, PrivilegeCodes
from hs_communities.models import Topic


class CollaborateView(TemplateView):
    template_name = "pages/collaborate.html"


class CommunityView(TemplateView):
    template_name = "hs_communities/community.html"

    def dispatch(self, *args, **kwargs):
        return super(CommunityView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        grpfilter = self.request.GET.get("grp")

        community = community_from_name_or_id(kwargs["community_id"])
        community_resources = community.public_resources.distinct()
        raw_groups = community.groups_with_public_resources()
        groups = []

        for g in raw_groups:
            res_count = len([r for r in community_resources if r.group_name == g.name])
            groups.append(
                {"id": str(g.id), "name": str(g.name), "res_count": str(res_count)}
            )

        groups = sorted(groups, key=lambda key: key["name"])

        try:
            u = User.objects.get(pk=self.request.user.id)
            # user must own the community to get admin privilege
            is_admin = UserCommunityPrivilege.objects.filter(
                user=u, community=community, privilege=PrivilegeCodes.OWNER
            ).exists()
        except: # noqa
            is_admin = False

        return {
            "community": community,
            "community_resources": community_resources,
            "groups": groups,
            "grpfilter": grpfilter,
            "is_admin": is_admin,
            "czo_community": "CZO National" in community.name,
        }


class FindCommunitiesView(TemplateView):
    template_name = "hs_communities/find-communities.html"

    def dispatch(self, *args, **kwargs):
        return super(FindCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        return {"communities_list": Community.objects.all()}


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
        grps_member_of = []
        u = User.objects.get(pk=self.request.user.id)
        groups = Group.objects.filter(gaccess__active=True).exclude(
            name="Hydroshare Author"
        )
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = u in g.gaccess.members
            if g.is_user_member:
                grps_member_of.append(g)
            g.join_request_waiting_owner_action = (
                g.gaccess.group_membership_requests.filter(request_from=u).exists()
            )
            g.join_request_waiting_user_action = (
                g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
            )
            g.join_request = None
            if (
                g.join_request_waiting_owner_action
                or g.join_request_waiting_user_action
            ):
                g.join_request = (
                    g.gaccess.group_membership_requests.filter(request_from=u).first()
                    or g.gaccess.group_membership_requests.filter(
                        invitation_to=u
                    ).first()
                )

        comms_member_of = [
            self.group_to_community(g, Community.objects.all()) for g in grps_member_of
        ]
        return {"communities_list": [c for c in comms_member_of if c is not None]}


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
