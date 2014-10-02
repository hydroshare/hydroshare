from django.contrib.gis.db.models import *

class WFSPointTest(Model):
    geom = PointField()
    name = CharField(max_length=16)
    state = CharField(max_length=16)
    in_cluster = IntegerField()

    objects = GeoManager()

    def __str__(self):
        return '{name} {state} {in_cluster} - {geom}'.format(name=self.name, state=self.state, in_cluster=self.in_cluster, geom=self.geom)

    class Meta:
        app_label = 'ga_ows'

class WFSLineStringTest(Model):
    geom = LineStringField()
    name = CharField(max_length=16)
    state = CharField(max_length=2)
    in_cluster = IntegerField()

    objects = GeoManager()

    class Meta:
        app_label = 'ga_ows'


