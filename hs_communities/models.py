from django.db import models


class Topics(models.Model):
    """
    Temporary class for demonstrating topics for Critical-Zone
    """
    name = models.CharField(max_length=200)
