from django.db import models


class University(models.Model):
    country_code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "universities"


class SubjectArea(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "subject areas"


class UncategorizedTerm(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "uncategorized terms"
