import defusedxml.sax

import rdflib

from django.db import transaction

from hs_core.serialization import GenericResourceMeta


class NetcdfResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of NetcdfResource instances.
    """
    def __init__(self):
        super(NetcdfResourceMeta, self).__init__()

        self.variables = []
        self.spatial_reference = None

    @staticmethod
    def include_resource_file(resource_filename):
        """
        :param resource_filename: Name of resource filename.
        :return: True if resource_filename should be included.
        """
        return not resource_filename.endswith('_header_info.txt')

    def _read_resource_metadata(self):
        super(NetcdfResourceMeta, self)._read_resource_metadata()

        print("--- NetcdfResourceMeta ---")

        # Also parse using SAX so that we can capture certain metadata elements
        # in the same order in which they appear in the RDF+XML serialization.
        SAX_parse_results = NetcdfResourceSAXHandler()
        defusedxml.sax.parse(self.rmeta_path, SAX_parse_results)

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get Variable
        if SAX_parse_results:
            # Use variables from SAX parser
            self.variables = list(SAX_parse_results.variables)
        else:
            for s, p, o in self._rmeta_graph.triples((None, hsterms.netcdfVariable, None)):
                var = NetcdfResourceMeta.Variable()
                # Get name
                name_lit = self._rmeta_graph.value(o, hsterms.name)
                if name_lit is None:
                    msg = "Name for Variable was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                var.name = str(name_lit)
                # Get shape
                shape_lit = self._rmeta_graph.value(o, hsterms.shape)
                if shape_lit is None:
                    msg = "Shape for Variable was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                var.shape = str(shape_lit)
                # Get type
                type_lit = self._rmeta_graph.value(o, hsterms.type)
                if type_lit is None:
                    msg = "Type for Variable was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                var.type = str(type_lit)
                # Get unit
                unit_lit = self._rmeta_graph.value(o, hsterms.unit)
                if unit_lit is None:
                    msg = "Unit for Variable was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                var.unit = str(unit_lit)
                # Get longName
                long_name_lit = self._rmeta_graph.value(o, hsterms.longName)
                if long_name_lit:
                    var.longName = str(long_name_lit)
                # Get comment
                comment_lit = self._rmeta_graph.value(o, hsterms.comment)
                if comment_lit:
                    var.comment = str(comment_lit)
                # Get missingValue
                missing_val_lit = self._rmeta_graph.value(o, hsterms.missingValue)
                if missing_val_lit:
                    var.missingValue = str(missing_val_lit)
                self.variables.append(var)
        for v in self.variables:
            print("\t\t{0}".format(str(v)))

        # Get spatialReference
        for s, p, o in self._rmeta_graph.triples((None, hsterms.spatialReference, None)):
            # Get extent
            extent_lit = self._rmeta_graph.value(o, hsterms.extent)
            if extent_lit is None:
                msg = "Extent not found in spatial reference for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            extent = str(extent_lit)
            # Get crsName
            crs_name_lit = self._rmeta_graph.value(o, hsterms.crsName)
            crs_name = None
            if crs_name_lit is not None:
                crs_name = str(crs_name_lit)
            # Get crsRepresentationText
            crs_repr_text_lit = self._rmeta_graph.value(o, hsterms.crsRepresentationText)
            crs_repr_text = None
            if crs_repr_text_lit is not None:
                crs_repr_text = str(crs_repr_text_lit)
            # Get crsRepresentationType
            crs_repr_type_lit = self._rmeta_graph.value(o, hsterms.crsRepresentationType)
            crs_repr_type = None
            if crs_repr_type_lit is not None:
                crs_repr_type = str(crs_repr_type_lit)
            self.spatial_reference = NetcdfResourceMeta.SpatialReference(extent, crs_name, crs_repr_text,
                                                                         crs_repr_type)
            print("\t\t{0}".format(self.spatial_reference))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: NetcdfResource instance
        """
        super(NetcdfResourceMeta, self).write_metadata_to_resource(resource)

        if self.spatial_reference:
            resource.metadata.ori_coverage.all().delete()
            values = {'units': self.spatial_reference.unit,
                      'northlimit': self.spatial_reference.northlimit,
                      'eastlimit': self.spatial_reference.eastlimit,
                      'southlimit': self.spatial_reference.southlimit,
                      'westlimit': self.spatial_reference.westlimit,
                      'projection': self.spatial_reference.crsName}
            resource.metadata.create_element('originalcoverage', value=values,
                                             projection_string_type=self.spatial_reference.crsRepresentationType,
                                             projection_string_text=self.spatial_reference.crsRepresentationText)
        if len(self.variables) > 0:
            resource.metadata.variables.all().delete()
            for v in self.variables:
                resource.metadata.create_element('variable', name=v.name,
                                                 shape=v.shape, type=v.type,
                                                 unit=v.unit,
                                                 descriptive_name=v.longName,
                                                 method=v.comment,
                                                 missing_value=v.missingValue)

    class Variable(object):

        def __init__(self):
            self.name = None
            self.shape = None
            self.type = None
            self.unit = None
            self.longName = None  # Optional
            self.comment = None  # Optional
            self.missingValue = None  # Optional

        def __str__(self):
            msg = "Variable name: {name}, unit: {unit}, type: {type}, "
            msg += "shape: {shape}, longName: {longName}, comment: {comment}, "
            msg += "missingValue: {missingValue}"
            msg = msg.format(name=self.name, unit=self.unit, type=self.type, shape=self.shape,
                             longName=self.longName, comment=self.comment,
                             missingValue=self.missingValue)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class SpatialReference(object):

        EXTENT_ELEM = {'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'unit'}
        EXTENT_ELEM_SEP = ';'
        EXTENT_VAL_SEP = '='

        def __init__(self):
            self.northlimit = None
            self.eastlimit = None
            self.southlimit = None
            self.westlimit = None
            self.unit = None
            self.crsName = None
            self.crsRepresentationText = None
            self.crsRepresentationType = None

        def __init__(self, extent, crsName, crsRepresentationText, crsRepresentationType):
            # Parse extent into limits and unit
            extent_elem = extent.split(self.EXTENT_ELEM_SEP)
            if len(extent_elem) != len(self.EXTENT_ELEM):
                msg = "Extent {0} does not have the required number of elements ({1}).".format(extent,
                                                                                               len(self.EXTENT_ELEM))
                raise GenericResourceMeta.ResourceMetaException(msg)
            for e in extent_elem:
                kvp = e.strip()
                k, v = kvp.split(self.EXTENT_VAL_SEP)
                if k not in self.EXTENT_ELEM:
                    msg = "Extent element {0} is not valid.  Entire extent was {1}.".format(k,
                                                                                            extent)
                setattr(self, k, v)

            self.crsName = crsName
            self.crsRepresentationText = crsRepresentationText
            self.crsRepresentationType = crsRepresentationType

        def __str__(self):
            msg = "SpatialReference northlimit: {northlimit}, "
            msg += "eastlimit: {eastlimit}, southlimit: {southlimit}, "
            msg += "westlimit: {westlimit}, unit: {unit}, "
            msg += "crsName: {crsName}, crsRepresentationText: {crsRepresentationText}, "
            msg += "crsRepresentationType: {crsRepresentationType}"
            msg = msg.format(northlimit=self.northlimit, eastlimit=self.eastlimit,
                             southlimit=self.southlimit, westlimit=self.westlimit,
                             unit=self.unit, crsName=self.crsName,
                             crsRepresentationText=self.crsRepresentationText,
                             crsRepresentationType=self.crsRepresentationType)
            return msg

        def __unicode__(self):
            return unicode(str(self))


class NetcdfResourceSAXHandler(defusedxml.sax.ContentHandler):
    def __init__(self):
        defusedxml.sax.ContentHandler.__init__(self)

        # Content
        self.variables = []

        # State variables
        self._get_var = False
        self._get_var_details = False
        self._get_var_name = False
        self._var_name = None
        self._get_var_shape = False
        self._var_shape = None
        self._get_var_long_name = False
        self._var_long_name = None
        self._get_var_missing_val = False
        self._var_missing_val = None
        self._get_var_type = False
        self._var_type = None
        self._get_var_comment = False
        self._var_comment = None
        self._get_var_unit = False
        self._var_unit = None

    def characters(self, content):
        if self._get_var_name:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable name."
                raise defusedxml.sax.SAXException(msg)
            self._var_name.append(content)

        elif self._get_var_shape:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable shape."
                raise defusedxml.sax.SAXException(msg)
            self._var_shape.append(content)

        elif self._get_var_long_name:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable long name."
                raise defusedxml.sax.SAXException(msg)
            self._var_long_name.append(content)

        elif self._get_var_missing_val:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable missing value."
                raise defusedxml.sax.SAXException(msg)
            self._var_missing_val.append(content)

        elif self._get_var_type:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable type."
                raise defusedxml.sax.SAXException(msg)
            self._var_type.append(content)

        elif self._get_var_comment:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable comment."
                raise defusedxml.sax.SAXException(msg)
            self._var_comment.append(content)

        elif self._get_var_unit:
            if len(self.variables) < 1:
                msg = "Error: haven't yet encountered variables, "
                msg += "yet trying to store variable unit."
                raise defusedxml.sax.SAXException(msg)
            self._var_unit.append(content)

    def startElement(self, name, attrs):
        if name == 'hsterms:netcdfVariable':
            if self._get_var:
                raise defusedxml.sax.SAXException("Error: nested hsterms:netcdfVariable elements.")
            self._get_var = True

        elif name == 'rdf:Description':
            if self._get_var:
                if self._get_var_details:
                    msg = "Error: nested rdf:Description elements within hsterms:netcdfVariable element."
                    raise defusedxml.sax.SAXException(msg)
                # Create new variable
                self.variables.append(NetcdfResourceMeta.Variable())
                self._get_var_details = True

        elif name == 'hsterms:name':
            if self._get_var_details:
                if self._get_var_name:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:name elements within hsterms:netcdfVariable.")
                self._get_var_name = True
                self._var_name = []

        elif name == 'hsterms:shape':
            if self._get_var_details:
                if self._get_var_shape:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:shape elements within hsterms:netcdfVariable.")
                self._get_var_shape = True
                self._var_shape = []

        elif name == 'hsterms:longName':
            if self._get_var_details:
                if self._get_var_long_name:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:longName elements within hsterms:netcdfVariable.")
                self._get_var_long_name = True
                self._var_long_name = []

        elif name == 'hsterms:missingValue':
            if self._get_var_details:
                if self._get_var_missing_val:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:missingValue elements within hsterms:netcdfVariable.")
                self._get_var_missing_val = True
                self._var_missing_val = []

        elif name == 'hsterms:type':
            if self._get_var_details:
                if self._get_var_type:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:type elements within hsterms:netcdfVariable.")
                self._get_var_type = True
                self._var_type = []

        elif name == 'hsterms:comment':
            if self._get_var_details:
                if self._get_var_comment:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:comment elements within hsterms:netcdfVariable.")
                self._get_var_comment = True
                self._var_comment = []

        elif name == 'hsterms:unit':
            if self._get_var_details:
                if self._get_var_unit:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:unit elements within hsterms:netcdfVariable.")
                self._get_var_unit = True
                self._var_unit = []

    def endElement(self, name):
        if name == 'hsterms:netcdfVariable':
            if not self._get_var:
                msg = "Error: close hsterms:netcdfVariable tag without corresponding open tag."
                raise defusedxml.sax.SAXException(msg)
            self._get_var = False

        elif name == 'rdf:Description':
            if self._get_var:
                if not self._get_var_details:
                    msg = "Error: close rdf:Description tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self._get_var_details = False

        elif name == 'hsterms:name':
            if self._get_var_details:
                if not self._get_var_name:
                    msg = "Error: close hsterms:name tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].name = "".join(self._var_name)
                self._var_name = None
                self._get_var_name = False

        elif name == 'hsterms:shape':
            if self._get_var_details:
                if not self._get_var_shape:
                    msg = "Error: close hsterms:shape tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].shape = "".join(self._var_shape)
                self._var_shape = None
                self._get_var_shape = False

        elif name == 'hsterms:longName':
            if self._get_var_details:
                if not self._get_var_long_name:
                    msg = "Error: close hsterms:longName tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].longName = "".join(self._var_long_name)
                self._var_long_name = None
                self._get_var_long_name = False

        elif name == 'hsterms:missingValue':
            if self._get_var_details:
                if not self._get_var_missing_val:
                    msg = "Error: close hsterms:missingValue tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].missingValue = "".join(self._var_missing_val)
                self._var_missing_val = None
                self._get_var_missing_val = False

        elif name == 'hsterms:type':
            if self._get_var_details:
                if not self._get_var_type:
                    msg = "Error: close hsterms:type tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].type = "".join(self._var_type)
                self._var_type = None
                self._get_var_type = False

        elif name == 'hsterms:comment':
            if self._get_var_details:
                if not self._get_var_comment:
                    msg = "Error: close hsterms:comment tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].comment = "".join(self._var_comment)
                self._var_comment = None
                self._get_var_comment = False

        elif name == 'hsterms:unit':
            if self._get_var_details:
                if not self._get_var_unit:
                    msg = "Error: close hsterms:unit tag without corresponding open tag "
                    msg += "within hsterms:netcdfVariable."
                    raise defusedxml.sax.SAXException(msg)
                self.variables[-1].unit = "".join(self._var_unit)
                self._var_unit = None
                self._get_var_unit = False

