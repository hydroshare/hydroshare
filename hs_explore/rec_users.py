# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView  # ListView
from hs_core.models import get_user
from hs_explore.models import RecommendedUser, Status, PropensityPrefToPair, \
        PropensityPreferences, UserNeighbors
from hs_core.hydroshare.utils import user_from_id


class RecommendUsers(TemplateView):
    """ Get the top five recommendations for resources, users, groups """
    template_name = 'recommended_users.html'

    def get_context_data(self, **kwargs):

        target_user = get_user(self.request)
        target_username = target_user.username
        # target_username = str(self.request.GET['user'])
        # target_user = user_from_id(target_username)
        action = str(self.request.GET['action'])

        if action == 'update':
            gk = str(self.request.GET['genre_key'])
            gv = str(self.request.GET['genre_value'])

            recommended_users = RecommendedUser.objects.filter(user=target_user)
            recommended_users.delete()

            rpp = PropensityPreferences.objects.get(user=target_user)

            rpp.reject('User', gk, gv)
            all_pp = rpp.preferences.all()

            propensity_preferences = PropensityPrefToPair.objects.filter(prop_pref=rpp,
                                                                         pair__in=all_pp,
                                                                         state='Seen',
                                                                         pref_for='User')
            target_propensity_preferences_set = set()

            for p in propensity_preferences:
                if p.pair.key == 'subject':
                    target_propensity_preferences_set.add(p.pair.value)

            user_neighbors = UserNeighbors.objects.get(user=target_user)

            for neighbor in user_neighbors.neighbors.all():
                neighbor_up = PropensityPreferences.objects.get(user=neighbor)
                neighbor_pref = neighbor_up.preferences.all()
                neighbor_propensity_preferences = PropensityPrefToPair.objects\
                    .filter(prop_pref=neighbor_up,
                            pair__in=neighbor_pref,
                            state='Seen',
                            pref_for='User')
                neighbor_subjects = set()
                for p in neighbor_propensity_preferences:
                    if p.pair.key == 'subject':
                        neighbor_subjects.add(p.pair.value)

                if (len(neighbor_subjects) == 0):
                    continue

                intersection_cardinality = len(set.intersection(*[target_propensity_preferences_set,
                                                                  neighbor_subjects]))
                union_cardinality = len(set.union(*[target_propensity_preferences_set,
                                                    neighbor_subjects]))
                js = intersection_cardinality/float(union_cardinality)
                
                #if js - 0 < 0.000001:
                #    continue
                r2 = RecommendedUser.recommend(target_user, neighbor, round(js, 4))
                common_subjects = set.intersection(target_propensity_preferences_set,
                                                   neighbor_subjects)

                for cs in common_subjects:
                    r2.relate('subject', cs, 1)

        context = super(RecommendUsers, self).get_context_data(**kwargs)

        context['user_list'] = RecommendedUser.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=target_username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        # mark relevant records as shown
        for r in context['user_list']:
            if r.state == Status.STATUS_NEW:
                r.shown()

        return context
