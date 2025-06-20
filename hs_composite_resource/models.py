import logging
import os
from typing import Union
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceFile, ResourceManager, resource_processor
from hs_file_types.models import (
    FileSetLogicalFile,
    GenericLogicalFile,
    GeoFeatureLogicalFile,
    GeoRasterLogicalFile,
    ModelInstanceLogicalFile,
    ModelProgramLogicalFile,
    ModelProgramResourceFileType,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    CSVLogicalFile,
)
from hs_file_types.enums import AggregationMetaFilePath
from hs_file_types.utils import update_target_spatial_coverage, update_target_temporal_coverage

logger = logging.getLogger(__name__)

AggregationType = Union[
    GenericLogicalFile,
    FileSetLogicalFile,
    GeoFeatureLogicalFile,
    GeoRasterLogicalFile,
    ModelProgramLogicalFile,
    ModelInstanceLogicalFile,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    CSVLogicalFile,
]


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

    # used during discovery as well as in all other places in UI where resource type is displayed
    display_name = 'Resource'

    class Meta:
        verbose_name = 'Composite Resource'
        proxy = True

    @property
    def can_be_public_or_discoverable(self):
        # resource level metadata check
        if not super(CompositeResource, self).can_be_public_or_discoverable:
            return False

        # logical file level metadata check
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False

        return True

    @property
    def has_required_metadata(self):
        """Return True only if all required metadata is present."""
        if not super(CompositeResource, self).has_required_metadata:
            return False

        for f in self.logical_files:
            if not f.metadata.has_all_required_elements():
                return False
        return True

    @property
    def logical_files(self):
        """A generator to access each of the logical files of this resource"""

        for lf in self.filesetlogicalfile_set.all():
            yield lf
        for lf in self.genericlogicalfile_set.all():
            yield lf
        for lf in self.geofeaturelogicalfile_set.all():
            yield lf
        for lf in self.netcdflogicalfile_set.all():
            yield lf
        for lf in self.georasterlogicalfile_set.all():
            yield lf
        for lf in self.reftimeserieslogicalfile_set.all():
            yield lf
        for lf in self.timeserieslogicalfile_set.all():
            yield lf
        for lf in self.modelprogramlogicalfile_set.all():
            yield lf
        for lf in self.modelinstancelogicalfile_set.all():
            yield lf
        for lf in self.csvlogicalfile_set.all():
            yield lf

    @property
    def aggregation_types(self):
        """Gets a list of all aggregation types that currently exist in this resource"""
        aggr_types = []
        aggr_type_names = []
        for lf in self.logical_files:
            if lf.type_name() not in aggr_type_names:
                aggr_type_names.append(lf.type_name())
                aggr_type = lf.get_aggregation_display_name().split(":")[0]
                aggr_types.append(aggr_type)
        return aggr_types

    @property
    def aggregation_type_names(self):
        """Gets a list of all aggregation type names that currently exist in this resource
        """
        aggr_type_names = []
        for lf in self.logical_files:
            if lf.type_name not in aggr_type_names:
                aggr_type_names.append(lf.type_name())
        return aggr_type_names

    def get_logical_files(self, logical_file_class_name):
        """Get a list of logical files (aggregations) for a specified logical file class name."""

        class_name_to_query_mappings = {
            FileSetLogicalFile.type_name(): self.filesetlogicalfile_set.all(),
            GenericLogicalFile.type_name(): self.genericlogicalfile_set.all(),
            GeoFeatureLogicalFile.type_name(): self.geofeaturelogicalfile_set.all(),
            GeoRasterLogicalFile.type_name(): self.georasterlogicalfile_set.all(),
            ModelInstanceLogicalFile.type_name(): self.modelinstancelogicalfile_set.all(),
            ModelProgramLogicalFile.type_name(): self.modelprogramlogicalfile_set.all(),
            NetCDFLogicalFile.type_name(): self.netcdflogicalfile_set.all(),
            TimeSeriesLogicalFile.type_name(): self.timeserieslogicalfile_set.all(),
            RefTimeseriesLogicalFile.type_name(): self.reftimeserieslogicalfile_set.all(),
            CSVLogicalFile.type_name(): self.csvlogicalfile_set.all(),
        }

        if logical_file_class_name in class_name_to_query_mappings:
            return class_name_to_query_mappings[logical_file_class_name]

        raise Exception(f"Invalid logical file type name:{logical_file_class_name}")

    @property
    def has_logical_spatial_coverage(self):
        """Checks if any of the logical files has spatial coverage"""

        return any(lf.metadata.spatial_coverage is not None for lf in self.logical_files)

    @property
    def has_logical_temporal_coverage(self):
        """Checks if any of the logical files has temporal coverage"""

        return any(lf.metadata.temporal_coverage is not None for lf in self.logical_files)

    @property
    def can_be_submitted_for_metadata_review(self):
        # resource level metadata check
        if not super(CompositeResource, self).can_be_submitted_for_metadata_review:
            return False

        # logical file level metadata check
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False
            # url file cannot be published
            if 'url' in lf.extra_data:
                return False

        return True

    def remove_aggregation_from_file(self, moved_res_file, src_folder, tgt_folder, aggregations=None, cleanup=True):
        """removes association with aggregation (fileset or model program) from a resource file that has been moved
        :param  moved_res_file: an instance of a ResourceFile which has been moved to a different folder
        :param  src_folder: folder from which the file got moved from
        :param  tgt_folder: folder to which the file got moved into
        :param aggregations:   list of all aggregations in self (this resource)
        :param cleanup: if True, cleanup aggregation if aggregation is empty after the file removal
        """

        if moved_res_file.file_folder:
            aggregation = self.get_folder_aggregation_in_path(moved_res_file.file_folder, aggregations=aggregations)
            if aggregation is None:
                return

            # aggregation must be one of 'fileset', 'model instance' or 'model program'
            if aggregation == moved_res_file.logical_file:
                # remove aggregation association with the file
                # the removed aggregation is a fileset aggregation or a model program or a model instance
                # aggregation based on folder (note: model program/instance aggregation can also be
                # created from a single file)
                moved_res_file.logical_file_content_object = None
                moved_res_file.save()
                # delete any instance of ModelProgramResourceFileType associated with this moved file
                if aggregation.is_model_program:
                    # if the file is getting moved within a model program folder hierarchy then no need
                    # to delete any associated ModelProgramResourceFileType object
                    if not tgt_folder.startswith(src_folder) and not src_folder.startswith(tgt_folder):
                        ModelProgramResourceFileType.objects.filter(res_file=moved_res_file).delete()
                if cleanup:
                    self.cleanup_aggregations()

    def add_file_to_aggregation(self, moved_res_file, aggregations=None):
        """adds the moved file to the aggregation (fileset or model program/instance) into which the file has been moved
        :param  moved_res_file: an instance of ResourceFile which has been moved into a folder that represents
        a fileset, a model program, or a model instance aggregation
        :param aggregations:   list of all aggregations in self (this resource)
        """
        if moved_res_file.file_folder and not moved_res_file.has_logical_file:
            # first check for model program/instance aggregation
            aggregation = self.get_model_aggregation_in_path(moved_res_file.file_folder, aggregations=aggregations)
            if aggregation is None:
                # then check for fileset aggregation
                aggregation = self.get_fileset_aggregation_in_path(moved_res_file.file_folder,
                                                                   aggregations=aggregations)
            if aggregation is not None:
                # make the moved file part of the fileset or model program aggregation unless the file is
                # already part of another aggregation (single file aggregation)
                aggregation.add_resource_file(moved_res_file)

    def get_folder_aggregation_object(self, dir_path, aggregations=None):
        """Returns an aggregation (file type) object if the specified folder *dir_path* represents a
         file type aggregation (logical file), otherwise None.

         :param dir_path: Resource file directory path (full folder path starting with resource id)
         for which the aggregation object to be retrieved
         :param aggregations:   list of all aggregations in self (this resource)
        """

        aggregation_path = self.get_relative_path(dir_path)
        logical_files = self._cache_aggregations(aggregations=aggregations)
        for lf in logical_files:
            if hasattr(lf, 'folder'):
                if lf.folder == aggregation_path:
                    return lf
        return None

    def get_folder_aggregation_in_path(self, dir_path, aggregations=None):
        """Gets any aggregation that is based on folder and exists in the specified path
        Searches for a folder based aggregation moving towards the root of the specified path
        :param  dir_path: directory path in which to search for a folder based aggregation
        :param aggregations: a list of all aggregations in self (this resource)
        :return a folder based aggregation if found otherwise, None
        """

        dir_path = self.get_relative_path(dir_path)
        aggregations = self._cache_aggregations(aggregations=aggregations)
        if not aggregations:
            # no aggregations exist in this resource
            return None

        def get_aggregation(path):
            try:
                aggregation = self.get_aggregation_by_name(path, aggregations=aggregations)
                return aggregation
            except ObjectDoesNotExist:
                return None

        while '/' in dir_path:
            aggr = get_aggregation(dir_path)
            if aggr is not None:
                return aggr
            dir_path = os.path.dirname(dir_path)
        else:
            return get_aggregation(dir_path)

    def get_file_aggregation_object(self, file_path):
        """Returns an aggregation (file type) object if the specified file *file_path* represents a
         file type aggregation (logical file), otherwise None.

         :param file_path: Resource file path (full file path starting with resource id)
         for which the aggregation object to be retrieved
        """
        relative_file_path = self.get_relative_path(file_path)
        folder, base = os.path.split(relative_file_path)
        try:
            res_file = ResourceFile.get(self, file=base, folder=folder)
            if res_file.has_logical_file:
                return res_file.logical_file
            return None
        except ObjectDoesNotExist:
            return None

    @property
    def supports_folders(self):
        """ allow folders for CompositeResources """
        return True

    @property
    def supports_logical_file(self):
        """ if this resource allows associating resource file objects with logical file"""
        return True

    def create_aggregation_meta_files(self, path=''):
        """Creates aggregation meta files (resource map, metadata xml files and schema json files) for each of the
        contained aggregations
        :param  path: (optional) file or folder path for which meta files need to be created for
        all associated aggregations of that path
        """

        if not path:
            # create xml docs far all aggregation of this resource
            for aggregation in self.logical_files:
                if aggregation.metadata.is_dirty:
                    aggregation.create_aggregation_xml_documents()
        else:
            # first check if the path is a folder path or file path
            is_path_a_folder = self.is_path_folder(path=path)
            if is_path_a_folder:
                # need to create xml files for all aggregations that exist under path
                path = self.get_relative_path(path)
                for lf in self.logical_files:
                    if lf.aggregation_name.startswith(path) and lf.metadata.is_dirty:
                        lf.create_aggregation_xml_documents()
            else:
                # path is a file path
                try:
                    aggregation = self.get_aggregation_by_name(path)
                    # need to create xml docs only for this aggregation
                    if aggregation.metadata.is_dirty:
                        aggregation.create_aggregation_xml_documents()
                except ObjectDoesNotExist:
                    # file path is not an aggregation - nothing to do
                    pass

    def get_aggregation_by_aggregation_name(self, aggregation_name):
        """Get an aggregation that matches the aggregation dataset_name specified by *dataset_name*
        :param  aggregation_name: aggregation_name (aggregation path) of the aggregation to find
        :return an aggregation object if found
        :raises ObjectDoesNotExist if no matching aggregation is found
        """
        for aggregation in self.logical_files:
            if aggregation.aggregation_name == aggregation_name:
                return aggregation

        raise ObjectDoesNotExist("No matching aggregation was found for "
                                 "name:{}".format(aggregation_name))

    def get_aggregation_by_name(self, name, aggregations=None):
        """Get an aggregation that matches the aggregation name specified by *name*
        :param  name: name (aggregation path) of the aggregation to find
        :param  aggregations:   a list of aggregations in the resource (self)
        :return an aggregation object if found
        :raises ObjectDoesNotExist if no matching aggregation is found
        """
        # check if aggregation path *name* is a file path or a folder
        is_aggr_path_a_folder = self.is_path_folder(path=name)
        if is_aggr_path_a_folder:
            folder_full_path = os.path.join(self.file_path, name)
            aggregation = self.get_folder_aggregation_object(folder_full_path, aggregations=aggregations)
            if aggregation is None:
                raise ObjectDoesNotExist(
                    "No matching aggregation was found for name:{}".format(name))
            return aggregation
        else:
            folder, base = os.path.split(name)
            res_file = ResourceFile.get(self, file=base, folder=folder)
            if res_file.has_logical_file:
                return res_file.logical_file

            raise ObjectDoesNotExist(
                "No matching aggregation was found for name:{}".format(name))

    def get_aggregation_by_meta_file(self, meta_file_path: str) -> AggregationType:
        """Get an aggregation that matches the specified meta xml/json file path
        :param  meta_file_path: directory path of the meta xml/json file
        :return an aggregation object if found
        :raises ObjectDoesNotExist if no matching aggregation is found
        """
        if __debug__:
            assert any(meta_file_path.endswith(ext) for ext in AggregationMetaFilePath)

        meta_file_path = self.get_relative_path(meta_file_path)
        folder, base = os.path.split(meta_file_path)
        if base.endswith(AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value):
            base_file_name_to_match = base[:-len(AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value)]
        elif base.endswith(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value):
            base_file_name_to_match = base[:-len(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value)]
        else:
            base_file_name_to_match = base[:-len(AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH)]

        for res_file in ResourceFile.list_folder(self, folder=folder, sub_folders=False):
            if res_file.has_logical_file:
                file_name_to_match = f"{base_file_name_to_match}{res_file.extension}"
                if res_file.file_name == file_name_to_match:
                    return res_file.logical_file
        # check for folder aggregation
        if folder and folder == base_file_name_to_match:
            folder_aggregation = self.get_folder_aggregation_object(folder)
            if folder_aggregation is not None:
                return folder_aggregation

        raise ObjectDoesNotExist("No matching aggregation was found for "
                                 "meta file path:{}".format(meta_file_path))

    def get_fileset_aggregation_in_path(self, path, aggregations=None):
        """Get the first fileset aggregation in the path moving up (towards the root)in the path
        :param  path: directory path in which to search for a fileset aggregation
        :param  aggregations: a list of aggregations in the resource (self)
        :return a fileset aggregation object if found, otherwise None
        """

        path = self.get_relative_path(path)
        aggregations = self._cache_aggregations(aggregations=aggregations)
        if not aggregations:
            # no aggregations exist in this resource
            return None

        def get_fileset(_path):
            try:
                aggregation = self.get_aggregation_by_name(_path, aggregations=aggregations)
                if aggregation.is_fileset:
                    return aggregation
            except ObjectDoesNotExist:
                return None

        while '/' in path:
            fileset = get_fileset(path)
            if fileset is not None:
                return fileset
            path = os.path.dirname(path)
        else:
            return get_fileset(path)

    def get_model_aggregation_in_path(self, path, aggregations=None):
        """Get the model program or model instance aggregation in the path moving up (towards the root)in the path
        :param  path: directory path in which to search for a model program or model instance aggregation
        :param  aggregations: a list of aggregations in the resource (self)
        :return a model program or model instance aggregation object if found, otherwise None
        """

        path = self.get_relative_path(path)
        aggregations = self._cache_aggregations(aggregations=aggregations)
        if not aggregations:
            # no aggregations exist in this resource
            return None

        def get_aggregation(_path):
            try:
                aggregation = self.get_aggregation_by_name(_path, aggregations=aggregations)
                return aggregation
            except ObjectDoesNotExist:
                return None

        while '/' in path:
            aggr = get_aggregation(path)
            if aggr is not None and (aggr.is_model_program or aggr.is_model_instance):
                return aggr
            path = os.path.dirname(path)
        else:
            aggr = get_aggregation(path)
            if aggr is not None and (aggr.is_model_program or aggr.is_model_instance):
                return aggr
            return None

    def set_flag_to_recreate_aggregation_meta_files(self, orig_path, new_path):
        """
        When a folder or file representing an aggregation is renamed or moved,
        the associated meta files (resource map, metadata xml files as well as schema json files) are deleted
        and then aggregation metadata is set to dirty so that these meta files will be regenerated as part of
        aggregation or bag download
        :param  orig_path: original file/folder path prior to move/rename
        :param  new_path: new file/folder path after move/rename
        """
        aggregations = list(self.logical_files)

        def set_parent_aggregation_dirty(path_to_search):
            if '/' in path_to_search:
                path = os.path.dirname(path_to_search)
                try:
                    parent_aggr = self.get_aggregation_by_name(path, aggregations=aggregations)
                    parent_aggr.set_metadata_dirty()
                except ObjectDoesNotExist:
                    pass

        new_path = self.get_relative_path(new_path)
        orig_path = self.get_relative_path(orig_path)
        is_new_path_a_folder = self.is_path_folder(path=new_path)
        istorage = self.get_s3_storage()

        # remove file extension from aggregation name (note: aggregation name is a file path
        # for all aggregation types except fileset/model aggregation
        file_name, _ = os.path.splitext(orig_path)
        schema_json_file_name = file_name + AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH.value
        meta_xml_file_name = file_name + AggregationMetaFilePath.METADATA_FILE_ENDSWITH.value
        map_xml_file_name = file_name + AggregationMetaFilePath.RESMAP_FILE_ENDSWITH.value
        if not is_new_path_a_folder:
            # case of file rename/move for single file aggregation
            schema_json_file_full_path = os.path.join(self.file_path, schema_json_file_name)
            meta_xml_file_full_path = os.path.join(self.file_path, meta_xml_file_name)
            map_xml_file_full_path = os.path.join(self.file_path, map_xml_file_name)
            # for single file aggregations, compute the metadata JSON file path using original path
            metadata_json_file_full_path = os.path.join(
                self.file_path, orig_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
            )
        else:
            # case of folder rename - fileset/model aggregation
            _, schema_json_file_name = os.path.split(schema_json_file_name)
            _, meta_xml_file_name = os.path.split(meta_xml_file_name)
            _, map_xml_file_name = os.path.split(map_xml_file_name)
            schema_json_file_full_path = os.path.join(self.file_path, new_path, schema_json_file_name)
            meta_xml_file_full_path = os.path.join(self.file_path, new_path, meta_xml_file_name)
            map_xml_file_full_path = os.path.join(self.file_path, new_path, map_xml_file_name)
            # No need to delete metadata JSON files for folder rename cases as metadata JSON filename
            # is not affected by folder rename
            metadata_json_file_full_path = None

        if istorage.exists(schema_json_file_full_path):
            istorage.delete(schema_json_file_full_path)

        if istorage.exists(meta_xml_file_full_path):
            istorage.delete(meta_xml_file_full_path)

        if istorage.exists(map_xml_file_full_path):
            istorage.delete(map_xml_file_full_path)
        
        # delete metadata JSON file only for single file aggregations
        if (
            not is_new_path_a_folder
            and metadata_json_file_full_path is not None
            and istorage.exists(metadata_json_file_full_path)
        ):
            istorage.delete(metadata_json_file_full_path)

        # set affected logical file metadata to dirty so that xml meta files will be regenerated at the time of
        # aggregation or bag download
        for lf in aggregations:
            # set metadata dirty for any folder based aggregations under the orig_path
            if hasattr(lf, 'folder'):
                if lf.folder is not None and lf.folder.startswith(orig_path):
                    lf.folder = os.path.join(new_path, lf.folder[len(orig_path) + 1:]).strip('/')
                    lf.save(update_fields=["folder"])
                    lf.set_metadata_dirty()
                    continue

            # set metadata dirty for any non-folder based aggregation under the orig_path
            if lf.aggregation_name.startswith(orig_path):
                lf.set_metadata_dirty()

            # set metadata to dirty for non-folder based aggregation under the new_path
            if lf.aggregation_name.startswith(new_path):
                lf.set_metadata_dirty()

        # set metadata to dirty for any parent aggregation that may exist relative to path *orig_path*
        set_parent_aggregation_dirty(orig_path)

        # set metadata to dirty for any parent aggregation that may exist relative to path *new_path*
        set_parent_aggregation_dirty(new_path)

        try:
            aggregation = self.get_aggregation_by_name(new_path, aggregations=aggregations)
            aggregation.set_metadata_dirty()
        except ObjectDoesNotExist:
            # the file path *new_path* does not represent an aggregation - no more
            # action is needed
            pass

    def is_aggregation_xml_file(self, file_path):
        """ determine whether a given file in the file hierarchy is metadata.

        This is true if it is listed as metadata in any logical file.
        """
        if not self.is_metadata_xml_file(file_path):
            return False
        for logical_file in self.logical_files:
            if logical_file.metadata_file_path == file_path or \
                    logical_file.map_file_path == file_path:
                return True
        return False

    def supports_rename_path(self, src_full_path, tgt_full_path):
        """checks if file/folder rename/move is allowed
        :param  src_full_path: name of the file/folder storage path to be renamed (path starts with resource id)
        :param  tgt_full_path: new name for file/folder storage path (path starts with resource id)
        :return True or False
        """

        if __debug__:
            assert src_full_path.startswith(self.file_path)
            assert tgt_full_path.startswith(self.file_path)

        # need to find out which of the following actions the user is trying to do:
        # renaming a file
        # renaming a folder
        # moving a file
        # moving a folder
        is_renaming_file = False
        is_moving_file = False
        is_moving_folder = False

        if tgt_full_path == self.file_path:
            # at the root of the resource all file operations are allowed
            return True

        istorage = self.get_s3_storage()
        scr_base_name = os.path.basename(src_full_path)
        src_dir_path = os.path.dirname(src_full_path)
        tgt_dir_path = os.path.dirname(tgt_full_path)

        if istorage.isFile(src_full_path):
            if istorage.exists(tgt_full_path) or tgt_full_path.endswith(scr_base_name):
                is_moving_file = True
                if tgt_full_path.endswith(scr_base_name):
                    tgt_dir_path = os.path.dirname(tgt_full_path)
                else:
                    tgt_dir_path = tgt_full_path
            else:
                is_renaming_file = True
        else:
            # src path is a directory
            if src_dir_path == tgt_dir_path:
                # renaming folder - no restriction
                return True
            else:
                is_moving_folder = True

        def check_src_aggregation(src_aggr):
            """checks if the aggregation at the source allows file rename/move action"""
            if src_aggr is not None:
                if is_renaming_file:
                    return src_aggr.supports_resource_file_rename
                elif is_moving_file:
                    return src_aggr.supports_resource_file_move
            return True

        if is_renaming_file or is_moving_file:
            # see if the folder containing the file represents an aggregation
            src_aggr = self.get_file_aggregation_object(file_path=src_full_path)
            if check_src_aggregation(src_aggr):
                # check target
                if is_moving_file:
                    tgt_aggr = self.get_folder_aggregation_in_path(dir_path=tgt_dir_path)
                    if tgt_aggr is not None:
                        if src_aggr is None:
                            return tgt_aggr.supports_resource_file_move
                        else:
                            return tgt_aggr.can_contain_aggregation(src_aggr)
                    return True
                return True
            return False

        if is_moving_folder:
            src_aggr = self.get_folder_aggregation_in_path(dir_path=src_full_path)
            if src_aggr is not None:
                if src_aggr.supports_resource_file_move:
                    tgt_aggr = self.get_folder_aggregation_in_path(dir_path=tgt_full_path)
                    if tgt_aggr is not None:
                        return tgt_aggr.supports_resource_file_move and tgt_aggr.can_contain_aggregation(src_aggr)
                    return True
            tgt_aggr = self.get_folder_aggregation_in_path(dir_path=tgt_full_path)
            if tgt_aggr is not None:
                return tgt_aggr.supports_resource_file_move
            return True

    def can_add_files(self, target_full_path):
        """
        checks if file(s) can be uploaded to the specified *target_full_path*
        :param target_full_path: full folder path name where file needs to be uploaded to
        :return: True or False
        """
        path_to_check = target_full_path

        if not path_to_check.endswith("data/contents"):
            # it is not the base directory - it must be a directory under base dir
            aggregation_path = self.get_relative_path(path_to_check)
            try:
                aggregation = self.get_aggregation_by_name(aggregation_path)
                return aggregation.supports_resource_file_add
            except ObjectDoesNotExist:
                # target path doesn't represent an aggregation - so it is OK to add a file
                pass
        return True

    def supports_zip(self, folder_to_zip):
        """check if the given folder can be zipped or not"""

        # find all the resource files in the folder to be zipped
        # this is being passed both qualified and unqualified paths!

        full_path = folder_to_zip
        if not full_path.startswith(self.file_path):
            full_path = os.path.join(self.file_path, full_path)
        # get all resource files at full_path and its sub-folders
        res_file_objects = ResourceFile.list_folder(self, full_path)

        # check any logical file associated with the resource file supports zip functionality
        for res_file in res_file_objects:
            if res_file.has_logical_file:
                if not res_file.logical_file.supports_zip:
                    return False
        return True

    def supports_delete_folder_on_zip(self, original_folder):
        """check if the specified folder can be deleted at the end of zipping that folder"""

        # find all the resource files in the folder to be deleted
        # this is being passed both qualified and unqualified paths!
        full_path = original_folder
        if not full_path.startswith(self.file_path):
            full_path = os.path.join(self.file_path, full_path)

        # get all resource files at full_path and its sub-folders
        res_file_objects = ResourceFile.list_folder(self, full_path)

        # check any logical file associated with the resource file supports deleting the folder
        # after its zipped
        for res_file in res_file_objects:
            if res_file.has_logical_file:
                if not res_file.logical_file.supports_delete_folder_on_zip:
                    return False
        return True

    def get_missing_file_type_metadata_info(self):
        # this is used in page pre-processor to build the context
        # so that the landing page can show what metadata items are missing for each
        # logical file/aggregation
        metadata_missing_info = []
        for lfo in self.logical_files:
            if not lfo.metadata.has_all_required_elements():
                missing_elements = lfo.metadata.get_required_missing_elements()
                metadata_missing_info.append({'file_path': lfo.aggregation_name,
                                              'missing_elements': missing_elements})
        return metadata_missing_info

    def get_data_services_urls(self):
        """
        Generates data services URLs for the resource.
        If the resource contains any GeoFeature or GeoRaster content, and if it's public,
        generate data service endpoints.
        If the resource contains any multidimensional content and it's public,
        generate THREDDS catalog service endpoint as well.
        """
        wfs_url = None
        wms_url = None
        wcs_url = None
        thredds_url = None
        if self.raccess.public:
            try:
                resource_data_types = [lf.data_type for lf in self.logical_files]
                service_url = (
                    f'{settings.HSWS_GEOSERVER_URL}/HS-{self.short_id}/'
                    + '{}?request=GetCapabilities'
                )
                if 'GeographicFeature' in resource_data_types:
                    wfs_url = service_url.format('wfs')
                    wms_url = service_url.format('wms')
                if 'GeographicRaster' in resource_data_types:
                    wcs_url = service_url.format('wcs')
                    wms_url = service_url.format('wms')
            except Exception as e:
                logger.exception("get_data_services_urls: " + str(e))

            if 'Multidimensional' in resource_data_types:
                thredds_url = (
                    f'{settings.THREDDS_SERVER_URL}catalog/hydroshare/resources/{self.short_id}/data/contents/'
                    f'catalog.html'
                )
        data_services_urls = {
            'wms_url': wms_url,
            'wfs_url': wfs_url,
            'wcs_url': wcs_url,
            'thredds_url': thredds_url
        }

        return data_services_urls

    def delete_coverage(self, coverage_type):
        """Deletes coverage data for the resource
        :param coverage_type: A value of either 'spatial' or 'temporal
        :return:
        """
        if coverage_type.lower() == 'spatial' and self.metadata.spatial_coverage:
            self.metadata.spatial_coverage.delete()
            self.metadata.is_dirty = True
            self.metadata.save()
        elif coverage_type.lower() == 'temporal' and self.metadata.temporal_coverage:
            self.metadata.temporal_coverage.delete()
            self.metadata.is_dirty = True
            self.metadata.save()

    def update_coverage(self):
        """Update resource spatial and temporal coverage based on the corresponding coverages
        from all the contained aggregations (logical file) only if the resource coverage is not
        already set"""

        # update resource spatial coverage only if there is no spatial coverage already
        if self.metadata.spatial_coverage is None:
            self.update_spatial_coverage()

        # update resource temporal coverage only if there is no temporal coverage already
        if self.metadata.temporal_coverage is None:
            self.update_temporal_coverage()

    def update_spatial_coverage(self):
        """Updates resource spatial coverage based on the contained spatial coverages of
        aggregations (file type). Note: This action will overwrite any existing resource spatial
        coverage data.
        """

        update_target_spatial_coverage(self)

    def update_temporal_coverage(self):
        """Updates resource temporal coverage based on the contained temporal coverages of
        aggregations (file type). Note: This action will overwrite any existing resource temporal
        coverage data.
        """

        update_target_temporal_coverage(self)

    def cleanup_aggregations(self):
        """Deletes any dangling aggregations (aggregation without resource files or folder) the resource may have"""

        count = 0
        for lf in self.logical_files:
            if lf.is_dangling:
                agg_cls_name = lf.type_name()
                lf.remove_aggregation()
                count += 1
                msg = "Deleted a dangling aggregation of type:{} for resource:{}".format(agg_cls_name, self.short_id)
                logger.warning(msg)
        return count

    def dangling_aggregations_exist(self):
        """Checks if there are any dangling aggregations in this resource
        Note: This function used only in tests
        """

        for lf in self.logical_files:
            if lf.is_dangling:
                return True
        return False

    def is_path_folder(self, path):
        istorage = self.get_s3_storage()
        if not path.startswith(self.file_path):
            path = os.path.join(self.file_path, path)
        return istorage.isDir(path)

    def _cache_aggregations(self, aggregations):
        """A helper function to cache aggregations to avoid repeated database queries"""
        if aggregations is None:
            aggregations = list(self.logical_files)

        return aggregations


# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
