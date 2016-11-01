# coding=utf-8
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from hs_core.models import Coverage

from base import AbstractFileMetaData, AbstractLogicalFile


class GenericFileMetaData(AbstractFileMetaData):
    _coverages = GenericRelation(Coverage)

    @classmethod
    def get_supported_element_names(cls):
        return ['Coverage']

    @property
    def coverage(self):
        return self._coverages.all().first()

    def delete_all_elements(self):
        if self.coverage:
            self.coverage.delete()

    def has_all_required_elements(self):
        if not self.coverage:
            return False

        return True


class GenericLogicalFile(AbstractLogicalFile):
    # each resource file is assigned this logical file type on upload to Composite Resource
    metadata = models.OneToOneField(GenericFileMetaData, related_name="logical_file")

    @classmethod
    def create(cls):
        generic_metadata = GenericFileMetaData.objects.create()
        return cls.objects.create(metadata=generic_metadata)
