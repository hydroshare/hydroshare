from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor


class ExternalResource(BaseResource):

    objects = ResourceManager('ExternalResource')

    # used during discovery as well as in all other places in UI where resource type is displayed
    display_name = 'External'

    class Meta:
        proxy = True
        verbose_name = 'External Resource'

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def allow_multiple_file_upload(cls):
        # cannot upload any file
        return False

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False

    @property
    def can_be_public_or_discoverable(self):
        return self.metadata.has_all_required_elements() and (self.resources.count() > 0)

    @property
    def can_be_submitted_for_metadata_review(self):
        return False


processor_for(ExternalResource)(resource_processor)
