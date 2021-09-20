
from django.db import models
from django.contrib.auth.models import User, Group


class person(models.Model):
    name = User.objects.all()
    # name  = models.CharField(max_length=200)

    def __str__(self):
        return self.name
