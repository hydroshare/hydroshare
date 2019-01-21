from django.db import models, transaction
from hs_core.models import BaseResource
from django.contrib.auth.models import User, Group
from hs_core.hydroshare import user_from_id, group_from_id, get_resource_by_shortkey


class Status(object):
    STATUS_NEW = 1
    STATUS_SHOWN = 2
    STATUS_EXPLORED = 3
    STATUS_APPROVED = 4
    STATUS_DISMISSED = 5
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_SHOWN, 'Shown'),
        (STATUS_EXPLORED, 'Explored'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DISMISSED, 'Dismissed')
    )
    RECOMMENDATION_LIMIT = 5


class KeyValuePair(models.Model):
    key = models.CharField(max_length=255, editable=False, null=False, blank=False,
                           default='subject')
    value = models.CharField(max_length=255, editable=False, null=False, blank=False,
                             default='value')

    class Meta:
        unique_together = ('key', 'value')

    @staticmethod
    def create(key, value):
        """ don't create duplicate objects """

        with transaction.atomic():
            object, _ = KeyValuePair.objects.get_or_create(key=key, value=value)

        return object

    @staticmethod
    def clear():
        KeyValuePair.objects.all().delete()

    def to_json(self):
        json_obj = {}
        json_obj['key'] = self.key
        json_obj['value'] = self.value
        return json_obj


class ResourceRecToPair(models.Model):
    recommendation = models.ForeignKey('RecommendedResource', editable=False,
                                       null=False, on_delete=models.CASCADE)
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('recommendation', 'pair')

    @staticmethod
    def create(r, k, v, w):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(k, v)
        with transaction.atomic():
            object, created = ResourceRecToPair.objects.get_or_create(recommendation=r, pair=p,
                                                                      defaults={'weight': w})
            if not created:
                object.weight = w
                object.save()

        return object


class UserRecToPair(models.Model):
    recommendation = models.ForeignKey('RecommendedUser', editable=False,
                                       null=False, on_delete=models.CASCADE)
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('recommendation', 'pair')

    @staticmethod
    def create(r, k, v, w):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        with transaction.atomic():
            object, created = UserRecToPair.objects.get_or_create(recommendation=r, pair=p,
                                                                  defaults={'weight': w})
            if not created:
                object.weight = w
                object.save()

        return object


class GroupRecToPair(models.Model):
    recommendation = models.ForeignKey('RecommendedGroup', editable=False,
                                       null=False, on_delete=models.CASCADE)
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('recommendation', 'pair')

    @staticmethod
    def create(r, k, v, w):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)

        with transaction.atomic():
            object, created = GroupRecToPair.objects.get_or_create(recommendation=r, pair=p,
                                                                   defaults={'weight': w})
            if not created:
                object.weight = w
                object.save()

        return object


class RecommendedResource(models.Model):
    """ Resource whose attributes cause them to be recommended """
    user = models.ForeignKey(User, editable=False)
    candidate_resource = models.ForeignKey(BaseResource, editable=False,
                                           related_name='resource_recommendation')
    relevance = models.FloatField(editable=False, default=0.0)
    rec_type = models.CharField(max_length=11, null=True,
                                choices=(('Ownership', 'Ownership'), ('Propensity', 'Propensity'),
                                         ('Combination', 'Combination')))
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)
    keywords = models.ManyToManyField(KeyValuePair, editable=False,
                                      related_name='for_resource_rec',
                                      through=ResourceRecToPair,
                                      through_fields=('recommendation', 'pair'))

    class Meta:
        unique_together = ('user', 'candidate_resource', 'rec_type')

    @staticmethod
    def recommend(u, r, t, relevance=None, state=None, keywords=()):

        defaults = {}
        if relevance is not None:
            defaults['relevance'] = relevance
        if state is not None:
            defaults['state'] = state

        with transaction.atomic():
            object, created = RecommendedResource.objects.get_or_create(user=u,
                                                                        candidate_resource=r,
                                                                        rec_type=t,
                                                                        defaults=defaults)
            if not created:
                if relevance is not None:
                    object.relevance = relevance
                if state is not None:
                    object.state = state
                if relevance is not None or state is not None:
                    object.save()

        for r in keywords:
            ResourceRecToPair.create(object, r[0], r[1], r[2])

        return object

    @staticmethod
    def recommend_ids(uid, rid, t, relevance=None, state=None, keywords=()):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = get_resource_by_shortkey(rid, or_404=False)
        RecommendedResource.recommend(u, r, t, relevance=relevance, state=state, keywords=keywords)

    def relate(self, key, value, weight):
        ResourceRecToPair.create(self, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationship = ResourceRecToPair.objects.get(pair=pair, recommendation=self)
        relationship.delete()

    def shown(self):
        self.state = Status.STATUS_SHOWN
        self.save()

    def explored(self):
        self.state = Status.STATUS_EXPLORED
        self.save()
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        self.state = Status.STATUS_DISMISSED
        self.save()

    @staticmethod
    def delete(u, r):
        try:
            record = RecommendedResource.objects.get(user=u, candidate_resource=r)
            record.delete()
        except Exception:
            pass

    @staticmethod
    def clear():
        RecommendedResource.objects.all().delete()
        ResourceRecToPair.objects.all().delete()

    def to_json(self):
        json_obj = {}
        json_obj['user'] = self.user.username
        json_obj['candidate_resource_id'] = self.candidate_resource.short_id
        json_obj['candidate_resource_title'] = self.candidate_resource.title
        json_obj['relevance'] = self.relevance
        json_obj['rec_type'] = self.rec_type
        json_obj['state'] = self.state

        keywords = []
        for keyword in self.keywords.all():
            keywords.append(keyword.to_json())
        json_obj['keywords'] = keywords
        return json_obj


class RecommendedUser(models.Model):
    """ Users whose attributes cause them to be recommended """
    user = models.ForeignKey(User, editable=False)
    candidate_user = models.ForeignKey(User, editable=False, related_name='user_recommendation')
    relevance = models.FloatField(editable=False, default=0.0)
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)

    keywords = models.ManyToManyField(KeyValuePair, editable=False,
                                      related_name='for_user_rec',
                                      through=UserRecToPair,
                                      through_fields=('recommendation', 'pair'))

    class Meta:
        unique_together = ('user', 'candidate_user')

    @staticmethod
    def recommend(u, r, relevance=None, state=None, keywords=()):

        defaults = {}
        if relevance is not None:
            defaults['relevance'] = relevance
        if state is not None:
            defaults['state'] = state

        with transaction.atomic():
            object, created = RecommendedUser.objects.get_or_create(user=u, candidate_user=r,
                                                                    defaults=defaults)
            if not created:
                if relevance is not None:
                    object.relevance = relevance
                if state is not None:
                    object.state = state
                if relevance is not None or state is not None:
                    object.save()

        for r in keywords:
            UserRecToPair.create(object, r[0], r[1], r[2])

        return object

    @staticmethod
    def recommend_ids(uid, rid, relevance=None, state=None, keywords=()):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = user_from_id(rid, or_404=False)
        RecommendedUser.recommend(u, r, relevance=relevance, state=state, keywords=keywords)

    def relate(self, key, value, weight):
        UserRecToPair.create(self, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationship = UserRecToPair.objects.get(pair=pair, recommendation=self)
        relationship.delete()

    def shown(self):
        self.state = Status.STATUS_SHOWN
        self.save()

    def explored(self):
        self.state = Status.STATUS_EXPLORED
        self.save()

    def approved(self):
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        self.state = Status.STATUS_DISMISSED
        self.save()

    @staticmethod
    def delete(u, r):
        try:
            record = RecommendedUser.objects.get(user=u, candidate_user=r)
            record.delete()
        except Exception:
            pass

    @staticmethod
    def clear():
        RecommendedUser.objects.all().delete()
        UserRecToPair.objects.all().delete()

    def to_json(self):
        json_obj = {}
        json_obj['user'] = self.user.username
        json_obj['candidate_user_id'] = self.candidate_user.id
        json_obj['candidate_username'] = self.candidate_resource.username
        json_obj['relevance'] = self.relevance
        json_obj['state'] = self.state

        keywords = []
        for keyword in self.keywords.all():
            keywords.append(keyword.to_json())
        json_obj['keywords'] = keywords
        return json_obj


class RecommendedGroup(models.Model):
    """ Groups whose attributes cause them to be recommended """
    user = models.ForeignKey(User, editable=False)
    candidate_group = models.ForeignKey(Group, editable=False, related_name='group_recommendation')
    relevance = models.FloatField(editable=False, default=0.0)
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)

    keywords = models.ManyToManyField(KeyValuePair, editable=False,
                                      related_name='for_group_rec',
                                      through=GroupRecToPair,
                                      through_fields=('recommendation', 'pair'))

    class Meta:
        unique_together = ('user', 'candidate_group')

    @staticmethod
    def recommend(u, r, relevance=None, state=None, keywords=()):

        defaults = {}
        if relevance is not None:
            defaults['relevance'] = relevance
        if state is not None:
            defaults['state'] = state

        with transaction.atomic():
            object, created = RecommendedGroup.objects.get_or_create(user=u,
                                                                     candidate_group=r,
                                                                     defaults=defaults)
            if not created:
                if relevance is not None:
                    object.relevance = relevance
                if state is not None:
                    object.state = state
                if relevance is not None or state is not None:
                    object.save()

        for r in keywords:
            GroupRecToPair.create(object, r[0], r[1], r[2])

        return object

    @staticmethod
    def recommend_ids(uid, rid, relevance=None, state=None, keywords=()):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = group_from_id(rid, or_404=False)
        RecommendedGroup.recommend(u, r, relevance=relevance, state=state, keywords=())

    def relate(self, key, value, weight):
        GroupRecToPair.create(self, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationship = GroupRecToPair.objects.get(pair=pair, recommendation=self)
        relationship.delete()

    def shown(self):
        self.state = Status.STATUS_SHOWN
        self.save()

    def explored(self):
        self.state = Status.STATUS_EXPLORED
        self.save()

    def approved(self):
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        self.state = Status.STATUS_DISMISSED
        self.save()

    @staticmethod
    def delete(u, r):
        try:
            record = RecommendedGroup.objects.get(user=u, candidate_group=r)
            record.delete()
        except Exception:
            pass

    @staticmethod
    def clear():
        RecommendedGroup.objects.all().delete()
        GroupRecToPair.objects.all().delete()

    def to_json(self):
        json_obj = {}
        json_obj['user'] = self.user.username
        json_obj['candidate_group_id'] = self.candidate_group.id
        json_obj['candidate_group_name'] = self.candidate_group.name
        json_obj['relevance'] = self.relevance
        json_obj['state'] = self.state

        keywords = []
        for keyword in self.keywords.all():
            keywords.append(keyword.to_json())
        json_obj['keywords'] = keywords
        return json_obj


class ResourcePrefToPair(models.Model):
    res_pref = models.ForeignKey('ResourcePreferences', editable=False,
                                  null=False, on_delete=models.CASCADE)
    pref_type = models.CharField(max_length=10, null=True, choices=(('Ownership', 'Ownership'),
                                                                    ('Propensity', 'Propensity')))
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)
    state = models.CharField(max_length=8, choices=(('Seen', 'Seen'), ('Rejected', 'Rejected')),
                             default='Seen')
    # time = models.IntegerField(null=False)

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('res_pref', 'pair', 'pref_type')

    @staticmethod
    def create(u, t, k, v, w, s=None):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        defaults = {}
        if s is not None:
            defaults['state'] = s
        with transaction.atomic():
            object, created = ResourcePrefToPair.objects.\
                                        get_or_create(res_pref=u,
                                                      pref_type=t,
                                                      pair=p,
                                                      weight=w,
                                                      defaults=defaults)
            if not created:
                if s is not None:
                    object.state = s
                object.save()

        return object


class UserPrefToPair(models.Model):
    user_pref = models.ForeignKey('UserPreferences', editable=False,
                                  null=False, on_delete=models.CASCADE)
    pref_type = models.CharField(max_length=10, null=True, choices=(('Ownership', 'Ownership'),
                                                                    ('Propensity', 'Propensity')))
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)
    state = models.CharField(max_length=8, choices=(('Seen', 'Seen'), ('Rejected', 'Rejected')),
                             default='Seen')

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('user_pref', 'pair', 'pref_type')

    @staticmethod
    def create(u, t, k, v, w, s=None):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        defaults = {}
        defaults['weight'] = w
        if s is not None:
            defaults['state'] = s
        with transaction.atomic():
            object, created = UserPrefToPair.objects.\
                                        get_or_create(user_pref=u,
                                                      pref_type=t,
                                                      pair=p,
                                                      defaults=defaults)
            if not created:
                object.weight = w
                if s is not None:
                    object.state = s
                object.save()

        return object


class GroupPrefToPair(models.Model):
    group_pref = models.ForeignKey('GroupPreferences', editable=False,
                                   null=False, on_delete=models.CASCADE)
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)
    # state = models.CharField(max_length=8, choices=(('Seen', 'Seen'), ('Rejected', 'Rejected')),
    #                        default='Seen')

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('group_pref', 'pair')

    @staticmethod
    def create(g, k, v, w):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        # defaults = {}
        # defaults['weight'] = w
        # if s is not None:
        #    defaults['state'] = s
        with transaction.atomic():
            object, created = GroupPrefToPair.objects.get_or_create(group_pref=g, pair=p, weight=w)
            if not created:
                object.weight = w
                # if s is not None:
                #    object.state = s
                object.save()

        return object


class PropensityPrefToPair(models.Model):
    prop_pref = models.ForeignKey('PropensityPreferences', editable=False,
                                  null=False, on_delete=models.CASCADE)
    pref_for = models.CharField(max_length=8, choices=(('Resource', 'Resource'),
                                ('User', 'User'), ('Group', 'Group')))
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)
    state = models.CharField(max_length=8, choices=(('Seen', 'Seen'), ('Rejected', 'Rejected')),
                             default='Seen')

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('prop_pref', 'pref_for', 'pair')

    @staticmethod
    def create(u, pf, k, v, w, s=None):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        defaults = {}
        if s is not None:
            defaults['state'] = s
        with transaction.atomic():
            object, created = PropensityPrefToPair.objects.\
                                        get_or_create(prop_pref=u,
                                                      pref_for=pf,
                                                      pair=p,
                                                      weight=w,
                                                      defaults=defaults)
            if not created:
                if s is not None:
                    object.state = s
                object.save()

        return object


class OwnershipPrefToPair(models.Model):
    own_pref = models.ForeignKey('OwnershipPreferences', editable=False,
                                  null=False, on_delete=models.CASCADE)
    pref_for = models.CharField(max_length=8, choices=(('Resource', 'Resource'),
                                ('User', 'User'), ('Group', 'Group')))
    pair = models.ForeignKey(KeyValuePair, editable=False, null=False, on_delete=models.CASCADE)
    weight = models.FloatField(editable=False, null=False)
    state = models.CharField(max_length=8, choices=(('Seen', 'Seen'), ('Rejected', 'Rejected')),
                             default='Seen')

    class Meta:  # this works with uniqueness of each pair
        unique_together = ('own_pref', 'pref_for', 'pair')

    @staticmethod
    def create(u, pf, k, v, w, s=None):
        """ eliminate duplicates: only thing that can change is weight """
        p = KeyValuePair.create(key=k, value=v)
        defaults = {}
        if s is not None:
            defaults['state'] = s
        with transaction.atomic():
            object, created = OwnershipPrefToPair.objects.\
                                        get_or_create(own_pref=u,
                                                      pref_for=pf,
                                                      pair=p,
                                                      weight=w,
                                                      defaults=defaults)
            if not created:
                if s is not None:
                    object.state = s
                object.save()

        return object


class ResourcePreferences(models.Model):
    user = models.OneToOneField(User, editable=False)
    preferences = models.ManyToManyField(KeyValuePair, editable=False,
                                         related_name='for_res_pref',
                                         through=ResourcePrefToPair,
                                         through_fields=('res_pref', 'pair'))
    interacted_resources = models.ManyToManyField(BaseResource,
                                                  editable=False,
                                                  related_name='interested_resources')

    @staticmethod
    def prefer(u, pref_type, preferences=(), interacted_resources=()):
        with transaction.atomic():
            object, created = ResourcePreferences.objects.get_or_create(user=u)
            if not created:
                object.save()
        for p in preferences:
            ResourcePrefToPair.create(object, pref_type, p[0], p[1], p[2])
        for r in interacted_resources:
            object.interacted_resources.add(r)
        return object

    def relate(self, pref_type, key, value, weight):
        ResourcePrefToPair.create(self, pref_type, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = ResourcePrefToPair.objects.filter(pair=pair, res_pref=self)
        for r in relationships:
            r.delete()

    def reject(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = ResourcePrefToPair.objects.filter(pair=pair, res_pref=self)
        for r in relationships:
            r.state = 'Rejected'
            r.save()

    @staticmethod
    def clear():
        ResourcePreferences.objects.all().delete()
        ResourcePrefToPair.objects.all().delete()


class UserPreferences(models.Model):
    user = models.OneToOneField(User, editable=False)
    preferences = models.ManyToManyField(KeyValuePair, editable=False,
                                         related_name='for_user_pref',
                                         through=UserPrefToPair,
                                         through_fields=('user_pref', 'pair'))
    neighbors = models.ManyToManyField(User, editable=False, related_name='nearest_neighbors')

    @staticmethod
    def prefer(u, pref_type, preferences=(), neighbors=()):
        with transaction.atomic():
            object, created = UserPreferences.objects.get_or_create(user=u)
            if not created:
                object.save()
        for p in preferences:
            UserPrefToPair.create(object, pref_type, p[0], p[1], p[2])
        for n in neighbors:
            object.neighbors.add(n)
        return object

    def relate(self, pref_type, key, value, weight):
        UserPrefToPair.create(self, pref_type, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = UserPrefToPair.objects.filter(pair=pair, user_pref=self)
        for r in relationships:
            r.delete()

    def reject(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = UserPrefToPair.objects.filter(pair=pair, user_pref=self)
        for r in relationships:
            r.state = 'Rejected'
            r.save()

    @staticmethod
    def clear():
        UserPreferences.objects.all().delete()
        UserPrefToPair.objects.all().delete()


class GroupPreferences(models.Model):
    group = models.OneToOneField(Group, editable=False)
    preferences = models.ManyToManyField(KeyValuePair, editable=False,
                                         related_name='for_group_pref',
                                         through=GroupPrefToPair,
                                         through_fields=('group_pref', 'pair'))

    @staticmethod
    def prefer(g, preferences=()):
        with transaction.atomic():
            object, created = GroupPreferences.objects.get_or_create(group=g)
            if not created:
                object.save()
        for p in preferences:
            GroupPrefToPair.create(object, p[0], p[1], p[2])
        return object

    def relate(self, key, value, weight):
        GroupPrefToPair.create(self, key, value, weight)

    def unrelate(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationship = GroupPrefToPair.objects.get(pair=pair, group_pref=self)
        relationship.delete()

    def reject(self, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = GroupPrefToPair.objects.filter(pair=pair, group_pref=self)
        for r in relationships:
            r.state = 'Rejected'
            r.save()

    @staticmethod
    def clear():
        GroupPreferences.objects.all().delete()
        GroupPrefToPair.objects.all().delete()


class PropensityPreferences(models.Model):
    user = models.OneToOneField(User, editable=False)
    preferences = models.ManyToManyField(KeyValuePair, editable=False,
                                         related_name='for_prop_pref',
                                         through=PropensityPrefToPair,
                                         through_fields=('prop_pref', 'pair', 'pref_for'))

    @staticmethod
    def prefer(u, pf, preferences=()):
        with transaction.atomic():
            object, created = PropensityPreferences.objects.get_or_create(user=u)
            if not created:
                object.save()
        for p in preferences:
            PropensityPrefToPair.create(object, pf, p[0], p[1], p[2])
        return object

    def relate(self, pf, key, value, weight):
        PropensityPrefToPair.create(self, pf, key, value, weight)

    def unrelate(self, pf, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = PropensityPrefToPair.objects.filter(prop_pref=self, pair=pair, pref_for=pf)
        for r in relationships:
            r.delete()

    def reject(self, pf, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = PropensityPrefToPair.objects.filter(prop_pref=self, pref_for=pf, pair=pair)
        for r in relationships:
            r.state = 'Rejected'
            r.save()

    @staticmethod
    def clear():
        PropensityPreferences.objects.all().delete()
        PropensityPrefToPair.objects.all().delete()


class OwnershipPreferences(models.Model):
    user = models.OneToOneField(User, editable=False)
    preferences = models.ManyToManyField(KeyValuePair, editable=False,
                                         related_name='for_own_pref',
                                         through=OwnershipPrefToPair,
                                         through_fields=('own_pref', 'pair'))

    @staticmethod
    def prefer(u, pf, preferences=()):
        with transaction.atomic():
            object, created = OwnershipPreferences.objects.get_or_create(user=u)
            if not created:
                object.save()
        for p in preferences:
            OwnershipPrefToPair.create(object, pf, p[0], p[1], p[2])
        return object

    def relate(self, pf, key, value, weight):
        OwnershipPrefToPair.create(self, pf, key, value, weight)

    def unrelate(self, pf, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = OwnershipPrefToPair.objects.filter(own_pref=self, pair=pair, pref_for=pf)
        for r in relationships:
            r.delete()

    def reject(self, pf, key, value):
        pair = KeyValuePair.objects.get(key=key, value=value)
        relationships = OwnershipPrefToPair.objects.filter(own_pref=self, pair=pair, pref_for=pf)
        for r in relationships:
            r.state = 'Rejected'
            r.save()

    @staticmethod
    def clear():
        OwnershipPreferences.objects.all().delete()
        OwnershipPrefToPair.objects.all().delete()


class UserInteractedResources(models.Model):
    user = models.OneToOneField(User, editable=False)
    interacted_resources = models.ManyToManyField(BaseResource,
                                                  editable=False,
                                                  related_name='interacted_resources')

    @staticmethod
    def interact(u, interacted_resources=()):
        with transaction.atomic():
            object, created = UserInteractedResources.objects.get_or_create(user=u)
            if not created:
                object.save()
        for r in interacted_resources:
            object.interacted_resources.add(r)
        return object

    @staticmethod
    def clear():
        UserInteractedResources.objects.all().delete()


class UserNeighbors(models.Model):
    user = models.OneToOneField(User, editable=False)
    neighbors = models.ManyToManyField(User, editable=False, related_name='user_neighbors')

    @staticmethod
    def relate_neighbos(u, neighbors=()):
        with transaction.atomic():
            object, created = UserNeighbors.objects.get_or_create(user=u)
            if not created:
                object.save()
        for n in neighbors:
            object.neighbors.add(n)
        return object

    @staticmethod
    def clear():
        UserNeighbors.objects.all().delete()
