import logging
import os

from django.core.exceptions import ValidationError
from django.db import models

from hs_core.models import ResourceFile
from .base import AbstractLogicalFile, FileTypeContext, NestedLogicalFileMixin
from .generic import GenericFileMetaDataMixin
from ..enums import AggregationMetaFilePath


class FileSetMetaData(GenericFileMetaDataMixin):
    pass


class FileSetLogicalFile(NestedLogicalFileMixin, AbstractLogicalFile):
    """ One more files in a specific folder can be part of this aggregation """

    metadata = models.OneToOneField(FileSetMetaData, on_delete=models.CASCADE, related_name="logical_file")
    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation
    folder = models.CharField(max_length=4096)
    data_type = "GenericData"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        generic_metadata = FileSetMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=generic_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'File Set Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_term_label():
        return "File Set Aggregation"

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

    @property
    def aggregation_name(self):
        """Returns aggregation name as per the aggregation naming rule defined in issue#2568"""

        return self.folder

    def can_contain_aggregation(self, aggregation):
        # fileset can contain any aggregation
        return True

    def can_be_deleted_on_file_delete(self):
        """fileset aggregation is not deleted on delete of any or all of the resource files that
        are part of the fileset aggregation"""
        return False

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
    def supports_folder_based_aggregation(cls):
        """A fileset aggregation must be created from a folder"""
        return True

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets any one resource file from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    @classmethod
    def can_set_folder_to_aggregation(cls, resource, dir_path, aggregations=None):
        """Checks if the specified folder *dir_path* can be set to Fileset aggregation

        :return
        If the specified folder is already represents an aggregation, return False
        if the specified folder does not contain any files, return False
        if any of the parent folders is a model program aggregation, return False
        if any of the parent folders is a model instance aggregation, return False
        otherwise, return True

        Note: A fileset aggregation is not allowed inside a model program or model instance aggregation. One
        fileset aggregation can contain any other aggregation types including fileset aggregation
        """

        if resource.get_folder_aggregation_object(dir_path, aggregations=aggregations) is not None:
            # target folder is already an aggregation
            return False

        # checking all parent folders
        path = os.path.dirname(dir_path)
        while '/' in path:
            parent_aggr = resource.get_folder_aggregation_object(path, aggregations=aggregations)
            if parent_aggr is not None and (parent_aggr.is_model_program or parent_aggr.is_model_instance):
                # avoid creating a fileset aggregation inside a model program/instance aggregation folder
                return False
            # go to next parent folder
            path = os.path.dirname(path)

        s3_path = dir_path

        files_in_path = ResourceFile.list_folder(resource, folder=s3_path, sub_folders=True)
        # if there are any files in the dir_path, we can set the folder to fileset aggregation
        return len(files_in_path) > 0

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

            msg = "Fileset aggregation. Error when creating aggregation. Error:{}"
            folder_name = folder_path
            if '/' in folder_path:
                folder_name = os.path.basename(folder_path)

            # create a fileset logical file object
            logical_file = cls.create_aggregation(dataset_name=folder_name,
                                                  resource=resource,
                                                  res_files=[],
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)

            try:
                logical_file.folder = folder_path
                logical_file.save()
                # make all the files in the selected folder as part of the aggregation
                logical_file.add_resource_files_in_folder(resource, folder_path)
                log.info("File set aggregation was created for folder:{}.".format(folder_path))
                ft_ctx.logical_file = logical_file
            except Exception as ex:
                logical_file.remove_aggregation()
                msg = msg.format(str(ex))
                log.exception(msg)
                raise ValidationError(msg)

            return logical_file

    def xml_file_short_path(self, resmap=True):
        """File path of the aggregation metadata or map xml file relative
        to {resource_id}/data/contents/
        :param  resmap  If true file path for aggregation resmap xml file, otherwise file path for
        aggregation metadata file is returned
        """

        xml_file_name = self.get_xml_file_name(resmap=resmap)
        file_folder = self.folder
        xml_file_name = os.path.join(file_folder, xml_file_name)
        return xml_file_name

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
                self.add_resource_file(res_file, set_metadata_dirty=False)
            elif res_file.logical_file.is_fileset and not res_file.logical_file.aggregation_name.startswith(folder):
                # resource file that is part of a fileset aggregation where the fileset aggregation
                # is not a sub folder of *folder* needs to be made part of this new fileset
                # aggregation
                self.add_resource_file(res_file, set_metadata_dirty=False)
        self.set_metadata_dirty()
        return res_files

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
                child_aggr.save(update_fields=["folder"])

        # update self
        self.folder = new_folder + self.folder[len(old_folder):]
        self.save()

    def set_metadata_dirty(self):
        super(FileSetLogicalFile, self).set_metadata_dirty()
        for child_aggr in self.get_children():
            child_aggr.set_metadata_dirty()

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(FileSetLogicalFile, self).create_aggregation_xml_documents(create_map_xml=create_map_xml)
        for child_aggr in self.get_children():
            child_aggr.create_aggregation_xml_documents(create_map_xml=create_map_xml)

    @property
    def metadata_json_file_path(self):
        """Returns the url path of the aggregation metadata json file"""

        meta_file_path = os.path.join(self.resource.file_path, self.folder,
                                      AggregationMetaFilePath.METADATA_JSON_FILE_NAME)
        return meta_file_path

    def save_metadata_json_file(self):
        """Creates aggregation metadata json file and saves it to S3. If the aggregation contains other
        aggregations, it also saves the metadata json file for each of those aggregations."""

        from hs_file_types.utils import save_metadata_json_file as utils_save_metadata_json_file

        metadata_json = self.metadata.to_json()
        to_file_name = self.metadata_json_file_path
        utils_save_metadata_json_file(self.resource.get_s3_storage(), metadata_json, to_file_name)
        for child_aggr in self.get_children():
            child_aggr.save_metadata_json_file()

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(FileSetLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.folder = self.folder
        copy_of_logical_file.save()
        return copy_of_logical_file
