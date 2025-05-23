from django.db import models

from hs_core.signals import pre_check_bag_flag


class ResourceS3Mixin(models.Model):
    """ This contains S3 methods to be included as options for resources """
    class Meta:
        abstract = True

    def update_bag(self):
        """
        Update a bag if necessary.

        This uses the Django signal pre_check_bag_flag to prepare collections,
        and then checks the AVUs 'metadata_dirty' and 'bag_modified' to determine
        whether to regenerate the metadata files and/or bag.

        This is a synchronous update. The call waits until the update is finished.
        """
        from hs_core.tasks import create_bag_by_s3
        from hs_core.hydroshare.resource import check_resource_type
        from hs_core.hydroshare.hs_bagit import create_bag_metadata_files

        # send signal for pre_check_bag_flag
        resource_cls = check_resource_type(self.resource_type)
        pre_check_bag_flag.send(sender=resource_cls, resource=self)

        metadata_dirty = self.getAVU('metadata_dirty')
        bag_modified = self.getAVU('bag_modified')

        if metadata_dirty:  # automatically cast to Bool
            create_bag_metadata_files(self)
            self.setAVU('metadata_dirty', False)

        # the ticket system does synchronous bag creation.
        # async bag creation isn't supported.
        if bag_modified:  # automatically cast to Bool
            create_bag_by_s3(self.short_id)
            self.setAVU('bag_modified', False)

    def update_metadata_files(self):
        """
        Make the metadata files resourcemetadata.xml and resourcemap.xml up to date.

        This checks the "metadata dirty" AVU before updating files if necessary.
        """
        from hs_core.hydroshare.hs_bagit import create_bag_metadata_files

        metadata_dirty = self.getAVU('metadata_dirty')
        if metadata_dirty:
            create_bag_metadata_files(self)
            self.setAVU('metadata_dirty', False)


class ResourceFileS3Mixin(models.Model):
    """ This contains S3 functions related to resource files """
    class Meta:
        abstract = True
