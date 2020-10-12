import os

from django.core.exceptions import ObjectDoesNotExist
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, ResourceFile, resource_processor
from hs_file_types.models import ModelProgramResourceFileType
from hs_file_types.models.base import RESMAP_FILE_ENDSWITH, METADATA_FILE_ENDSWITH
from hs_file_types.utils import update_target_temporal_coverage, update_target_spatial_coverage


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

    discovery_content_type = 'Composite'  # used during discovery

    class Meta:
        verbose_name = 'Composite Resource'
        proxy = True

    @property
    def can_be_public_or_discoverable(self):
        # resource level metadata check
        if not super(CompositeResource, self).can_be_public_or_discoverable:
            return False

        # filetype level metadata check
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False

        return True

    @property
    def logical_files(self):
        """A generator that returns each of the logical files of this resource"""
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

    @property
    def can_be_published(self):
        # resource level metadata check
        if not super(CompositeResource, self).can_be_published:
            return False

        # filetype level metadata check
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False
            # url file cannot be published
            if 'url' in lf.extra_data:
                return False
            # check for model instance linked to model program
            if lf.is_model_instance:
                mi_aggr = lf
                mp_aggr = mi_aggr.metadata.executed_by
                if mp_aggr is not None:
                    if mp_aggr.resource.short_id != mi_aggr.resource.short_id:
                        # model instance aggregation and model program aggregations are not in the same resource
                        # the other resource containing the linked model program must have been published
                        # before this resource can be published
                        if not mp_aggr.resource.raccess.published:
                            return False
                    else:
                        # model program aggregation and the linked model instance aggregations are in the same resource
                        continue
                model_program_url = mi_aggr.metadata.executed_by_url
                if model_program_url:
                    # external linked model program url must be a DOI url for this resource to be published
                    if not model_program_url.startswith("https://doi.org") and \
                            not model_program_url.startswith("http://doi.org"):
                        return False

        return True

    def remove_aggregation_from_file(self, moved_res_file, src_folder, tgt_folder):
        """removes association with aggregation (fileset or model program) from this
        moved resource file
        :param  moved_res_file: an instance of a ResourceFile which has been moved to a different folder
        :param  src_folder: folder from which the file got moved from
        :param  tgt_folder: folder to which the file got moved into
        """
        if moved_res_file.has_logical_file and (moved_res_file.logical_file.is_fileset or
                                                moved_res_file.logical_file.is_model_program or
                                                moved_res_file.logical_file.is_model_instance):
            if moved_res_file.file_folder:
                try:
                    aggregation = self.get_aggregation_by_name(moved_res_file.file_folder)
                    if aggregation == moved_res_file.logical_file:
                        if aggregation.is_fileset or ((aggregation.is_model_program or
                                                       aggregation.is_model_instance) and
                                                      aggregation.folder is not None):
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
                except ObjectDoesNotExist:
                    pass

    def add_file_to_aggregation(self, moved_res_file):
        """adds the moved file to the aggregation (fileset or model program/instance) into which the file has been moved
        :param  moved_res_file: an instance of ResourceFile which has been moved into a folder that represents
        a fileset or a model program or a model instance aggregation
        """
        if moved_res_file.file_folder and not moved_res_file.has_logical_file:
            # first check for model program/instance aggregation
            aggregation = self.get_model_aggregation_in_path(moved_res_file.file_folder)
            if aggregation is None:
                # then check for fileset aggregation
                aggregation = self.get_fileset_aggregation_in_path(moved_res_file.file_folder)
            if aggregation is not None:
                # make the moved file part of the fileset or model program aggregation unless the file is
                # already part of another aggregation (single file aggregation)
                aggregation.add_resource_file(moved_res_file)

    def get_folder_aggregation_object(self, dir_path):
        """Returns an aggregation (file type) object if the specified folder *dir_path* represents a
         file type aggregation (logical file), otherwise None.

         :param dir_path: Resource file directory path (full folder path starting with resource id)
         for which the aggregation object to be retrieved
        """

        aggregation_path = dir_path[len(self.file_path) + 1:]
        # first check for model program/instance aggregation
        mp_mi_aggr = self.modelprogramlogicalfile_set.filter(folder=aggregation_path).first()
        if mp_mi_aggr is None:
            mp_mi_aggr = self.modelinstancelogicalfile_set.filter(folder=aggregation_path).first()

        if mp_mi_aggr is None:
            # no model program or model instance aggr - check for fileset aggr
            return self.filesetlogicalfile_set.filter(folder=aggregation_path).first()
        return mp_mi_aggr

    def get_file_aggregation_object(self, file_path):
        """Returns an aggregation (file type) object if the specified file *file_path* represents a
         file type aggregation (logical file), otherwise None.

         :param file_path: Resource file path (full file path starting with resource id)
         for which the aggregation object to be retrieved
        """
        relative_file_path = file_path[len(self.file_path) + 1:]
        folder, base = os.path.split(relative_file_path)
        try:
            res_file = ResourceFile.get(self, file=base, folder=folder)
            if res_file.has_logical_file:
                return res_file.logical_file
            return None
        except ObjectDoesNotExist:
            return None

    def can_set_folder_to_fileset(self, dir_path):
        """Checks if the specified folder *dir_path* can be set to Fileset aggregation

        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which the FileSet aggregation to be set

        :return
        If the specified folder is already represents an aggregation, return False
        if the specified folder does not contain any files, return False
        if any of the parent folders is a model program aggregation, return False
        if any of the parent folders is a model instance aggregation, return False
        otherwise, return True

        Note: A fileset aggregation is not allowed inside a model program or model instance aggregation. One
        fileset aggregation can contain any other aggregation types including fileset aggregation
        """

        if self.get_folder_aggregation_object(dir_path) is not None:
            # target folder is already an aggregation
            return False

        # checking all parent folders
        path = os.path.dirname(dir_path)
        while '/' in path:
            parent_aggr = self.get_folder_aggregation_object(path)
            if parent_aggr is not None and (parent_aggr.is_model_program or parent_aggr.is_model_instance):
                # avoid creating a fileset aggregation inside a model program/instance aggregation folder
                return False
            # go to next parent folder
            path = os.path.dirname(path)

        irods_path = dir_path
        if self.is_federated:
            irods_path = os.path.join(self.resource_federation_path, irods_path)

        files_in_path = ResourceFile.list_folder(self, folder=irods_path, sub_folders=True)
        # if there are any files in the dir_path, we can set the folder to fileset aggregation
        return len(files_in_path) > 0

    def can_set_folder_to_model_instance_aggregation(self, dir_path):
        """Checks if the specified folder *dir_path* can be set to ModelInstance aggregation

        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which the ModelInstance aggregation to be set

        :return
        If the specified folder is already represents an aggregation, return Flase
        if the specified folder path does not contain any files, return False
        if any of the files in the specified folder path is part of an aggregation other than fileset, return False
        if any of the sub-folders is a fileset aggregation, returns False
        if any of the parent folders is a model program aggregation, return False
        if any of the parent folders is a model instance aggregation, return False
        otherwise, return True
        """
        return self._can_set_folder_to_mi_or_mp_aggregation(dir_path=dir_path, aggr_type="ModelInstance")

    def can_set_folder_to_model_program_aggregation(self, dir_path):
        """Checks if the specified folder *dir_path* can be set to ModelProgram aggregation

        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which the ModelProgram aggregation to be set

        :return
        If the specified folder is already represents an aggregation, return False
        if the specified folder does not contain any files, return False
        if any of the files in the specified folder path is part of an aggregation other than fileset, return False
        if any of the sub-folders is a fileset aggregation, return False
        if any of the sub-folders is a model program aggregation, return False
        if any of the sub-folders is a model instance aggregation, return False
        if any of the parent folders is a model program aggregation or model instance aggregation, return False
        otherwise, return True
        """
        return self._can_set_folder_to_mi_or_mp_aggregation(dir_path=dir_path, aggr_type="ModelProgram")

    def _can_set_folder_to_mi_or_mp_aggregation(self, dir_path, aggr_type):
        """helper to check if the specified folder *dir_path* can be set to ModelProgram or ModelInstance aggregation

        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which the aggregation of the type *aggr_type* to be set
        :param aggr_type: a value of either ModelProgram or ModelInstance

        :return True or False

        """

        # checking target folder for any aggregation
        if self.get_folder_aggregation_object(dir_path) is not None:
            # target folder is already an aggregation
            return False

        aggregation_path = dir_path[len(self.file_path) + 1:]
        # checking sub-folders for fileset aggregation
        # check that we don't have any sub folder of dir_path representing a fileset aggregation
        # so that we can avoid nesting a fileset aggregation inside a model program or model instance aggregation
        if self.filesetlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        if aggr_type == "ModelProgram":
            # checking sub-folders for model program aggregation
            # check that we don't have any sub folder of dir_path representing a model program aggregation
            # so that we can avoid nesting a model program aggregation inside a model
            # program aggregation
            if self.modelprogramlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
                return False

        # checking sub-folders for model instance aggregation
        # check that we don't have any sub folder of dir_path representing a model instance aggregation
        # so that we can avoid nesting a model instance aggregation inside a model program aggregation
        if self.modelinstancelogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        # check the first parent folder that represents an aggregation
        irods_path = dir_path
        if self.is_federated:
            irods_path = os.path.join(self.resource_federation_path, irods_path)

        # get the parent folder path
        path = os.path.dirname(dir_path)
        parent_aggregation = None
        while '/' in path:
            if path == self.file_path:
                break
            parent_aggregation = self.get_folder_aggregation_object(path)
            if parent_aggregation is not None:
                # this is the first parent folder that represents an aggregation
                break
            # get the next parent folder path
            path = os.path.dirname(path)

        if parent_aggregation is not None:
            if parent_aggregation.is_fileset:
                # check that all resource files under the target folder 'dir_path' are associated with fileset only
                files_in_path = ResourceFile.list_folder(self, folder=irods_path, sub_folders=True)
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
            files_in_path = ResourceFile.list_folder(self, folder=irods_path, sub_folders=True)

            if files_in_path:
                # if none of the resource files in the target path has logical file then we can set the folder
                # to model program or model instance aggregation
                if aggr_type == "ModelProgram":
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

    @property
    def supports_folders(self):
        """ allow folders for CompositeResources """
        return True

    @property
    def supports_logical_file(self):
        """ if this resource allows associating resource file objects with logical file"""
        return True

    def get_metadata_xml(self, pretty_print=True, include_format_elements=True):
        # get resource level core metadata as xml string
        # for composite resource we don't want the format elements at the resource level
        # as they are included at the aggregation map xml document
        xml_string = super(CompositeResource, self).get_metadata_xml(pretty_print=True,
                                                                     include_format_elements=False)
        return xml_string

    def _recreate_nested_aggr_xml_docs(self, folder, nested_aggr):
        """Recreates xml files for all fileset or model instance aggregations that exist under the path 'folder'
        as well as for any parent fileset/model instance that may exist relative to path 'folder'
        """
        if nested_aggr == 'fileset':
            nested_aggr_set = self.filesetlogicalfile_set
            aggr_in_path_func = self.get_fileset_aggregation_in_path
        else:
            # create xml files for all model instance aggregation that may exist under *folder*
            nested_aggr_set = self.modelinstancelogicalfile_set
            aggr_in_path_func = self.get_model_aggregation_in_path

        nested_aggrs = nested_aggr_set.filter(folder__startswith=folder)
        for ns_aggr in nested_aggrs:
            ns_aggr.create_aggregation_xml_documents()

        # Also need to recreate xml doc for any parent fileset/model instance that may exist relative to path
        # *folder*
        if '/' in folder:
            path = os.path.dirname(folder)
            parent_aggr = aggr_in_path_func(path)
            if parent_aggr is not None:
                parent_aggr.create_aggregation_xml_documents()

    def create_model_aggr_meta_json_schema_files(self, path=''):
        """ Creates metadata json schema file for any model aggregations in the resource that has
        metadata schema
        :param  path: (optional) file or folder path for which metadata schema files need to be created for
        all associated model aggregations of that path
        """

        if not path:
            # create metadata schema json file far all model aggregations of this resource
            for aggregation in self.modelprogramlogicalfile_set.exclude(metadata_schema_json={}):
                aggregation.create_metadata_schema_json_file()
            for aggregation in self.modelinstancelogicalfile_set.exclude(metadata_schema_json={}):
                aggregation.create_metadata_schema_json_file()

        else:
            # first check if the path is a folder path or file path
            _, ext = os.path.splitext(path)
            is_path_a_folder = ext == ''
            try:
                if is_path_a_folder:
                    # need to create json files for all model aggregations that exist under path
                    if path.startswith(self.file_path):
                        folder = path[len(self.file_path) + 1:]
                    else:
                        folder = path
                    mp_aggrs = self.modelprogramlogicalfile_set.filter(folder__startswith=folder).exclude(
                        metadata_schema_json={})
                    for mp_aggr in mp_aggrs:
                        mp_aggr.create_metadata_schema_json_file()

                    mi_aggrs = self.modelinstancelogicalfile_set.filter(folder__startswith=folder).exclude(
                        metadata_schema_json={})
                    for mi_aggr in mi_aggrs:
                        mi_aggr.create_metadata_schema_json_file()
                else:
                    # path is a file path
                    aggregation = self.get_aggregation_by_name(path)
                    # need to create json file only for this model aggregation
                    if aggregation.is_model_program or aggregation.is_model_instance:
                        aggregation.create_metadata_schema_json_file()
            except ObjectDoesNotExist:
                # path representing a file path is not an aggregation - nothing to do
                pass

    def create_aggregation_xml_documents(self, path=''):
        """Creates aggregation map and metadata xml files for each of the contained aggregations

        :param  path: (optional) file or folder path for which xml documents need to be created for
        all associated aggregations of that path
        """

        if not path:
            # create xml docs far all aggregation of this resource
            for aggregation in self.logical_files:
                if aggregation.metadata.is_dirty:
                    aggregation.create_aggregation_xml_documents()
        else:
            # first check if the path is a folder path or file path
            _, ext = os.path.splitext(path)
            is_path_a_folder = ext == ''
            try:
                if is_path_a_folder:
                    # need to create all aggregations that exist under path
                    self._create_xml_docs_for_folder(folder=path)
                else:
                    # path is a file path
                    aggregation = self.get_aggregation_by_name(path)
                    # need to create xml docs only for this aggregation
                    if aggregation.metadata.is_dirty:
                        aggregation.create_aggregation_xml_documents()
            except ObjectDoesNotExist:
                # path representing a file path is not an aggregation - nothing to do
                pass

    def _recreate_xml_docs_for_folder(self, new_folder, old_folder):
        """Re-creates xml metadata and map documents for all aggregations that exists under
        the specified folder *new_folder

        :param  new_folder: folder path for which xml documents need to be re-created for all
        aggregations that exist under this folder path
        :param  old_folder: folder path prior to folder path changed to as
        per 'new_folder'
        """

        def update_fileset_folder():
            """Updates the folder attribute of all filesets that exist under 'old_folder' when
            the folder is renamed to *new_folder*"""

            filesets = self.filesetlogicalfile_set.filter(folder__startswith=old_folder)
            for fs in filesets:
                fs.folder = new_folder + fs.folder[len(old_folder):]
                fs.save()

        def update_model_program_folder():
            """Updates the folder attribute of all folder based model program aggregation that exist under
            'old_folder' when the folder is renamed to *new_folder*"""

            mp_aggregations = self.modelprogramlogicalfile_set.filter(folder__startswith=old_folder)
            for mp_aggr in mp_aggregations:
                if mp_aggr.folder is not None:
                    mp_aggr.folder = new_folder + mp_aggr.folder[len(old_folder):]
                    mp_aggr.save()
                    # any associated model instance aggregation metadata needs to be set dirty
                    # in order to regenerate metadata xml files for these linked model instance aggregations
                    for mi_metadata in mp_aggr.mi_metadata_objects.all():
                        mi_metadata.is_dirty = True
                        mi_metadata.save()

        def update_model_instance_folder():
            """Updates the folder attribute of all folder based model instance aggregation that exist under
            'old_folder' when the folder is renamed to *new_folder*"""

            mi_aggregations = self.modelinstancelogicalfile_set.filter(folder__startswith=old_folder)
            for mi_aggr in mi_aggregations:
                if mi_aggr.folder is not None:
                    mi_aggr.folder = new_folder + mi_aggr.folder[len(old_folder):]
                    mi_aggr.save()

        # recreate xml files for all fileset aggregations that exist under new_folder
        if new_folder.startswith(self.file_path):
            new_folder = new_folder[len(self.file_path) + 1:]

        if old_folder.startswith(self.file_path):
            old_folder = old_folder[len(self.file_path) + 1:]

        # first update folder attribute of any model program aggregation that exist under *old_folder*
        update_model_program_folder()
        mp_aggregations = self.modelprogramlogicalfile_set.filter(folder__startswith=new_folder)
        for mp_aggr in mp_aggregations:
            mp_aggr.create_aggregation_xml_documents()

        # first update folder attribute of any model instance aggregation that exist under *old_folder*
        update_model_instance_folder()
        self._recreate_nested_aggr_xml_docs(folder=new_folder, nested_aggr='modelinstance')

        # first update folder attribute of all filesets that exist under *old_folder*
        update_fileset_folder()
        self._recreate_nested_aggr_xml_docs(folder=new_folder, nested_aggr='fileset')

        # create xml files for all non fileset aggregations
        if not new_folder.startswith(self.file_path):
            new_folder = os.path.join(self.file_path, new_folder)

        # create xml docs for all non-fileset aggregations
        logical_files = self._get_aggregations_by_folder(new_folder)
        for lf in logical_files:
            lf.create_aggregation_xml_documents()

    def _create_xml_docs_for_folder(self, folder):
        """Creates xml metadata and map documents for any aggregation that is part of the
        the specified folder *folder*. Also xml docs are created for an aggregation only if the
        aggregation metadata is dirty

        :param  folder: folder for which xml documents need to be created for all aggregations that
        exist in folder *folder*
        """

        # create xml map and metadata xml documents for all aggregations that exist
        # in *folder* and its sub-folders
        if not folder.startswith(self.file_path):
            folder = os.path.join(self.file_path, folder)

        # create xml docs for all non fileset aggregations
        # note: we can't get to all filesets from resource files since
        # it is possible to have filesets without any associated resource files
        logical_files = self._get_aggregations_by_folder(folder)
        for lf in logical_files:
            if lf.metadata.is_dirty:
                lf.create_aggregation_xml_documents()

        # create xml docs for all fileset aggregations that exist under folder *folder*
        if folder.startswith(self.file_path):
            folder = folder[len(self.file_path) + 1:]

        filesets = self.filesetlogicalfile_set.filter(folder__startswith=folder)
        for fs in filesets:
            if fs.metadata.is_dirty:
                fs.create_aggregation_xml_documents()

    def _get_aggregations_by_folder(self, folder):
        """Get a list of all non-fileset aggregations associated with resource files that
        exist in the specified file path *folder*
        :param  folder: the folder path for which aggregations need to be searched
        """
        res_file_objects = ResourceFile.list_folder(self, folder)
        logical_files = set(res_file.logical_file for res_file in res_file_objects if
                            res_file.has_logical_file and not res_file.logical_file.is_fileset)
        return logical_files

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

    def get_aggregation_by_name(self, name):
        """Get an aggregation that matches the aggregation name specified by *name*
        :param  name: name (aggregation path) of the aggregation to find
        :return an aggregation object if found
        :raises ObjectDoesNotExist if no matching aggregation is found
        """
        # check if aggregation path *name* is a file path or a folder
        _, ext = os.path.splitext(name)
        is_aggr_path_a_folder = ext == ''
        if is_aggr_path_a_folder:
            folder_full_path = os.path.join(self.file_path, name)
            aggregation = self.get_folder_aggregation_object(folder_full_path)
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

    def get_fileset_aggregation_in_path(self, path):
        """Get the first fileset aggregation in the path moving up (towards the root)in the path
        :param  path: directory path in which to search for a fileset aggregation
        :return a fileset aggregation object if found, otherwise None
        """

        def get_fileset(path):
            try:
                aggregation = self.get_aggregation_by_name(path)
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

    def get_model_aggregation_in_path(self, path):
        """Get the model program or model instance aggregation in the path moving up (towards the root)in the path
        :param  path: directory path in which to search for a model program or model instance aggregation
        :return a model program or model instance aggregation object if found, otherwise None
        """

        def get_aggregation(path):
            try:
                aggregation = self.get_aggregation_by_name(path)
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

    def recreate_aggregation_xml_docs(self, orig_path, new_path):
        """
        When a folder or file representing an aggregation is renamed or moved,
        the associated map and metadata xml documents are deleted
        and then regenerated
        :param  orig_path: original file/folder path prior to move/rename
        :param  new_path: new file/folder path after move/rename
        """

        def delete_old_xml_files(folder=''):
            istorage = self.get_irods_storage()
            # remove file extension from aggregation name (note: aggregation name is a file path
            # for all aggregation types except fileset
            xml_file_name, _ = os.path.splitext(orig_path)
            meta_xml_file_name = xml_file_name + METADATA_FILE_ENDSWITH
            map_xml_file_name = xml_file_name + RESMAP_FILE_ENDSWITH
            if not folder:
                # case of file rename/move for single file aggregation
                meta_xml_file_full_path = os.path.join(self.file_path, meta_xml_file_name)
                map_xml_file_full_path = os.path.join(self.file_path, map_xml_file_name)
            else:
                # case of folder rename - fileset aggregation
                _, meta_xml_file_name = os.path.split(meta_xml_file_name)
                _, map_xml_file_name = os.path.split(map_xml_file_name)
                meta_xml_file_full_path = os.path.join(self.file_path, folder, meta_xml_file_name)
                map_xml_file_full_path = os.path.join(self.file_path, folder, map_xml_file_name)

            if istorage.exists(meta_xml_file_full_path):
                istorage.delete(meta_xml_file_full_path)

            if istorage.exists(map_xml_file_full_path):
                istorage.delete(map_xml_file_full_path)

        # first check if the new_path is a folder path or file path
        name, ext = os.path.splitext(new_path)
        is_new_path_a_folder = ext == ''

        if is_new_path_a_folder:
            delete_old_xml_files(folder=new_path)
            self._recreate_xml_docs_for_folder(new_folder=new_path, old_folder=orig_path)
        else:
            # check if there is a matching aggregation based on file path *new_path*
            try:
                aggregation = self.get_aggregation_by_name(new_path)
                delete_old_xml_files()
                aggregation.create_aggregation_xml_documents()
                # check if the affected aggregation is a model program aggregation
                # then any associated model instance aggregation metadata needs to be set dirty
                # in order to regenerate metadata xml files for these linked model instance aggregations
                if aggregation.type_name() == "ModelProgramLogicalFile":
                    for mi_metadata in aggregation.mi_metadata_objects.all():
                        mi_metadata.is_dirty = True
                        mi_metadata.save()

            except ObjectDoesNotExist:
                # the file path *new_path* does not represent an aggregation - no more
                # action is needed
                pass

    def is_aggregation_xml_file(self, file_path):
        """ determine whether a given file in the file hierarchy is metadata.

        This is true if it is listed as metadata in any logical file.
        """
        if not (file_path.endswith(METADATA_FILE_ENDSWITH) or
                file_path.endswith(RESMAP_FILE_ENDSWITH)):
            return False
        for logical_file in self.logical_files:
            if logical_file.metadata_file_path == file_path or \
                    logical_file.map_file_path == file_path:
                return True
        return False

    def supports_rename_path(self, src_full_path, tgt_full_path):
        """checks if file/folder rename/move is allowed
        :param  src_full_path: name of the file/folder path to be renamed
        :param  tgt_full_path: new name for file/folder path
        :return True or False
        """

        if __debug__:
            assert(src_full_path.startswith(self.file_path))
            assert(tgt_full_path.startswith(self.file_path))

        # need to find out which of the following actions the user is trying to do:
        # renaming a file
        # renaming a folder
        # moving a file
        # moving a folder
        is_renaming_file = False
        is_moving_file = False
        is_moving_folder = False

        istorage = self.get_irods_storage()

        tgt_folder, tgt_file_name = os.path.split(tgt_full_path)
        _, tgt_ext = os.path.splitext(tgt_file_name)
        if tgt_ext:
            tgt_file_dir = os.path.dirname(tgt_full_path)
        else:
            tgt_file_dir = tgt_full_path

        src_folder, src_file_name = os.path.split(src_full_path)
        _, src_ext = os.path.splitext(src_file_name)
        if src_ext:
            src_file_dir = os.path.dirname(src_full_path)
        else:
            src_file_dir = src_full_path

        if src_ext and tgt_ext:
            if src_file_name != tgt_file_name:
                is_renaming_file = True
            else:
                is_moving_file = True
        elif src_ext:
            is_moving_file = True
        elif not istorage.exists(tgt_file_dir):
            src_base_dir = os.path.dirname(src_full_path)
            tgt_base_dir = os.path.dirname(tgt_full_path)
            if src_base_dir == tgt_base_dir:
                # renaming folder - no restriction
                return True
            is_moving_folder = True
        else:
            is_moving_folder = True

        def check_target_folder(src_aggr=None):
            """checks if the target folder allows file/folder being moved into it"""
            tgt_aggr_path = tgt_file_dir[len(self.file_path) + 1:]
            # check if this move would create a nested model program aggregation -
            # nested model program aggregation is NOT allowed
            # model instance aggregation can't contain model program aggregation
            if src_aggr is not None and (src_aggr.is_model_program or src_aggr.is_model_instance):
                # src_aggr is a model based aggregation
                if is_moving_file or is_moving_folder:
                    src_model_aggr = src_aggr
                    #  find if there is any folder based model program/instance aggregation in the target path
                    tgt_model_aggr = self.get_model_aggregation_in_path(tgt_aggr_path)
                    if tgt_model_aggr is not None:
                        # tgt_model_aggr is a folder based aggregation
                        if src_model_aggr.folder is None:
                            # moving a file based model program/model instance aggregation
                            if tgt_model_aggr.is_model_program:
                                # aggregation nesting is not allowed for model program aggregation
                                return False
                            else:
                                # target aggregation folder is a model instance aggregation
                                if src_aggr.is_model_instance or src_aggr.is_model_program:
                                    # not allowed to move a model instance/program to another model instance
                                    return False

                        # moving a folder based model program/instance aggregation
                        # moving folder within the same model program/instance aggregation is allowed
                        return src_model_aggr.id == tgt_model_aggr.id

                    # target folder is either a normal folder or fileset folder - file or folder move is allowed
                    return True
                return True

            # src is not an aggregation OR src is not a model instance/program type aggregation
            if is_moving_file or is_moving_folder:
                tgt_aggregation = self.get_fileset_aggregation_in_path(tgt_aggr_path)
                if tgt_aggregation is None:
                    tgt_aggregation = self.get_model_aggregation_in_path(tgt_aggr_path)
                if src_aggr is not None and tgt_aggregation is not None:
                    if tgt_aggregation.is_model_instance:
                        # model instance can contains any aggregation except fileset or model instance
                        # or model program aggregation
                        if src_aggr.is_fileset or src_aggr.is_model_instance or src_aggr.is_model_program:
                            return False
                    return tgt_aggregation.can_contain_aggregations
                elif tgt_aggregation is not None:
                    # moving a file or folder that is not part of any aggregation
                    return tgt_aggregation.supports_resource_file_move
                else:
                    # target a non-aggregation folder
                    return True
            return True

        def check_src_aggregation(src_aggr):
            """checks if the aggregation at the source allows rename/move action"""

            if src_aggr is None:
                return True

            if is_renaming_file:
                return src_aggr.supports_resource_file_rename
            elif is_moving_file:
                if src_aggr.supports_resource_file_move:
                    # source aggregation allows file move now check target folder
                    return check_target_folder(src_aggr)
                return False

        if src_file_dir != self.file_path:
            # see if the folder containing the file represents an aggregation
            aggregation_path = src_file_dir[len(self.file_path) + 1:]
            try:
                src_aggregation = self.get_aggregation_by_name(aggregation_path)
                if src_ext:
                    # file rename or move
                    return check_src_aggregation(src_aggregation)
                else:
                    # moving folder
                    return check_target_folder(src_aggregation)
            except ObjectDoesNotExist:
                # source folder does not represent an aggregation
                # check if the source file represents an aggregation
                # get source resource file object from source file path
                if src_ext:
                    # case of file rename or move
                    src_res_file = ResourceFile.get(self, src_file_name, aggregation_path)
                    src_aggregation = src_res_file.logical_file
                    return check_src_aggregation(src_aggregation)
                else:
                    # moving folder
                    # check if any of the files in the moved folder is part of aggregation
                    src_res_files = ResourceFile.list_folder(self, aggregation_path, sub_folders=True)
                    for src_file in src_res_files:
                        if src_file.has_logical_file:
                            if not check_target_folder(src_file.logical_file):
                                return False

                    return check_target_folder()
        else:
            # get source resource file object from source file path
            if src_ext:
                # case of file rename or move
                src_res_file = ResourceFile.get(self, src_file_name)
                # check if the source file is part of an aggregation
                src_aggregation = src_res_file.logical_file
                return check_src_aggregation(src_aggregation)
            else:
                # moving folder
                return check_target_folder()

    def can_add_files(self, target_full_path):
        """
        checks if file(s) can be uploaded to the specified *target_full_path*
        :param target_full_path: full folder path name where file needs to be uploaded to
        :return: True or False
        """
        istorage = self.get_irods_storage()
        if istorage.exists(target_full_path):
            path_to_check = target_full_path
        else:
            return False

        if not path_to_check.endswith("data/contents"):
            # it is not the base directory - it must be a directory under base dir
            if path_to_check.startswith(self.file_path):
                aggregation_path = path_to_check[len(self.file_path) + 1:]
            else:
                aggregation_path = path_to_check
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

    def get_model_program_aggregations(self):
        """Gets a list of model program aggregations in this (self) resource"""

        mp_aggregations = [aggr for aggr in self.logical_files if aggr.type_name() == "ModelProgramLogicalFile"]
        return mp_aggregations


# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
