import os

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor

from hs_file_types.models import GenericLogicalFile


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

    @property
    def supports_logical_file(self):
        """ if this resource allows associating resource file objects with logical file"""
        return True

    def get_metadata_xml(self, pretty_print=True):
        from lxml import etree

        # get resource level core metadata as xml string
        xml_string = super(CompositeResource, self).get_metadata_xml(pretty_print=False)
        # add file type metadata xml

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.metadata.NAMESPACES)

        for lf in self.logical_files:
            lf.metadata.add_to_xml_container(container)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def supports_folder_creation(self, folder_full_path):
        """this checks if it is allowed to create a folder at the specified path"""

        path_parts = folder_full_path.split("/")
        # remove the new folder name from the path
        path_parts = path_parts[:-1]
        path_to_check = "/".join(path_parts)
        if not path_to_check.endswith("/data/contents"):
            res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                             res_file_obj.dir_path == path_to_check]

            for res_file_obj in res_file_objs:
                if not res_file_obj.logical_file.supports_resource_file_rename or \
                        not res_file_obj.logical_file.supports_resource_file_move:
                    return False

        return True

    def supports_move_or_rename_file_or_folder(self, src_full_path, tgt_full_path):
        """checks if file/folder rename/move is allowed"""

        istorage = self.get_irods_storage()
        tgt_file_dir = os.path.dirname(tgt_full_path)
        src_file_dir = os.path.dirname(src_full_path)

        def check_target_directory():
            path_to_check = ''
            if istorage.exists(tgt_file_dir):
                path_to_check = tgt_file_dir
            else:
                if tgt_file_dir.startswith(src_file_dir):
                    path_to_check = src_file_dir

            if path_to_check and not path_to_check.endswith("data/contents"):
                # it is not the base directory - it must be a directory under base dir
                res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                                 res_file_obj.dir_path == path_to_check]

                for res_file_obj in res_file_objs:
                    if not res_file_obj.logical_file.supports_resource_file_rename or \
                            not res_file_obj.logical_file.supports_resource_file_move:
                        return False
            return True

        res_file_objs = [res_file_obj for res_file_obj in self.files.all() if
                        res_file_obj.full_path == src_full_path]

        if res_file_objs:
            res_file_obj = res_file_objs[0]
            # src_full_path contains file name
            if not res_file_obj.logical_file.supports_resource_file_rename or \
                    not res_file_obj.logical_file.supports_resource_file_move:
                return False

            # check if the target directory allows stuff to be moved there
            return check_target_directory()
        else:
            # src_full_path is a folder path without file name
            # tgt_full_path also must be a folder path without file name
            # check that if the target folder contains any files and if any of those files
            # allow moving stuff there
            return check_target_directory()

    def supports_zip(self, folder_to_zip):
        """check if the given folder can be zipped or not"""

        # find all the resource files in the folder to be zipped
        if self.resource_federation_path:
            res_file_objects = self.files.filter(
                object_id=self.id,
                fed_resource_file_name_or_path__contains=folder_to_zip).all()
        else:
            res_file_objects = self.files.filter(object_id=self.id,
                                                 resource_file__contains=folder_to_zip).all()

        # check any logical file associated with the resource file supports zip functionality
        for res_file in res_file_objects:
            if not res_file.logical_file.supports_zip:
                return False

        return True

    def supports_delete_original_folder_on_zip(self, original_folder):
        """check if the specified folder can be deleted at the end of zipping that folder"""

        # find all the resource files in the folder to be deleted
        if self.resource_federation_path:
            res_file_objects = self.files.filter(
                object_id=self.id,
                fed_resource_file_name_or_path__contains=original_folder).all()
        else:
            res_file_objects = self.files.filter(object_id=self.id,
                                                 resource_file__contains=original_folder).all()

        # check any logical file associated with the resource file supports deleting the folder
        # after its zipped
        for res_file in res_file_objects:
            if not res_file.logical_file.supports_delete_original_folder_on_zip:
                return False

        return True


# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
