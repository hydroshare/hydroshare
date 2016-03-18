from lxml import etree

from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericRelation
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

class Collection(AbstractMetaDataElement):
    term = 'Collection'
    resources = models.ManyToManyField(BaseResource, null=True, blank=True)

    def get_resource_id_list(self):
        return [res.short_id for res in self.resources.all()]

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        if 'resource_id_list' in kwargs:
            metadata_obj = kwargs['content_object']
            collection_meta_obj = Collection.objects.create(content_object=metadata_obj)
            for res_id in kwargs['resource_id_list']:
                res = BaseResource.objects.filter(short_id__exact=res_id)
                if res.exists():
                    collection_meta_obj.resources.add(res[0])
                else:
                    raise ObjectDoesNotExist("No resource was found with the provided id: %s" % res_id)
            return collection_meta_obj
        else:
            raise ObjectDoesNotExist("No resource_id_list parameter was found in the **kwargs list")

    @classmethod
    @transaction.atomic
    def update(cls, element_id, **kwargs):
        collection_meta_obj = Collection.objects.get(id=element_id)

        if 'resource_id_list' in kwargs:
            collection_meta_obj.resources.clear()
            for res_id in kwargs['resource_id_list']:
                qs = BaseResource.objects.filter(short_id__exact=res_id)
                if qs.exists():
                    collection_meta_obj.resources.add(qs[0])
                else:
                    raise ObjectDoesNotExist("No resource was found with the provided id: %s" % res_id)
            collection_meta_obj.save()
            if collection_meta_obj.resources.all().count() == 0:
                collection_meta_obj.delete()
        else:
            raise ObjectDoesNotExist("No resource_id_list parameter was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Collection element can't be deleted.")


class CollectionMetaData(CoreMetaData):

    _collection = GenericRelation(Collection)

    @property
    def collection(self):
        return self._collection.first()

    @classmethod
    def get_supported_element_names(cls):
        elements = super(CollectionMetaData, cls).get_supported_element_names()
        elements.append('Collection')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        else:
            # check if no member resource exists
            if self.collection.resources.all().count() == 0:
                return False
            # check if all member resources are NOT private
            for res in self.collection.resources.all():
                if not res.raccess.public and not res.raccess.discoverable:
                    return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(CollectionMetaData, self).get_required_missing_elements()
        if not self._collection.first():
            missing_required_elements.append('Collection Resources')

        return missing_required_elements

    def get_xml(self):
        # get the xml string representation of the core metadata elements
        xml_string = super(CollectionMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)
        collection_container = etree.SubElement(container, '{%s}Collection' % self.NAMESPACES['hsterms'])
        if self.collection:
            for res in self.collection.resources.all():
                hsterms_method = etree.SubElement(collection_container, '{%s}Collection' % self.NAMESPACES['hsterms'])
                hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
                hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}ResourceID' % self.NAMESPACES['hsterms'])
                hsterms_name.text = res.short_id
                hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}LandingPageURL' % self.NAMESPACES['hsterms'])
                hsterms_name.text = current_site_url() + "/resource/" + res.short_id + "/"

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(CollectionMetaData, self).delete_all_elements()
        self._collection.all().delete()

# import receivers # never delete this otherwise non of the receiver function will work
