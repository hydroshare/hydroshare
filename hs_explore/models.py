from django.db import models, transaction
from hs_core.models import BaseResource
from django.contrib.auth.models import User
from hs_core.hydroshare import user_from_id, get_resource_by_shortkey


class Status(object):
    STATUS_NEW = 1
    STATUS_VIEWED = 2
    STATUS_APPROVED = 3
    STATUS_DISMISSED = 4
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_VIEWED, 'Viewed'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DISMISSED, 'Dismissed')
    )


class Recommend(models.Model):
    user = models.ForeignKey(User, editable=False)
    resource = models.ForeignKey(BaseResource, editable=False)
    relevance = models.FloatField(editable=False, default=0.0)
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)

    class Meta:
        unique_together = ('user', 'resource')

    @classmethod
    def recommend(u, r, relevance=0.0):
        with transaction.atomic:
            Recommend.objects.get_or_create(user=u, resource=r,
                                            default={'relevance': relevance})

    @classmethod
    def recommend_ids(uid, rid, relevance=0.0):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = get_resource_by_shortkey(rid, or_404=False)
        Recommend.recommend(u, r, relevance)

    def viewed(self):
        self.state = Status.STATUS_VIEWED
        self.save()

    def approved(self):
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        self.state = Status.STATUS_DISMISSED
        self.save()

    @classmethod
    def delete(u, r):
        try:
            record = Recommend.objects.get(user=u, resource=r)
            record.delete()
        except Exception:
            pass

    @classmethod
    def clear():
        for r in Recommend.objects.all():
            r.delete()
