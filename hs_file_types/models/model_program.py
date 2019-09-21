import os
import logging

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models

from hs_core.models import ResourceFile
from base import AbstractLogicalFile, FileTypeContext
from generic import GenericFileMetaDataMixin


class ModelProgramResourceFileType(models.Model):
    RELEASE_NOTES = 1
    DOCUMENTATION = 2
    SOFTWARE = 3
    ENGINE = 4
    CHOICES = (
        (RELEASE_NOTES, 'Release Notes'),
        (DOCUMENTATION, 'Documentation'),
        (SOFTWARE, 'Software'),
        (ENGINE, "Computational Engine")
    )
    file_type = models.PositiveSmallIntegerField(choices=CHOICES)
    res_file = models.ForeignKey(ResourceFile, on_delete=models.CASCADE)
    mp_metadata = models.ForeignKey('ModelProgramFileMetaData', on_delete=models.CASCADE, related_name='mp_file_types')

    @classmethod
    def type_from_string(cls, type_string):
        type_map = {'release notes': cls.RELEASE_NOTES, 'documentation': cls.DOCUMENTATION,
                    'software': cls.SOFTWARE, 'engine': cls.ENGINE}

        type_string = type_string.lower()
        return type_map.get(type_string, None)


class ModelProgramFileMetaData(GenericFileMetaDataMixin):
    # version
    version = models.CharField(verbose_name='Version', null=True, blank=True, max_length=255,
                               help_text='The software version or build number of the model')

    # program language
    programming_languages = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[],
                                       help_text="The programming language(s) that the model is written in")

    # operating system
    operating_systems = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[],
                                   help_text="Compatible operating systems to setup and run the model")

    # release date
    release_date = models.DateField(verbose_name='Release Date', null=True, blank=True,
                                    help_text='The date that this version of the model was released')

    # web page
    website = models.URLField(verbose_name='Website', null=True, blank=True, max_length=255,
                              help_text='A URL to the website maintained by the model developers')

    # repository
    code_repository = models.URLField(verbose_name='Software Repository', null=True,
                                      blank=True, max_length=255,
                                      help_text='A URL to the source code repository (e.g. git, mercurial, svn)')


class ModelProgramLogicalFile(AbstractLogicalFile):
    """ One file or more than one files in a specific folder can be part of this aggregation """

    metadata = models.OneToOneField(ModelProgramFileMetaData, related_name="logical_file")

    # metadata schema (in json format) for model instance aggregation to which this aggregation
    # can be related. metadata for the related model instance aggregation is validated based on this schema
    mi_schema_json = JSONField(default=dict)

    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation. Where folder is not set, the one file that is part
    # of this aggregation becomes the aggregation name
    folder = models.CharField(max_length=4096, null=True, blank=True)
    data_type = "Model Program"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mp_metadata = ModelProgramFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mp_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Program Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelProgramLogicalFile"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return "Model Program"

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
        """Makes all physical files that are in a folder (*folder_path*) part of a model program
        aggregation type or a single file (*file_id*) part of this aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=None,
                             is_temp_file=False) as ft_ctx:

            if folder_path is not None:
                res_files = []
                dataset_name = folder_path
                if '/' in folder_path:
                    dataset_name = os.path.basename(folder_path)
            else:
                res_file = ft_ctx.res_file
                res_files = [res_file]
                folder_path = res_file.file_folder
                dataset_name, _ = os.path.splitext(res_file.file_name)

            # create a model program logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=res_files,
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)

            if folder_path is not None:
                logical_file.folder = folder_path
                logical_file.save()
                # make all the files in the selected folder as part of the aggregation
                logical_file.add_resource_files_in_folder(resource, folder_path)
                log.info("Model Program aggregation was created for folder:{}.".format(folder_path))
            else:
                log.info("Model Program aggregation was created for file:{}.".format(res_file.storage_path))
            ft_ctx.logical_file = logical_file


