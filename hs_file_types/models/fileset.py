import os
import logging

from django.db import models

from hs_core.models import ResourceFile
from base import AbstractLogicalFile
from generic import GenericFileMetaDataMixin


class FileSetMetaData(GenericFileMetaDataMixin):
    pass


class FileSetLogicalFile(AbstractLogicalFile):
    """ One more files in a specific folder can be part of this aggregation """

    metadata = models.OneToOneField(FileSetMetaData, related_name="logical_file")
    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation
    folder = models.CharField(max_length=4096)
    data_type = "GenericData"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        generic_metadata = FileSetMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=generic_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'File Set Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "FileSetAggregation"

    @property
    def can_contain_folders(self):
        """This aggregation can contain folders"""
        return True

    @property
    def supports_nested_aggregations(self):
        """This aggregation type can contain other aggregations"""
        return True

    @property
    def must_delete(self):
        """
        A helper to decide if the aggregation needs to be deleted when a resource file that is part
        part of the aggregation gets deleted.
        :return True if there is no more than one resource file in the folder (including
        any sub-folders) that represent the aggregation
        """

        # get all res files that exist under the folder that represents this aggregation and under
        # any sub-folders of this aggregation
        res_files = ResourceFile.list_folder(self.resource, folder=self.aggregation_name,
                                             sub_folders=True)
        return len(res_files) < 2

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation - no specific main file"""
        return ".*"

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) == 0:
            # no files
            return ""

        return cls.__name__

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
        """Gets any one resource file from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """Makes all physical files that are in a folder (*folder_path*) part of a file set
        aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        if folder_path is None:
            raise ValueError("Must specify folder to be set as a file set aggregation type")

        _, folder_path = cls._validate_set_file_type_inputs(resource, file_id, folder_path)

        folder_name = folder_path
        if '/' in folder_path:
            folder_name = os.path.basename(folder_path)

        logical_file = cls.initialize(folder_name, resource)
        logical_file.folder = folder_path
        # logical file record gets created in DB
        logical_file.save()
        # make all the files in the selected folder as part of the aggregation
        logical_file.add_resource_files_in_folder(resource, folder_path)
        logical_file.create_aggregation_xml_documents()
        log.info("Fie set aggregation was created for folder:{}.".format(folder_path))

    def add_resource_files_in_folder(self, resource, folder):
        """
        A helper for creating aggregation. Makes all resource files in a given folder and its
        sub folders as part of the aggregation/logical file type
        :param  resource:  an instance of CompositeResource
        :param  folder: folder from which all files need to be made part of this aggregation
        """

        # get all resource files that in folder *folder* and all its sub folders
        res_files = ResourceFile.list_folder(resource=resource, folder=folder, sub_folders=True)

        for res_file in res_files:
            if not res_file.has_logical_file:
                self.add_resource_file(res_file)
            elif res_file.logical_file.is_fileset and not \
                    res_file.logical_file.aggregation_name.startswith(folder):
                # resource file that is part of a fileset aggregation where the fileset aggregation
                # is not a sub folder of *folder* needs to be made part of this new fileset
                # aggregation
                self.add_resource_file(res_file)

        return res_files

    def get_children(self):
        child_aggregations = []
        for aggr in self.resource.logical_files:
            parent_aggr = aggr.get_parent()
            if parent_aggr is not None and parent_aggr == self:
                child_aggregations.append(aggr)

        return child_aggregations
