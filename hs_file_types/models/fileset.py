import os
import logging

from django.db import models

from hs_core.models import ResourceFile
from .base import AbstractLogicalFile, FileTypeContext
from .generic import GenericFileMetaDataMixin


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

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types (there is no equivalent native type
        for File Set).
        """
        return "File Set"

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
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """Makes all physical files that are in a folder (*folder_path*) part of a file set
        aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=None,
                             is_temp_file=False) as ft_ctx:

            folder_name = folder_path
            if '/' in folder_path:
                folder_name = os.path.basename(folder_path)

            # create a fileset logical file object
            logical_file = cls.create_aggregation(dataset_name=folder_name,
                                                  resource=resource,
                                                  res_files=[],
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)

            logical_file.folder = folder_path
            logical_file.save()
            # make all the files in the selected folder as part of the aggregation
            logical_file.add_resource_files_in_folder(resource, folder_path)
            ft_ctx.logical_file = logical_file
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
            elif res_file.logical_file.is_fileset and not res_file.logical_file.aggregation_name.startswith(folder):
                # resource file that is part of a fileset aggregation where the fileset aggregation
                # is not a sub folder of *folder* needs to be made part of this new fileset
                # aggregation
                self.add_resource_file(res_file)

        return res_files

    def update_temporal_coverage(self):
        """Updates temporal coverage of this fileset instance based on the contained temporal
        coverages of aggregations (file type). Note: This action will overwrite any existing
        fileset temporal coverage data.
        """

        from ..utils import update_target_temporal_coverage

        update_target_temporal_coverage(self)

    def update_spatial_coverage(self):
        """Updates spatial coverage of this fileset instance based on the contained spatial
        coverages of aggregations (file type). Note: This action will overwrite any existing
        fileset spatial coverage data.
        """
        from ..utils import update_target_spatial_coverage

        update_target_spatial_coverage(self)

    def update_coverage(self):
        """Update fileset spatial and temporal coverage based on the corresponding coverages
        from all the contained aggregations (logical file) only if the fileset coverage is not
        already set"""

        # update fileset spatial coverage only if there is no spatial coverage already
        if self.metadata.spatial_coverage is None:
            self.update_spatial_coverage()

        # update fileset temporal coverage only if there is no temporal coverage already
        if self.metadata.temporal_coverage is None:
            self.update_temporal_coverage()

    def get_children(self):
        """Return a list of aggregation that this (self) aggregation contains"""
        child_aggregations = []
        for aggr in self.resource.logical_files:
            parent_aggr = aggr.get_parent()
            if parent_aggr is not None and parent_aggr == self:
                child_aggregations.append(aggr)

        return child_aggregations

    def update_folder(self, new_folder, old_folder):
        """Update folder attribute of this fileset (self) and folder attribute of all fileset
        aggregations that exist under self.
        When folder name of a fileset aggregation is changed, the folder attribute of all nested
        fileset aggregations needs to be updated.
        :param  new_folder:  new folder path of the self
        :param  old_folder:  original folder path of the self
        """

        new_folder = new_folder.rstrip('/')
        old_folder = old_folder.rstrip('/')

        # update child fileset aggregations of self
        for child_aggr in self.get_children():
            if child_aggr.is_fileset:
                child_aggr.folder = new_folder + child_aggr.folder[len(old_folder):]
                child_aggr.save()

        # update self
        self.folder = new_folder + self.folder[len(old_folder):]
        self.save()
