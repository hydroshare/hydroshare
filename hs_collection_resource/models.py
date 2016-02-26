from lxml import etree

from django.db import models
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare.utils import current_site_url

class CollectionResource(BaseResource):
    objects = ResourceManager('CollectionResource')

    class Meta:
        proxy = True
        verbose_name = 'Collection Resource'

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False

    @property
    def metadata(self):
        md = CollectionMetaData()
        return self._get_metadata(md)

processor_for(CollectionResource)(resource_processor)

class CollectionItems(AbstractMetaDataElement):
    term = 'CollectionItems'
    collection_items = models.ManyToManyField(BaseResource, null=True, blank=True)

    def get_collection_items_str(self):
        return ','.join([res.title+":" + res.resource_type for res in self.collection_items.all()])

    @classmethod
    def create(cls, **kwargs):
        if 'collection_items' in kwargs:
            metadata_obj = kwargs['content_object']
            new_meta_instance = CollectionItems.objects.create(content_object=metadata_obj)
            for res_id in kwargs['collection_items']:
                res = BaseResource.objects.filter(short_id__iexact=res_id)
                if res.exists():
                    new_meta_instance.collection_items.add(res[0])
            return new_meta_instance
        else:
            raise ObjectDoesNotExist("No collection_items parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = CollectionItems.objects.get(id=element_id)
        if meta_instance:
            if 'collection_items' in kwargs:
                meta_instance.collection_items.clear()
                for res_id in kwargs['collection_items']:
                    qs = BaseResource.objects.filter(short_id__iexact=res_id)
                    if qs.exists():
                        meta_instance.collection_items.add(qs[0])
                meta_instance.save()
                if meta_instance.collection_items.all().count() == 0:
                    meta_instance.delete()
            else:
                raise ObjectDoesNotExist("No collection_items parameter was found in the **kwargs list")
        else:
            raise ObjectDoesNotExist("No CollectionItems object was found with the provided id: %s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CollectionItems element can't be deleted.")


class CollectionMetaData(CoreMetaData):
    collection_items = generic.GenericRelation(CollectionItems)

    @classmethod
    def get_supported_element_names(cls):
        elements = super(CollectionMetaData, cls).get_supported_element_names()
        elements.append('CollectionItems')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        else:
            # check if no member resource exists
            if self.collection_items.first().collection_items.all().count() == 0:
                return False
            # check if all member resources are either public or private
            for res in self.collection_items.first().collection_items.all():
                if not res.raccess.public and not res.raccess.discoverable:
                    return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(CollectionMetaData, self).get_required_missing_elements()
        if not self.collection_items.all().first():
            missing_required_elements.append('Collection Resources')

        return missing_required_elements

    def get_xml(self):
        # get the xml string representation of the core metadata elements
        xml_string = super(CollectionMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)
        CollectionItems_container = etree.SubElement(container, '{%s}CollectionItems' % self.NAMESPACES['hsterms'])
        collection_items = self.collection_items.first()
        if collection_items:
            for res in collection_items.collection_items.all():
                hsterms_method = etree.SubElement(CollectionItems_container, '{%s}CollectionItem' % self.NAMESPACES['hsterms'])
                hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
                hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}ResourceID' % self.NAMESPACES['hsterms'])
                hsterms_name.text = res.short_id
                hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}PageURL' % self.NAMESPACES['hsterms'])
                hsterms_name.text = current_site_url() + "/resource/" + res.short_id + "/"

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(CollectionMetaData, self).delete_all_elements()
        self.collection_items.all().delete()

# import receivers # never delete this otherwise non of the receiver function will work
