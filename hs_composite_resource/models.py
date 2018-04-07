import os

from django.core.exceptions import ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, ResourceFile, resource_processor


from hs_file_types.models import GenericLogicalFile, GeoFeatureLogicalFile, GeoRasterLogicalFile, \
    NetCDFLogicalFile, TimeSeriesLogicalFile


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

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
        files_in_folder = [res_file for res_file in self.files.all()
                           if res_file.dir_path == dir_path]
        for fl in files_in_folder:
            if fl.has_logical_file:
                return fl.logical_file
        return None

    def get_folder_aggregation_type_to_set(self, dir_path):
        """Returns an aggregation (file type) type that the specified folder *dir_path* can
        possibly be set to.

        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which the possible aggregation type that can be set needs to be determined

        :return If the specified folder is already represents an aggregation or does
        not contain suitable file(s) then returns "" (empty string). If the specified folder
        contains only the files that meet the requirements of a supported aggregation, and
        does not contain other folders or does not have a parent folder then return the
        class name of that matching aggregation type.
        """
        aggregation_type_to_set = ""
        if self.get_folder_aggregation_object(dir_path) is not None:
            # target folder is already an aggregation
            return aggregation_type_to_set

        istorage = self.get_irods_storage()
        store = istorage.listdir(dir_path)
        if store[0]:
            # seems there are folders under dir_path - no aggregation type can be set if the target
            # folder contains other folders
            return aggregation_type_to_set

        files_in_folder = [res_file for res_file in self.files.all()
                           if res_file.dir_path == dir_path]
        if not files_in_folder:
            # folder is empty
            return aggregation_type_to_set
        if len(files_in_folder) > 1:
            # check for geo feature
            aggregation_type_to_set = GeoFeatureLogicalFile.check_files_for_aggregation_type(
                files_in_folder)
            if aggregation_type_to_set:
                return aggregation_type_to_set

            # check for raster
            aggregation_type_to_set = GeoRasterLogicalFile.check_files_for_aggregation_type(
                files_in_folder)
            if aggregation_type_to_set:
                return aggregation_type_to_set
        else:
            # check for raster
            aggregation_type_to_set = GeoRasterLogicalFile.check_files_for_aggregation_type(
                files_in_folder)
            if aggregation_type_to_set:
                return aggregation_type_to_set
            # check for NetCDF aggregation type
            aggregation_type_to_set = NetCDFLogicalFile.check_files_for_aggregation_type(
                files_in_folder)
            if aggregation_type_to_set:
                return aggregation_type_to_set
            # check for TimeSeries aggregation type
            aggregation_type_to_set = TimeSeriesLogicalFile.check_files_for_aggregation_type(
                files_in_folder)
            if aggregation_type_to_set:
                return aggregation_type_to_set

        return aggregation_type_to_set

    @property
    def supports_folders(self):
        """ allow folders for CompositeResources """
        return True

    @property
    def supports_logical_file(self):
        """ if this resource allows associating resource file objects with logical file"""
        return True

    def get_metadata_xml(self, pretty_print=True, include_format_elements=True):
        from lxml import etree

        # get resource level core metadata as xml string
        # for composite resource we don't want the format elements at the resource level
        # as they are included at the aggregation map xml document
        xml_string = super(CompositeResource, self).get_metadata_xml(pretty_print=False,
                                                                     include_format_elements=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def create_aggregation_xml_documents(self, aggregation_name=None):
        """Creates aggregation map and metadata xml files for each of the contained aggregations

        :param  aggregation_name: (optional) name of the the specific aggregation for which xml
        documents need to be created
        """

        def reset_metadata_is_dirty(aggregation):
            # resets the metadata.is_dirty to False if the
            # aggregation is not a NetCDF or Time series aggregation.
            # NetCDF and Time series aggregations reset metadata.is_dirty
            # as part of updating the content file
            if aggregation.get_aggregation_class_name() not in \
                    ("NetCDFLogicalFile", "TimeSeriesLogicalFile"):
                aggregation.metadata.is_dirty = False
                aggregation.metadata.save()

        if aggregation_name is None:
            for aggregation in self.logical_files:
                if aggregation.metadata.is_dirty:
                    aggregation.create_aggregation_xml_documents()
                    reset_metadata_is_dirty(aggregation)
        else:
            try:
                aggregation = self.get_aggregation_by_name(aggregation_name)
                if aggregation.metadata.is_dirty:
                    aggregation.create_aggregation_xml_documents()
                    reset_metadata_is_dirty(aggregation)
            except ObjectDoesNotExist:
                # aggregation_name must be a folder path that doesn't represent an aggregation
                # there may be single file aggregation in that folder for which xml documents
                # need to be created
                self._recreate_xml_docs_for_folder(aggregation_name, check_metadata_dirty=True)

    def _recreate_xml_docs_for_folder(self, folder, check_metadata_dirty=False):
        """Re-creates xml metadata and map documents associated with the specified folder.
        If the *folder* represents an aggregation then map and metadata xml documents are
        recreated only for that aggregation. Otherwise, xml documents are created for any
        aggregation that may exist in the specified folder and its sub-folders.

        :param  folder: folder for which xml documents need to be re-created
        :param  check_metadata_dirty: if true, then xml files will be created only if the
        aggregation metadata is dirty
        """

        # first check if the the folder represents an aggregation
        try:
            aggregation = self.get_aggregation_by_name(folder)
            if check_metadata_dirty:
                if aggregation.metadata.is_dirty:
                    aggregation.create_aggregation_xml_documents()
            else:
                aggregation.create_aggregation_xml_documents()
                # if we found an aggregation by the folder name that means this folder doesn't
                # have any sub folders as multi-file aggregation folder can't have sub folders
        except ObjectDoesNotExist:
            # create xml map and metadata xml documents for all aggregations that exist
            # in *folder* and its sub-folders
            if not folder.startswith(self.file_path):
                folder = os.path.join(self.file_path, folder)

            res_file_objects = ResourceFile.list_folder(self, folder)
            aggregations = []
            for res_file in res_file_objects:
                if res_file.has_logical_file and res_file.logical_file not in aggregations:
                    aggregations.append(res_file.logical_file)

            if check_metadata_dirty:
                aggregations = [aggr for aggr in aggregations if aggr.metadata.is_dirty]
            for aggregation in aggregations:
                aggregation.create_aggregation_xml_documents()

    def get_aggregation_by_name(self, name):
            """Get an aggregation that matches the aggregation name specified by *name*
            :param  name: name of the aggregation to find
            :return an aggregation object if found
            :raises ObjectDoesNotExist if no matching aggregation is found
            """
            for aggregation in self.logical_files:
                if aggregation.aggregation_name == name:
                    return aggregation

            raise ObjectDoesNotExist("No matching aggregation was found for name:{}".format(name))

    def recreate_aggregation_xml_docs(self, orig_aggr_name, new_aggr_name):
        """
        When a folder or file representing an aggregation is renamed or moved,
        the associated map and metadata xml documents are deleted
        and then regenerated
        :param  orig_aggr_name: original aggregation name - used for deleting existing
        xml documents
        :param  new_aggr_name: new aggregation name - used for finding a matching
        aggregation so that new xml documents can be recreated
        """

        """
        check if the following logic meets the use cases of file/folder rename/move
        case-1 (renaming a single aggregation at the root):
                orgi_aggr: text.txt
                new_aggr: text_rename.txt
                Note: needs deleting old xml files

        case-2 (renaming a single aggregation inside a folder):
                orgi_aggr: folder_1/text.txt
                new_aggr: folder_1/text_rename.txt    
                Note: needs deleting old xml files

        case-3 (renaming a folder that conatins a single aggregation):
                orgi_aggr: folder_1/text.txt
                new_aggr: folder_2/text.txt    
                Note: no need for deleting old xml files

        case-3.1 (renaming a folder that conatins a single aggregation):
                orgi_aggr: folder_1/folder_A/text.txt
                new_aggr: folder_2/folder_A/text.txt    
                Note: no need for deleting old xml files

        case-4 (moving a single aggregation file to a folder: folder_1):
                orgi_aggr: text.txt
                new_aggr: folder_1/text.txt    
                Note: needs deleting old xml files

        case-4.1 (moving a single aggregation file to a folder: folder_2):
                orgi_aggr: /folder_1/text.txt
                new_aggr: folder_2/text.txt    
                Note: needs deleting old xml files

        case-5 (moving a folder: folder_1 containing a single aggregation file to a folder: folder_2):
                orgi_aggr: /folder_1/text.txt
                new_aggr: folder_2/folder_1/text.txt    
                Note: no need for deleting old xml files                

        case-6 (renaming a folder that conatins a multi-file aggregation):
                orgi_aggr: folder_1 [folder_1/logan.nc]
                new_aggr: folder_2 [folder_2/logan.nc]    
                Note: needs deleting old xml files

        case-7 (moving a folder:folder_1 that conatins a multi-file aggregation to another folder: folder_2):
                orgi_aggr: folder_1 [folder_1/logan.nc]
                new_aggr: folder_2/folder_1 [folder_2/folder_1/logan.nc]
                Note: no need for deleting old xml files    


        case-8 (renaming a non-aggregation file at the root):
                orgi_aggr: text.txt
                new_aggr: text_rename.txt
                Note: no need for deleting old xml files or generating xml files    

        case-9 (renaming a non-aggregation file inside a folder):
                orgi_aggr: folder_1/text.txt
                new_aggr: folder_1/text_rename.txt    
                Note: no need for deleting old xml files or generating xml files    

        case-10 (renaming a folder that conatins a non-aggregation files):
                orgi_aggr: folder_1
                new_aggr: folder_2    
                Note: no need for deleting old xml files or generating xml files

        case-11 (moving a single non-aggregation file to a folder: folder_1):
                orgi_aggr: text.txt
                new_aggr: folder_1/text.txt    
                Note: no need for deleting old xml files or generating xml files

        case-12 (moving a folder: folder_1 containing a non-aggregation file to a folder: folder_2):
                orgi_aggr: folder_1
                new_aggr: folder_2/folder_1    
                Note: no need for deleting old xml files or generating xml files

        case-13 (moving a folder:folder_1 that conatins multile multi-file aggregation to another folder: folder_2):
                orgi_aggr: folder_1 [folder_1/netcdf/logan.nc, folder_1/raster/logan.tif]
                new_aggr: folder_2/folder_1 [folder_2/folder_1/netcdf/logan.nc, folder_2/folder_1/raster/logan.tif]
                Note: no need for deleting old xml files    

        case-14 (moving a folder:folder_1 that conatins multile multi-file aggregation and single file aggregations to another folder: folder_2):
                orgi_aggr: folder_1 [folder_1/netcdf/logan.nc, folder_1/rasetr/logan.tif, folder_1/text.txt]
                new_aggr: folder_2/folder_1 [folder_2/folder_1/netcdf/logan.nc, folder_2/folder_1/rasetr/logan.tif, folder_2/folder_1/text.txt]
                Note: no need for deleting old xml files                
        """

        def delete_old_xml_files(folder=''):
            meta_xml_file_name = orig_aggr_name + "_meta.xml"
            map_xml_file_name = orig_aggr_name + "_resmap.xml"
            if not folder:
                # case if file rename/move for single file aggregation
                meta_xml_file_full_path = os.path.join(self.file_path, meta_xml_file_name)
                map_xml_file_full_path = os.path.join(self.file_path, map_xml_file_name)
            else:
                # case of folder rename - multi-file aggregation
                _, meta_xml_file_name = os.path.split(meta_xml_file_name)
                _, map_xml_file_name = os.path.split(map_xml_file_name)
                meta_xml_file_full_path = os.path.join(self.file_path, folder, meta_xml_file_name)
                map_xml_file_full_path = os.path.join(self.file_path, folder, map_xml_file_name)

            if istorage.exists(meta_xml_file_full_path):
                istorage.delete(meta_xml_file_full_path)

            if istorage.exists(map_xml_file_full_path):
                istorage.delete(map_xml_file_full_path)

        # first check if the new_aggr_name is a folder path or file path
        name, ext = os.path.splitext(new_aggr_name)
        is_new_aggr_a_folder = ext == ''

        if is_new_aggr_a_folder:
            # case-3, case-5, case-6, case-7, case-10, case-12, case-13, case-14
            self._recreate_xml_docs_for_folder(new_aggr_name)
        else:
            # check if there is a matching single file aggregation
            try:
                # case-1, case-2, case-4 & 4.1
                aggregation = self.get_aggregation_by_name(new_aggr_name)
                aggregation.create_aggregation_xml_documents()
            except ObjectDoesNotExist:
                # case-8, case-9, case-11
                # the file path *new_aggr_name* is not a single file aggregation - no more
                # action is needed
                return

        # we have to delete old _meta.xml file and _resmap.xml file if they exist
        # first check if the orig_aggr_name is a folder path or file path
        istorage = self.get_irods_storage()
        is_folder_renamed = False
        is_file_moved = False
        is_file_renamed = False

        if not is_new_aggr_a_folder:
            # case of single file aggregation possible file rename or move
            # find if this a case of file renaming
            if '/' in new_aggr_name:
                # new aggregation name contains folder path
                new_folder, new_file_name = os.path.split(new_aggr_name)
                old_folder, old_file_name = os.path.split(orig_aggr_name)
                if new_file_name != old_file_name:
                    # case-2
                    is_file_renamed = True
                else:
                    # case-4
                    is_file_moved = True
            else:
                # case-1
                is_file_renamed = True
        else:
            # case of multi-file aggregation possible folder re-naming or folder move
            # find if this is a case of folder renaming
            if '/' in orig_aggr_name:
                _, moved_folder = os.path.split(orig_aggr_name)
            else:
                moved_folder = orig_aggr_name
            if not new_aggr_name.endswith(moved_folder):
                # case of folder renaming - handles case-6
                is_folder_renamed = True

        # case-3 & 3.1, 5, 13, 14 - there is no need to delete xml files as it is case of folder
        # renaming or folder moving

        if is_file_renamed or is_file_moved:
            # case of single file aggregation
            # case-1, case-2, case-4 & 4.1
            delete_old_xml_files()
        elif is_folder_renamed:
            # case of multi-file aggregation
            # folder move (case-7) does not require deleting old xml files in case of
            # multi-aggregation only folder rename requires deleting old xml files
            # case-6
            # old xml files need to be deleted only if the new folder represents an aggregation
            try:
                self.get_aggregation_by_name(new_aggr_name)
                delete_old_xml_files(folder=new_aggr_name)
            except ObjectDoesNotExist:
                # target folder is not an aggregation
                pass

    def supports_folder_creation(self, folder_full_path):
        """this checks if it is allowed to create a folder at the specified path
        :param  folder_full_path: the target path where the new folder needs to be created

        :return True or False
        """

        if __debug__:
            assert(folder_full_path.startswith(self.file_path))

        # determine containing folder
        if "/" in folder_full_path:
            path_to_check, _ = os.path.split(folder_full_path)
        else:
            path_to_check = folder_full_path

        # find if the path represents a multi-file aggregation
        if path_to_check.startswith(self.file_path):
            aggregation_path = path_to_check[len(self.file_path) + 1:]
        else:
            aggregation_path = path_to_check
        try:
            aggregation = self.get_aggregation_by_name(aggregation_path)
            return aggregation.can_contain_folders
        except ObjectDoesNotExist:
            # target path doesn't represent an aggregation - so it is OK to create a folder
            pass
        return True

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

        if is_renaming_file:
            # see if the folder containing the file represents an aggregation
            if src_file_dir != self.file_path:
                aggregation_path = src_file_dir[len(self.file_path) + 1:]
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.supports_resource_file_rename
                except ObjectDoesNotExist:
                    # check if the source file represents an aggregation
                    aggregation_path = os.path.join(aggregation_path, src_file_name)
                    try:
                        aggregation = self.get_aggregation_by_name(aggregation_path)
                        return aggregation.supports_resource_file_rename
                    except ObjectDoesNotExist:
                        # source is not an aggregation - no restriction
                        return True
            else:
                # check if the source file represents an aggregation
                aggregation_path = src_file_name
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.supports_resource_file_rename
                except ObjectDoesNotExist:
                    # source is not an aggregation - no restriction
                    return True
        elif is_moving_file:
            # check source - see if the folder containing the file represents an aggregation
            if src_file_dir != self.file_path:
                aggregation_path = src_file_dir[len(self.file_path) + 1:]
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.supports_resource_file_move
                except ObjectDoesNotExist:
                    # check if the source file represents an aggregation
                    aggregation_path = os.path.join(aggregation_path, src_file_name)
                    try:
                        aggregation = self.get_aggregation_by_name(aggregation_path)
                        if not aggregation.supports_resource_file_move:
                            return False
                    except ObjectDoesNotExist:
                        # source is not an aggregation
                        pass
            else:
                # check if the source file represents an aggregation
                aggregation_path = src_file_name
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    if not aggregation.supports_resource_file_move:
                        return False
                except ObjectDoesNotExist:
                    # source file is not an aggregation
                    pass

            # check target folder only if it is not the root
            if tgt_file_dir != self.file_path:
                aggregation_path = tgt_file_dir[len(self.file_path) + 1:]
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.supports_resource_file_add
                except ObjectDoesNotExist:
                    # target folder is not an aggregation - no restriction
                    return True
            return True
        elif is_moving_folder:
            # no check on source is needed in this case
            # check target - only if it is not the root
            if tgt_file_dir != self.file_path:
                aggregation_path = tgt_file_dir[len(self.file_path) + 1:]
                try:
                    aggregation = self.get_aggregation_by_name(aggregation_path)
                    return aggregation.can_contain_folders
                except ObjectDoesNotExist:
                    # target folder doesn't represent an aggrgation - no restriction
                    return True
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

# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
