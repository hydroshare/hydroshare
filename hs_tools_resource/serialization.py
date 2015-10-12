import decimal

import rdflib

from django.db import transaction

from hs_core.serialization import GenericResourceMeta


class ToolResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of ToolResource instances.
    """
    def __init__(self):
        super(ToolResourceMeta, self).__init__()

        self.url_base = None
        self.resource_types = []
        self.fees = []
        self.version = None

    def __str__(self):
        fees_str = ';'.join([str(f) for f in self.fees])
        msg = "{classname} url_base: {url_base}, resource_types: {resource_types}, "
        msg += "fees: {fees}, version: {version}"
        msg = msg.format(classname=type(self).__name__,
                         url_base=self.url_base,
                         resource_types=str(self.resource_types),
                         fees=fees_str,
                         version=self.version)
        return msg

    def __unicode__(self):
        return unicode(str(self))

    def _read_resource_metadata(self):
        super(ToolResourceMeta, self)._read_resource_metadata()

        print("--- ToolResource ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get RequestUrlBase
        for s, p, o in self._rmeta_graph.triples((None, hsterms.RequestUrlBase, None)):
            # Get value
            value_lit = self._rmeta_graph.value(o, hsterms.value)
            if value_lit is None:
                msg = "RequestUrlBase for ToolResource was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.url_base = str(value_lit)

        # Get ResourceType
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ResourceType, None)):
            # Get type
            type_lit = self._rmeta_graph.value(o, hsterms.type)
            if type_lit is not None:
                self.resource_types.append(str(type_lit))

        # Get Fee
        for s, p, o in self._rmeta_graph.triples((None, hsterms.Fee, None)):
            # Get value
            value_lit = self._rmeta_graph.value(o, hsterms.value)
            if value_lit is None:
                msg = "Fee:value for ToolResource was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            value_str = str(value_lit)
            # Get description
            description_lit = self._rmeta_graph.value(o, hsterms.description)
            if description_lit is None:
                msg = "Fee:description for ToolResource was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            description_str = str(description_lit)

            fee = ToolResourceMeta.ToolFee(description_str, value_str)
            self.fees.append(fee)

        # Get ToolVersion
        for s, p, o in self._rmeta_graph.triples((None, hsterms.ToolVersion, None)):
            # Get value
            value_lit = self._rmeta_graph.value(o, hsterms.value)
            if value_lit is None:
                msg = "ToolVersion for ToolResource was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.version = str(value_lit)

        print("\t\t{0}".format((str(self))))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: ToolResource instance
        """
        super(ToolResourceMeta, self).write_metadata_to_resource(resource)

        if self.url_base:
            resource.metadata.url_bases.all().delete()
            resource.metadata.create_element('RequestUrlBase',
                                             value=self.url_base)
        if len(self.resource_types) > 0:
            resource.metadata.res_types.all().delete()
            for t in self.resource_types:
                resource.metadata.create_element('ToolResourceType',
                                                 tool_res_type=t)
        if len(self.fees) > 0:
            resource.metadata.fees.all().delete()
            for f in self.fees:
                resource.metadata.create_element('Fee',
                                                 description=f.description,
                                                 value=f.value)
        if self.version:
            resource.metadata.versions.all().delete()
            resource.metadata.create_element('ToolVersion',
                                             value=self.version)

    class ToolFee(object):
        def __str__(self):
            msg = "{classname} description: {description}, value: {value}"
            msg = msg.format(classname=type(self).__name__,
                             description=self.description,
                             value=str(self.value))
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, description, value):
            self.description = description
            self.value = decimal.Decimal(value)
