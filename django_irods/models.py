from django.db import models as m
from django.contrib.auth.models import User


class RodsEnvironment(m.Model):
    owner = m.ForeignKey(User, on_delete=m.CASCADE)
    host = m.CharField(verbose_name='Hostname', max_length=255)
    port = m.IntegerField()
    def_res = m.CharField(verbose_name="Default resource", max_length=255)
    home_coll = m.CharField(verbose_name="Home collection", max_length=255)
    cwd = m.TextField(verbose_name="Working directory")
    username = m.CharField(max_length=255)
    zone = m.TextField()
    auth = m.TextField(verbose_name='Password')

    def __unicode__(self):
        return '{username}@{host}:{port}//{def_res}/{home_coll}'.format(
            username=self.username,
            host=self.host,
            port=self.port,
            def_res=self.def_res,
            home_coll=self.home_coll
        )

    class Meta:
        verbose_name = 'iRODS Environment'
