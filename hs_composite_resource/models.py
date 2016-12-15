import os

from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

    class Meta:
        verbose_name = 'Composite'
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

    def check_folder_creation(self, folder_full_path):
        """this checks if it is allowed to create a folder by the given path
        if not allowed then raises ValidationError
        """
        # TODO: Need to have unit tests for this function
        path_parts = folder_full_path.split("/")
        # remove the new folder name from the path
        path_parts = path_parts[:-1]
        path_to_check = "/".join(path_parts)
        if not path_to_check.endswith("/data/contents"):
            err_msg = "Folder creation not allowed here."
            if self.resource_federation_path:
                res_file_objs = self.files.filter(
                    object_id=self.id,
                    fed_resource_file_name_or_path__contains=path_to_check).all()
            else:
                res_file_objs = self.files.filter(object_id=self.id,
                                                  resource_file__contains=path_to_check).all()
            for res_file_obj in res_file_objs:
                if not res_file_obj.logical_file.supports_resource_file_rename or \
                        not res_file_obj.logical_file.supports_resource_file_move:
                    raise ValidationError(err_msg)

    def check_move_or_rename_file_or_folder(self, src_full_path, tgt_full_path):
        """checks if file/folder rename/move is allowed
        If not allowed, raises ValidationError
        """

        err_msg = "File/folder move/rename is not allowed."
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
                if self.resource_federation_path:
                    res_file_objs = self.files.filter(
                        object_id=self.id,
                        fed_resource_file_name_or_path__contains=path_to_check).all()
                else:
                    res_file_objs = self.files.filter(
                        object_id=self.id,
                        resource_file__contains=path_to_check).all()
                for res_file_obj in res_file_objs:
                    if not res_file_obj.logical_file.supports_resource_file_rename or \
                            not res_file_obj.logical_file.supports_resource_file_move:
                        raise ValidationError(err_msg)

        if self.resource_federation_path:
            res_file_obj = self.files.filter(
                object_id=self.id,
                fed_resource_file_name_or_path=src_full_path).first()
        else:
            res_file_obj = self.files.filter(object_id=self.id,
                                             resource_file=src_full_path).first()
        if res_file_obj is not None:
            # src_full_path contains file name
            if not res_file_obj.logical_file.supports_resource_file_rename or \
                    not res_file_obj.logical_file.supports_resource_file_move:
                raise ValidationError(err_msg)

            # check if the target directory allows stuff to be moved there
            check_target_directory()
        else:
            # src_full_path is a folder path without file name
            # tgt_full_path also must be a folder path without file name
            # check that if the target folder contains any files and if any of those files
            # allow moving stuff there
            check_target_directory()

# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)
