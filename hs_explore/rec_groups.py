# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView  # ListView
from hs_core.models import get_user
from hs_explore.models import RecommendedGroup, Status, PropensityPreferences, \
    PropensityPrefToPair, GroupPreferences, GroupPrefToPair
from hs_core.hydroshare.utils import user_from_id


class RecommendGroups(TemplateView):
    """ Get the top five recommendations for resources, users, groups """
    template_name = 'recommended_groups.html'

    def get_context_data(self, **kwargs):

        # target_user = get_user(self.request)
        # target_username = target_user.username
        target_username = str(self.request.GET['user'])
        target_user = user_from_id(target_username)
        action = str(self.request.GET['action'])

        if action == 'update':
            gk = str(self.request.GET['genre_key'])
            gv = str(self.request.GET['genre_value'])
            recommended_gps = RecommendedGroup.objects.filter(user=target_user)
            recommended_gps.delete()

            rpp = PropensityPreferences.objects.get(user=target_user)

            rpp.reject('Group', gk, gv)
            all_pp = rpp.preferences.all()

            propensity_preferences = PropensityPrefToPair.objects\
                .filter(prop_pref=rpp,
                        pair__in=all_pp,
                        state='Seen',
                        pref_for='Group')
            target_propensity_preferences_set = set()

            for p in propensity_preferences:
                if p.pair.key == 'subject':
                    target_propensity_preferences_set.add(p.pair.value)

            for gp in GroupPreferences.objects.all():
                group = gp.group
                all_gp = gp.preferences.all()
                gp_preferences = GroupPrefToPair.objects.filter(group_pref=gp,
                                                                pair__in=all_gp)
                gp_propensity_preferences_set = set()

                for p in gp_preferences:
                    if p.pair.key == 'subject':
                        gp_propensity_preferences_set.add(p.pair.value)

                intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set,
                                                                  gp_propensity_preferences_set]))
                union_cardinality = len(set.union(*[target_propensity_preferences_set,
                                                    gp_propensity_preferences_set]))
                js = intersection_cardinality/float(union_cardinality)
                r3 = RecommendedGroup.recommend(target_user, group, round(js, 4))
                common_subjects = set.intersection(target_propensity_preferences_set,
                                                   gp_propensity_preferences_set)
                for cs in common_subjects:
                    r3.relate('subject', cs, 1)

        context = super(RecommendGroups, self).get_context_data(**kwargs)
        context['group_list'] = RecommendedGroup.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        # mark relevant records as shown
        for r in context['group_list']:
            if r.state == Status.STATUS_NEW:
                r.shown()

        return context
