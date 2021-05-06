import os
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, ResourceFile, resource_processor


from hs_file_types.models import GenericLogicalFile
from hs_file_types.models.base import RESMAP_FILE_ENDSWITH, METADATA_FILE_ENDSWITH
from hs_file_types.utils import update_target_temporal_coverage, update_target_spatial_coverage


logger = logging.getLogger(__name__)


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
        return True

    def set_default_logical_file(self):
        """sets an instance of GenericLogicalFile to any resource file objects of this instance
        of the resource that is not already associated with a logical file. """

        for res_file in self.files.all():
            if not res_file.has_logical_file:
                logical_file = GenericLogicalFile.create()
                res_file.logical_file_content_object = logical_file
                res_file.save()

    def get_folder_aggregation_object(self, dir_path):
        """Returns an aggregation (file type) object if the specified folder *dir_path* represents a
         file type aggregation (logical file), otherwise None.

         :param dir_path: Resource file directory path (full folder path starting with resource id)
         for which the aggregation object to be retrieved
        """

        aggregation_path = dir_path[len(self.file_path) + 1:]
        return self.filesetlogicalfile_set.filter(folder=aggregation_path).first()

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

        :return If the specified folder is already represents an aggregation or does
        not contain any files then returns False, otherwise True
        """

        if self.get_folder_aggregation_object(dir_path) is not None:
            # target folder is already an aggregation
            return False

        irods_path = dir_path
        if self.is_federated:
            irods_path = os.path.join(self.resource_federation_path, irods_path)

        files_in_path = ResourceFile.list_folder(self, folder=irods_path, sub_folders=True)
        # if there are any files in the dir_path, we can set the folder to fileset aggregation
        return len(files_in_path) > 0

    @property
    def supports_folders(self):
        """ allow folders for CompositeResources """
        return True

    @property
    def supports_logical_file(self):
        """ if this resource allows associating resource file objects with logical file"""
        return True

    def _recreate_fileset_xml_docs(self, folder):
        """Recreates xml files for all fileset aggregations that exist under the path 'folder'
        as well as for any parent fileset that may exist relative to path 'folder'
        """

        filesets = self.filesetlogicalfile_set.filter(folder__startswith=folder)
        for fs in filesets:
            fs.create_aggregation_xml_documents()

        # Also need to recreate xml doc for any parent fileset that may exist relative to path
        # *folder*
        if '/' in folder:
            path = os.path.dirname(folder)
            parent_fs = self.get_fileset_aggregation_in_path(path)
            if parent_fs is not None:
                parent_fs.create_aggregation_xml_documents()

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

        # recreate xml files for all fileset aggregations that exist under new_folder
        if new_folder.startswith(self.file_path):
            new_folder = new_folder[len(self.file_path) + 1:]

        if old_folder.startswith(self.file_path):
            old_folder = old_folder[len(self.file_path) + 1:]

        # first update folder attribute of all filesets that exist under *old_folder*
        update_fileset_folder()
        self._recreate_fileset_xml_docs(folder=new_folder)

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

        istorage = self.get_irods_storage()

        # need to find out which of the following actions the user is trying to do:
        # renaming a file
        # renaming a folder
        # moving a file
        # moving a folder
        is_renaming_file = False
        is_moving_file = False
        is_moving_folder = False

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
            is_renaming_file = True
        elif src_ext:
            is_moving_file = True
        elif not istorage.exists(tgt_file_dir):
            # renaming folder - no restriction
            return True
        else:
            is_moving_folder = True

        def check_file_rename_or_move():
            # see if the folder containing the file represents an aggregation
            if src_file_dir != self.file_path:
                aggregation_path = src_file_dir[len(self.file_path) + 1:]
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.supports_resource_file_rename
                except ObjectDoesNotExist:
                    # check if the source file represents an aggregation
                    # get source resource file object from source file path
                    src_res_file = ResourceFile.get(self, src_file_name, aggregation_path)
                    aggregation = src_res_file.logical_file
                    if aggregation is None:
                        raise ObjectDoesNotExist("No aggregation found at {}".format(
                            aggregation_path))
                    if is_renaming_file:
                        return aggregation.supports_resource_file_rename
                    else:
                        return aggregation.supports_resource_file_move
            else:
                # get source resource file object from source file path
                src_res_file = ResourceFile.get(self, src_file_name)
                # check if the source file is part of an aggregation
                aggregation = src_res_file.logical_file
                if aggregation is None:
                    raise ObjectDoesNotExist("No aggregation found at {}".format(src_file_name))

                if is_renaming_file:
                    return aggregation.supports_resource_file_rename
                else:
                    return aggregation.supports_resource_file_move

        if is_renaming_file:
            # see if the folder containing the file represents an aggregation
            try:
                can_rename = check_file_rename_or_move()
                return can_rename
            except ObjectDoesNotExist:
                return True

        elif is_moving_file:
            # check source - see if the folder containing the file represents an aggregation
            try:
                can_move = check_file_rename_or_move()
                return can_move
            except ObjectDoesNotExist:
                return True

        elif is_moving_folder:
            return True

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

    def get_data_services_urls(self):
        """
        Generates data services URLs for the resource.
        If the resource contains any GeoFeature or GeoRaster content, and if it's public,
        generate data service endpoints.
        If the resource contains any multidimensional content and it's public,
        generate THREDDS catalog service endpoint as well.
        """

        if self.raccess.public is True:
            try:
                resource_data_types = [lf.data_type for lf in self.logical_files]

                if any(
                    data_type in [
                        'GeographicFeature', 'GeographicRaster'
                    ] for data_type in resource_data_types
                ):
                    wms_url = (
                        f'{settings.HSWS_GEOSERVER_URL}/wms?'
                        f'service=WMS&'
                        f'version=1.3.0&'
                        f'request=GetCapabilities&'
                        f'namespace=HS-{self.short_id}'
                    )
                else:
                    wms_url = None

                if 'GeographicFeature' in resource_data_types:
                    wfs_url = (
                        f'{settings.HSWS_GEOSERVER_URL}/HS-{self.short_id}/wfs?'
                        f'request=GetCapabilities'
                    )
                else:
                    wfs_url = None

                if 'GeographicRaster' in resource_data_types:
                    wcs_url = (
                        f'{settings.HSWS_GEOSERVER_URL}/wcs?'
                        f'service=WCS&'
                        f'version=1.1.0&'
                        f'request=GetCapabilities&'
                        f'namespace=HS-{self.short_id}'
                    )
                else:
                    wcs_url = None
            except Exception as e:
                logger.exception("get_data_services_urls: " + str(e))
                wms_url = None
                wfs_url = None
                wcs_url = None

            if 'Multidimensional' in resource_data_types:
                thredds_url = (
                    f'{settings.THREDDS_SERVER_URL}catalog/hydroshare/resources/{self.short_id}/data/contents/catalog.html'
                )
            else:
                thredds_url = None
        else:
            wms_url = None
            wfs_url = None
            wcs_url = None
            thredds_url = None

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


# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
