import json
import logging
import os
import random
import shutil
from uuid import uuid4

from django.contrib.postgres.fields import JSONField
from django.db import models

from hs_core.models import ResourceFile
from hydroshare import settings

from hs_file_types.models import AbstractLogicalFile
from hs_file_types.models.base import FileTypeContext, SCHEMA_JSON_FILE_ENDSWITH


class AbstractModelLogicalFile(AbstractLogicalFile):
    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation. Where folder is not set, the one file that is part
    # of this aggregation becomes the aggregation name
    folder = models.CharField(max_length=4096, null=True, blank=True)

    # metadata schema (in json format) for model instance aggregation
    # metadata for the model instance aggregation is validated based on this schema
    metadata_schema_json = JSONField(default=dict)

    class Meta:
        abstract = True

    @property
    def schema_short_file_path(self):
        """File path of the aggregation metadata schema file relative to {resource_id}/data/contents/
        """

        json_file_name = self.aggregation_name
        if "/" in json_file_name:
            json_file_name = os.path.basename(json_file_name)

        json_file_name, _ = os.path.splitext(json_file_name)

        json_file_name += SCHEMA_JSON_FILE_ENDSWITH

        if self.folder:
            file_folder = self.folder
        else:
            file_folder = self.files.first().file_folder
        if file_folder:
            json_file_name = os.path.join(file_folder, json_file_name)

        return json_file_name

    @property
    def schema_file_path(self):
        """Full path of the aggregation metadata schema json file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.schema_short_file_path)

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
        """Makes all physical files that are in a folder (*folder_path*) part of a model program/instance
        aggregation type or a single file (*file_id*) part of this aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=None,
                             is_temp_file=False) as ft_ctx:

            if folder_path:
                res_files = []
                dataset_name = folder_path
                if '/' in folder_path:
                    dataset_name = os.path.basename(folder_path)
            else:
                res_file = ft_ctx.res_file
                res_files = [res_file]
                folder_path = res_file.file_folder
                dataset_name, _ = os.path.splitext(res_file.file_name)

            # remove any previously associated logical files from the files
            # before making them part of this new logical file
            for res_file in res_files:
                if res_file.has_logical_file:
                    res_file.logical_file_content_object = None
                    res_file.save()

            # create a model program/instance logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=res_files,
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)

            if folder_path and file_id is None:
                logical_file.folder = folder_path
                logical_file.save()
                # make all the files in the selected folder as part of the aggregation
                logical_file.add_resource_files_in_folder(resource, folder_path)
                log.info("{0} aggregation was created for folder:{1}.".format(logical_file.data_type, folder_path))
            else:
                log.info("{0} aggregation was created for file:{1}.".format(logical_file.data_type,
                                                                            res_file.storage_path))
            ft_ctx.logical_file = logical_file
        return logical_file

    def create_metadata_schema_json_file(self):
        """Creates aggregation metadata schema json file """

        if not self.metadata_schema_json:
            return

        # create a temp dir where the json file will be temporarily saved before copying to iRODS
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_irods_storage()

        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)

        # create json schema file for the aggregation
        json_from_file_name = os.path.join(tmpdir, 'schema.json')
        try:
            with open(json_from_file_name, 'w') as out:
                json_schema = json.dumps(self.metadata_schema_json, indent=4)
                out.write(json_schema)
            to_file_name = self.schema_file_path
            istorage.saveFile(json_from_file_name, to_file_name, True)
        finally:
            shutil.rmtree(tmpdir)

    @classmethod
    def can_set_folder_to_aggregation(cls, resource, dir_path):
        """helper to check if the specified folder *dir_path* can be set to ModelProgram or ModelInstance aggregation
        """

        # checking target folder for any aggregation
        if resource.get_folder_aggregation_object(dir_path) is not None:
            # target folder is already an aggregation
            return False

        aggregation_path = dir_path[len(resource.file_path) + 1:]
        # checking sub-folders for fileset aggregation
        # check that we don't have any sub folder of dir_path representing a fileset aggregation
        # so that we can avoid nesting a fileset aggregation inside a model program or model instance aggregation
        if resource.filesetlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        if cls.__name__ == "ModelProgramLogicalFile":
            # checking sub-folders for model program aggregation
            # check that we don't have any sub folder of dir_path representing a model program aggregation
            # so that we can avoid nesting a model program aggregation inside a model
            # program aggregation
            if resource.modelprogramlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
                return False

        # checking sub-folders for model instance aggregation
        # check that we don't have any sub folder of dir_path representing a model instance aggregation
        # so that we can avoid nesting a model instance aggregation inside a model program aggregation
        if resource.modelinstancelogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        # check the first parent folder that represents an aggregation
        irods_path = dir_path
        if resource.is_federated:
            irods_path = os.path.join(resource.resource_federation_path, irods_path)

        # get the parent folder path
        path = os.path.dirname(dir_path)
        parent_aggregation = None
        while '/' in path:
            if path == resource.file_path:
                break
            parent_aggregation = resource.get_folder_aggregation_object(path)
            if parent_aggregation is not None:
                # this is the first parent folder that represents an aggregation
                break
            # get the next parent folder path
            path = os.path.dirname(path)

        if parent_aggregation is not None:
            if parent_aggregation.is_fileset:
                # check that all resource files under the target folder 'dir_path' are associated with fileset only
                files_in_path = ResourceFile.list_folder(resource, folder=irods_path, sub_folders=True)
                # if all the resource files are associated with fileset then we can set the folder to model program
                # or model instance aggregation
                if files_in_path:
                    return all(res_file.has_logical_file and res_file.logical_file.is_fileset for
                               res_file in files_in_path)
                return False
            else:
                return False
        else:
            # none of the parent folders represents an aggregation
            # check the files in the target path
            files_in_path = ResourceFile.list_folder(resource, folder=irods_path, sub_folders=True)

            if files_in_path:
                # if none of the resource files in the target path has logical file then we can set the folder
                # to model program or model instance aggregation
                if cls.__name__ == "ModelProgramLogicalFile":
                    # if none of the resource files in the target path has logical file then we can set the folder
                    # to model program aggregation
                    return not any(res_file.has_logical_file for res_file in files_in_path)
                else:
                    # if any of the files is part of a model instance aggr or fileset - folder can't be
                    # set to model instance
                    return not any(res_file.has_logical_file and (res_file.logical_file.is_model_instance or
                                                                  res_file.logical_file.is_fileset) for
                                   res_file in files_in_path)

            # path has no files - can't set the folder to aggregation
            return False
