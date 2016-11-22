# coding=utf-8
from django.db import models
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor


class CompositeResource(BaseResource):
    objects = ResourceManager("CompositeResource")

    class Meta:
        verbose_name = 'Composite'
        proxy = True

    @property
    def can_be_public_or_discoverable(self):
        # TODO: This needs to be unit tested
        if not super(BaseResource, self).can_be_public_or_discoverable:
            return False
        for lf in self.logical_files:
            if not lf.metadata.has_all_required_elements():
                return False

        return True

    def get_metadata_xml(self, pretty_print=True):
        from lxml import etree
        # TODO: (Pabitra) use super class' s get_metadata_xml() instead
        # of the following code line
        # get the xml string representation of the core metadata elements
        xml_string = self.metadata.get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.metadata.NAMESPACES)

        for lf in self.logical_files:
            lf.metadata.add_to_xml_container(container)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)



# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(CompositeResource)(resource_processor)

import receivers