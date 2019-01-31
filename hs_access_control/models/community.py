from django.contrib.auth.models import User, Group
from django.db import models

###################################
# Communities of groups
###################################


class Community(models.Model):
    """ a placeholder class for a community of groups """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    purpose = models.TextField(null=True, blank=True)
    auto_approve = models.BooleanField(null=False, default=False, blank=False, editable=False)
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    picture = models.ImageField(upload_to='community', null=True, blank=True)

    @property
    def member_groups(self):
        return Group.objects.filter(gaccess__active=True, g2gcp__community=self)

    @property
    def member_users(self):
        return User.objects.filter(is_active=True, u2ucp__community=self)

    def get_groups_with_explicit_access(self, privilege):
        return Group.objects.filter(g2gcp__community=self, g2gcp__privilege=privilege)
