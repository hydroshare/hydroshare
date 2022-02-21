from django.db import models


# We need a precise simulation of what iRODS does for HydroShare.
# This includes memorizing AVUs and returning what was memorized.
# At present, the AVUs are only allocated at the root level of a resource,
# i.e., at the level where the resource root folders are.


class LinuxAVU(models.Model):
    """ Simulate iRODS AVU functions in Linux """
    path = models.CharField(max_length=1024)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)

    @classmethod
    def set(cls, p, n, v, u):
        record, create = cls.objects.get_or_create(defaults={'value': v, 'unit': u},
                                                   path=p, name=n)
        if not create:
            record.unit = u
            record.value = v
            record.save()

    @classmethod
    def get(cls, p, n):
        try:
            record = cls.object.get(path=p, name=n)
            return record
        except cls.DoesNotExist:
            return None

    @classmethod
    def remove(cls, p, n):
        try:
            record = cls.object.get(path=p, name=n)
            record.delete()
        except cls.DoesNotExist:
            pass

    class Meta:
        unique_together = ('path', 'name')
