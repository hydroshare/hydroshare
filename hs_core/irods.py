import os
from django.db import models
from django.core.exceptions import ValidationError, SuspiciousFileOperation


# Various iRODS functions required by resources.
class ResourceIRODSMixin(models.Model):

    class Meta:
        abstract = True

    def create_folder(self, folder_path):
        """
        create a sub-folder/sub-collection in hydroshareZone or any federated zone used for
        HydroShare resource backend store.
        :param folder_path: relative path for the new folder to be created under resource
        collection/directory
        :return:
        """
        if __debug__:  # no more
            assert(not folder_path.startswith("data/contents/"))

        istorage = self.get_irods_storage()
        coll_path = os.path.join(self.file_path, folder_path)

        if not self.supports_folder_creation(coll_path):
            raise ValidationError("Folder creation is not allowed here.")

        istorage.session.run("imkdir", None, '-p', coll_path)

    def remove_folder(self, user, folder_path):
        """
        remove a sub-folder/sub-collection in hydroshareZone or any federated zone used for
        HydroShare resource backend store.
        :param user: requesting user
        :param folder_path: the relative path for the folder to be removed under res_id collection.
        :return:
        """
        from hs_core.views.utils import remove_irods_folder_in_django
        from hs_core.hydroshare.utils import resource_modified

        if __debug__:  # no more
            assert(not folder_path.startswith("data/contents/"))

        istorage = self.get_irods_storage()
        coll_path = os.path.join(self.file_path, folder_path)

        # TODO: Pabitra - resource should check here if folder can be removed
        istorage.delete(coll_path)

        remove_irods_folder_in_django(self, istorage, coll_path, user)

        if self.raccess.public or self.raccess.discoverable:
            if not self.can_be_public_or_discoverable:
                self.raccess.public = False
                self.raccess.discoverable = False
                self.raccess.save()

        resource_modified(self, user, overwrite_bag=False)

    def list_folder(self, folder_path):
        """
        list a sub-folder/sub-collection in hydroshareZone or any federated zone used for
        HydroShare resource backend store.
        :param user: requesting user
        :param folder_path: the relative path for the folder to be listed under res_id collection.
        :return:
        """
        if __debug__:
            assert(not folder_path.startswith("data/contents/"))

        istorage = self.get_irods_storage()
        coll_path = os.path.join(self.file_path, folder_path)

        return istorage.listdir(coll_path)

    def move_or_rename_file_or_folder(self, user, src_path, tgt_path, validate_move_rename=True):
        """
        Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
        resource backend store.
        :param user: requesting user
        :param src_path: the relative paths for the source file or folder under resource collection
        :param tgt_path: the relative paths for the target file or folder under resource collection
        :param validate_move_rename: if True, then only ask resource type to check if this action is
                allowed. Sometimes resource types internally want to take this action but disallow
                this action by a user. In that case resource types set this parameter to False to
                allow this action.
        :return:

        """
        from hs_core.hydroshare.utils import resource_modified
        from hs_core.views.utils import rename_irods_file_or_folder_in_django

        if __debug__:
            assert(not src_path.startswith("data/contents/"))
            assert(not tgt_path.startswith("data/contents/"))

        istorage = self.get_irods_storage()
        src_full_path = os.path.join(self.file_path, src_path)
        tgt_full_path = os.path.join(self.file_path, tgt_path)

        tgt_file_name = os.path.basename(tgt_full_path)
        tgt_file_dir = os.path.dirname(tgt_full_path)
        src_file_name = os.path.basename(src_full_path)
        src_file_dir = os.path.dirname(src_full_path)

        # ensure the target_full_path contains the file name to be moved or renamed to
        # if we are moving to a directory, put the filename into the request.
        if src_file_dir != tgt_file_dir and tgt_file_name != src_file_name:
            tgt_full_path = os.path.join(tgt_full_path, src_file_name)

        if validate_move_rename:
            # raise ValidationError if move/rename is not allowed by specific resource type
            if not self.supports_rename_path(src_full_path, tgt_full_path):
                raise ValidationError("File/folder move/rename is not allowed.")

        istorage.moveFile(src_full_path, tgt_full_path)

        rename_irods_file_or_folder_in_django(self, src_path, tgt_path)

        resource_modified(self, user, overwrite_bag=False)


class ResourceFileIRODSMixin(models.Model):
    class Meta:
        abstract = True
