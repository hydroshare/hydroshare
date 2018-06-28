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
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)

    keywords = models.ManyToManyField(KeyValuePair, editable=False,
                                      related_name='for_resource_rec',
                                      through=ResourceRecToPair,
                                      through_fields=('recommendation', 'pair'))

    class Meta:
        unique_together = ('user', 'candidate_resource')

    @staticmethod
    def recommend(u, r, relevance=None, state=None, keywords=()):

        defaults = {}
        if relevance is not None:
            defaults['relevance'] = relevance
        if state is not None:
            defaults['state'] = state

        with transaction.atomic():
            object, created = RecommendedResource.objects.get_or_create(user=u,
                                                                        candidate_resource=r,
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
    def recommend_ids(uid, rid, relevance=None, state=None, keywords=()):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = get_resource_by_shortkey(rid, or_404=False)
        RecommendedResource.recommend(u, r, relevance=relevance, state=state, keywords=keywords)

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

    def approved(self):
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

class UserPreferences(models.Model):
    user = models.ForeignKey(User, editable=False)
    preferences = models.TextField(null=True)

    class Meta:
        unique_together = ('user', 'preferences')

    @staticmethod
    def prefer(u, p):
        with transaction.atomic():
            object, created = UserPreferences.objects.get_or_create(user=u,preferences=p)
            if not created:
                object.save()
        return object
    @staticmethod
    def clear():
        UserPreferences.objects.all().delte()
