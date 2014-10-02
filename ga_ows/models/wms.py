from django.contrib.gis.db import models

class OGRDatasetCollection(models.Model):
    name = models.CharField(max_length=255, blank=False)

class OGRDataset(models.Model):
    collection = models.ForeignKey(OGRDatasetCollection, null=False)
    location = models.TextField(blank=False, null=False)
    checksum = models.CharField(max_length=32, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False, db_index=True)
    human_name = models.TextField(blank=True, null=True, db_index=True)
    extent = models.PolygonField(srid=4326)

class OGRLayer(models.Model):
    dataset = models.ForeignKey(OGRDataset)
    name = models.CharField(max_length=255, db_index=True)
    human_name = models.TextField(blank=True, null=True, db_index=True)
    extent = models.PolygonField(srid=4326)

