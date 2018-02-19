from django.db import models, transaction
from hs_core.models import BaseResource
from django.contrib.auth.models import User


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
    user = models.ForeignKey(User)
    resource = models.ForeignKey(BaseResource)
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW)

    class Meta:
        unique_together = ('user', 'resource')

    @classmethod
    def recommend(u, r):
        with transaction.atomic:
            Recommend.objects.get_or_create(user=u, resource=r)

    def viewed(self):
        self.state = Status.STATUS_VIEWED
        self.save()

    def approved(self):
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        self.state = Status.STATUS_DISMISSED
        self.save()
