# -*- coding: utf-8 -*-


from django.db import models
import urllib.request
import urllib.error
import urllib.parse
import json


class ODM2Variable(models.Model):
    """Maintain a cached copy of the ODM2 variable name database inside HydroShare
    This maintains a copy of the ODM2 database maintained at odm2.org.
    It sets the id of every record to the id identified by odm2.org in order to
    pick up versions when synchronizing.
    """

    name = models.CharField(
        max_length=256,
        editable=False,
        null=False,
        blank=False,
        help_text="Variable name",
    )
    definition = models.TextField(
        editable=False, null=False, blank=False, help_text="Definition of variable name"
    )
    resource_uri = models.TextField(
        editable=False,
        null=False,
        blank=True,
        help_text="URI of variable name relative to ODM2 server",
    )
    provenance_uri = models.TextField(
        editable=False,
        null=False,
        blank=True,
        help_text="URI describing provenance of variable name",
    )

    def __str__(self):
        return self.name

    @classmethod
    def sync(cls, uri="http://vocabulary.odm2.org/api/v1/variablename/?format:json"):
        response = urllib.request.urlopen(uri)
        str = response.read()
        data = json.loads(str)
        for d in data["objects"]:
            try:
                record = ODM2Variable.objects.get(id=int(d["vocabulary_id"]))
                if d["vocabulary_status"] == "Current":
                    if (
                        d["name"] != record.name
                        or d["definition"] != record.definition
                        or d["resource_uri"] != record.resource_uri
                        or d["provenance_uri"] != record.provenance_uri
                    ):
                        record.name = d["name"]
                        record.definition = d["definition"]
                        record.resource_uri = d["resource_uri"]
                        record.provenance_uri = d["provenance_uri"]
                        record.save()
                else:
                    record.delete()  # stale record
            except ODM2Variable.DoesNotExist:
                if d["vocabulary_status"] == "Current":
                    record = ODM2Variable()
                    record.name = d["name"]
                    record.definition = d["definition"]
                    record.resource_uri = d["resource_uri"]
                    record.provenance_uri = d["provenance_uri"]
                    record.id = int(d["vocabulary_id"])
                    record.save()

    @classmethod
    def search(cls, prefix):
        return ODM2Variable.objects.filter(name__startswith=prefix).order_by("name")

    @classmethod
    def all(cls):
        term_names = ODM2Variable.objects.all().values_list("name").order_by("name")
        formatted_terms = [
            str(t[0].replace(",", " -")) for t in term_names if not t[0][0].isdigit()
        ]
        return formatted_terms
