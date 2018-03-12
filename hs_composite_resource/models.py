import os

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

        # check that target folder specified in dir_path does not have a parent folder
        if len(dir_path.split("/")) - len(self.file_path.split("/")) > 1:
            # target folder in dir_path contains parent folder
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
        :param  aggregation_name: (optional) name of the the aggregation for which xm documents
        be created
        """
        if aggregation_name is None:
            for aggregation in self.logical_files:
                aggregation.create_aggregation_xml_documents()
        else:
            for aggregation in self.logical_files:
                if aggregation.aggregation_name == aggregation_name:
                    aggregation.create_aggregation_xml_documents()
                    break

    def rename_aggregation(self, orig_aggregation_name, new_aggregation_name):
        """When a folder or file representing an aggregation is renamed, the associated
        map and metadata xml documents need to be deleted and then regenerated"""

        for aggregation in self.logical_files:
            if aggregation.aggregation_name == new_aggregation_name:
                istorage = self.get_irods_storage()
                xml_file_name = orig_aggregation_name + "_meta.xml"
                if aggregation.files.first().file_folder is not None:
                    xml_file_name = os.path.join(new_aggregation_name, xml_file_name)
                orig_xml_file_full_path = os.path.join(self.file_path, xml_file_name)
                if istorage.exists(orig_xml_file_full_path):
                    istorage.delete(orig_xml_file_full_path)
                aggregation.create_aggregation_xml_documents()
                break

    def supports_folder_creation(self, folder_full_path):
        """this checks if it is allowed to create a folder at the specified path"""

        if __debug__:
            assert(folder_full_path.startswith(self.file_path))

        # determine containing folder
        if "/" in folder_full_path:
            path_to_check, _ = os.path.split(folder_full_path)
        else:
            path_to_check = folder_full_path

        if path_to_check != self.file_path:
            res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                             res_file_obj.dir_path == path_to_check]

            for res_file_obj in res_file_objs:
                if res_file_obj.has_logical_file:
                    if not res_file_obj.logical_file.supports_resource_file_rename or \
                            not res_file_obj.logical_file.supports_resource_file_move:
                        return False

        return True

    def supports_rename_path(self, src_full_path, tgt_full_path):
        """checks if file/folder rename/move is allowed"""

        if __debug__:
            assert(src_full_path.startswith(self.file_path))
            assert(tgt_full_path.startswith(self.file_path))

        istorage = self.get_irods_storage()
        folder, file_name = os.path.split(tgt_full_path)
        basename, ext = os.path.splitext(file_name)
        if ext:
            tgt_file_dir = os.path.dirname(tgt_full_path)
        else:
            tgt_file_dir = tgt_full_path

        folder, file_name = os.path.split(src_full_path)
        basename, ext = os.path.splitext(file_name)
        if ext:
            src_file_dir = os.path.dirname(src_full_path)
        else:
            src_file_dir = src_full_path

        def check_directory():
            # may need to check both source and target directories
            dirs_to_check = []
            if not tgt_file_dir.endswith("data/contents") and istorage.exists(tgt_file_dir):
                # target dir is not the base directory - it must be a directory under base dir
                dirs_to_check.append(tgt_file_dir)
            if not src_file_dir.endswith("data/contents") and istorage.exists(tgt_file_dir):
                # source dir is not the base directory - it must be a directory under base dir
                dirs_to_check.append(src_file_dir)

            for path_to_check in dirs_to_check:
                # get the resource files in the path_to_check dir
                res_file_objs = ResourceFile.list_folder(resource=self, folder=path_to_check,
                                                         sub_folders=False)
                for res_file_obj in res_file_objs:
                    if res_file_obj.has_logical_file:
                        if not res_file_obj.logical_file.supports_resource_file_rename or \
                                not res_file_obj.logical_file.supports_resource_file_move:
                            return False

            return True

        res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                         res_file_obj.full_path == src_full_path]

        if res_file_objs:
            res_file_obj = res_file_objs[0]
            # src_full_path contains file name
            if res_file_obj.has_logical_file:
                if not res_file_obj.logical_file.supports_resource_file_rename or \
                        not res_file_obj.logical_file.supports_resource_file_move:
                    return False

            # check if the source and target directory allow move
            return check_directory()
        else:
            # src_full_path is a folder path without file name
            # tgt_full_path also must be a folder path without file name
            # check that if the target folder and source folder contain any files and if any of
            # those files allow moving
            return check_directory()

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
            res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                             res_file_obj.dir_path == path_to_check]

            for res_file_obj in res_file_objs:
                if res_file_obj.has_logical_file:
                    if not res_file_obj.logical_file.supports_resource_file_add:
                        return False
        return True

    def supports_zip(self, folder_to_zip):
        """check if the given folder can be zipped or not"""

        # find all the resource files in the folder to be zipped
        # this is being passed both qualified and unqualified paths!
        full_path = folder_to_zip
        if not full_path.startswith(self.file_path):
            full_path = os.path.join(self.file_path, full_path)

        if self.is_federated:
            res_file_objects = self.files.filter(
                object_id=self.id,
                fed_resource_file__startswith=full_path).all()
        else:
            res_file_objects = self.files.filter(object_id=self.id,
                                                 resource_file__startswith=full_path).all()

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

        if self.is_federated:
            res_file_objects = self.files.filter(
                object_id=self.id,
                fed_resource_file__startswith=full_path).all()
        else:
            res_file_objects = self.files.filter(
                object_id=self.id,
                resource_file__startswith=full_path).all()

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
