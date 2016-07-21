import defusedxml.sax

import rdflib

from django.db import transaction

from hs_core.serialization import GenericResourceMeta

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage


class RasterResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of RasterResource instances.
    """
    def __init__(self):
        super(RasterResourceMeta, self).__init__()

        self.cell_info = None
        self.band_info = []
        self.spatial_reference = None

    def _read_resource_metadata(self):
        super(RasterResourceMeta, self)._read_resource_metadata()

        print("--- RasterResourceMeta ---")

        # Also parse using SAX so that we can capture certain metadata elements
        # in the same order in which they appear in the RDF+XML serialization.
        SAX_parse_results = RasterResourceSAXHandler()
        defusedxml.sax.parse(self.rmeta_path, SAX_parse_results)

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get CellInformation
        for s, p, o in self._rmeta_graph.triples((None, hsterms.CellInformation, None)):
            self.cell_info = RasterResourceMeta.CellInformation()
            # Get name
            name_lit = self._rmeta_graph.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for CellInformation was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.name = str(name_lit)
            # Get rows
            rows_lit = self._rmeta_graph.value(o, hsterms.rows)
            if rows_lit is None:
                msg = "Rows attribute was not found for CellInformation for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.rows = int(str(rows_lit))
            # Get columns
            columns_lit = self._rmeta_graph.value(o, hsterms.columns)
            if columns_lit is None:
                msg = "Columns attribute was not found for CellInformation for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.columns = int(str(columns_lit))
            # Get cellSizeXValue
            cellX_lit = self._rmeta_graph.value(o, hsterms.cellSizeXValue)
            if cellX_lit is None:
                msg = "cellSizeXValue attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellSizeXValue = float(str(cellX_lit))
            # Get cellSizeYValue
            cellY_lit = self._rmeta_graph.value(o, hsterms.cellSizeYValue)
            if cellY_lit is None:
                msg = "cellSizeYValue attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellSizeYValue = float(str(cellY_lit))
            # Get cellDataType
            celldt_lit = self._rmeta_graph.value(o, hsterms.cellDataType)
            if celldt_lit is None:
                msg = "cellDataType attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellDataType = str(celldt_lit)
            # Get noDateValue
            nodata_lit = self._rmeta_graph.value(o, hsterms.noDataValue)
            if nodata_lit is not None:
                self.cell_info.noDataValue = float(str(nodata_lit))
            print("\t\t{0}".format(self.cell_info))

        # Get BandInformation
        if SAX_parse_results:
            # Use band info from SAX parser
            self.band_info = list(SAX_parse_results.band_info)
        else:
            # Get band info from RDF
            for s, p, o in self._rmeta_graph.triples((None, hsterms.BandInformation, None)):
                band_info = RasterResourceMeta.BandInformation()
                # Get name
                name_lit = self._rmeta_graph.value(o, hsterms.name)
                if name_lit is None:
                    msg = "Name for BandInformation was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                band_info.name = str(name_lit)
                # Get variableName
                varname_lit = self._rmeta_graph.value(o, hsterms.variableName)
                if varname_lit is None:
                    msg = "variableName for BandInformation was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                band_info.variableName = str(varname_lit)
                # Get variableUnit
                varunit_lit = self._rmeta_graph.value(o, hsterms.variableUnit)
                if varunit_lit is None:
                    msg = "variableUnit for BandInformation was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                band_info.variableUnit = str(varunit_lit)
                # Get method
                method_lit = self._rmeta_graph.value(o, hsterms.method)
                if method_lit is not None:
                    band_info.method = str(method_lit)
                # Get comment
                comment_lit = self._rmeta_graph.value(o, hsterms.comment)
                if comment_lit is not None:
                    band_info.comment = str(comment_lit)
                self.band_info.append(band_info)
        for b in self.band_info:
            print("\t\t{0}".format(str(b)))

        # Get spatialReference
        for s, p, o in self._rmeta_graph.triples((None, hsterms.spatialReference, None)):
            spat_ref_lit = self._rmeta_graph.value(o, rdflib.namespace.RDF.value)
            if spat_ref_lit is None:
                msg = "Spatial reference value not found for {0}.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.spatial_reference = RasterResourceMeta.SpatialReference(str(spat_ref_lit))
            print("\t\t{0}".format(self.spatial_reference))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: RasterResource instance
        """
        super(RasterResourceMeta, self).write_metadata_to_resource(resource)

        if self.cell_info:
            resource.metadata.cellInformation.delete()
            resource.metadata.create_element('CellInformation', name=self.cell_info.name,
                                             rows=self.cell_info.rows, columns=self.cell_info.columns,
                                             cellSizeXValue=self.cell_info.cellSizeXValue,
                                             cellSizeYValue=self.cell_info.cellSizeYValue,
                                             cellDataType=self.cell_info.cellDataType,
                                             noDataValue=self.cell_info.noDataValue)
        if len(self.band_info) > 0:
            for band in resource.metadata.bandInformation:
                band.delete()
            for b in self.band_info:
                resource.metadata.create_element('BandInformation', name=b.name, variableName=b.variableName,
                                                 variableUnit=b.variableUnit, method=b.method, comment=b.comment)
        if self.spatial_reference:
            resource.metadata.originalCoverage.delete()
            values = {'units': self.spatial_reference.units,
                      'northlimit': self.spatial_reference.northlimit,
                      'eastlimit': self.spatial_reference.eastlimit,
                      'southlimit': self.spatial_reference.southlimit,
                      'westlimit': self.spatial_reference.westlimit,
                      'projection': self.spatial_reference.projection}
            kwargs = {'value': values}
            resource.metadata.create_element('OriginalCoverage', **kwargs)

    class CellInformation(object):

        def __init__(self):
            self.name = None
            self.rows = None
            self.columns = None
            self.cellSizeXValue = None
            self.cellSizeYValue = None
            self.cellDataType = None
            self.noDataValue = None  # Optional

        def __str__(self):
            msg = "CellInformation name: {name}, "
            msg += "rows: {rows}, columns: {columns}, "
            msg += "cellSizeXValue: {cellSizeXValue}, cellSizeYValue: {cellSizeYValue}, "
            msg += "cellDataType: {cellDataType}, noDataValue: {noDataValue}"
            msg = msg.format(name=self.name, rows=self.rows,
                             columns=self.columns, cellSizeXValue=self.cellSizeXValue,
                             cellSizeYValue=self.cellSizeYValue, cellDataType=self.cellDataType,
                             noDataValue=self.noDataValue)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class BandInformation(object):

        def __init__(self):
            self.name = None
            self.variableName = None
            self.variableUnit = None
            self.method = None  # Optional
            self.comment = None  # Optional

        def __str__(self):
            msg = "BandInformation name: {name}, "
            msg += "variableName: {variableName}, variableUnit: {variableUnit}, "
            msg += "method: {method}, comment: {comment}"
            msg = msg.format(name=self.name, variableName=self.variableName,
                             variableUnit=self.variableUnit, method=self.method,
                             comment=self.comment)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class SpatialReference(object):

        def __init__(self):
            self.northlimit = None
            self.eastlimit = None
            self.southlimit = None
            self.westlimit = None
            self.units = None
            self.projection = None  # Optional

        def __str__(self):
            msg = "SpatialReference northlimit: {northlimit}, "
            msg += "eastlimit: {eastlimit}, southlimit: {southlimit}, "
            msg += "westlimit: {westlimit}, units: {units}, projection: {projection}"
            msg = msg.format(northlimit=self.northlimit, eastlimit=self.eastlimit,
                             southlimit=self.southlimit, westlimit=self.westlimit,
                             units=self.units, projection=self.projection)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, value_str):
            kvp = value_str.split(';')
            for pair in kvp:
                (key, value) = pair.split('=')
                key = key.strip()
                value = value.strip()
                if key == 'name':
                    self.name = value
                elif key == 'eastlimit':
                    try:
                        self.eastlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse east limit {0}, error: {1}".format(value,
                                                                                  str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'northlimit':
                    try:
                        self.northlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse north limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'southlimit':
                    try:
                        self.southlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse south limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'westlimit':
                    try:
                        self.westlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse west limit {0}, error: {1}".format(value,
                                                                                  str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'units':
                    self.units = value
                elif key == 'projection':
                    self.projection = value

class RasterResourceSAXHandler(defusedxml.sax.ContentHandler):
    def __init__(self):
        defusedxml.sax.ContentHandler.__init__(self)

        # Content
        self.band_info = []

        # State variables
        self._get_bandinfo = False
        self._get_bandinfo_details = False
        self._get_bandinfo_name = False
        self._bandinfo_name = None
        self._get_bandinfo_var_name = False
        self._bandinfo_var_name = None
        self._get_bandinfo_var_unit = False
        self._bandinfo_var_unit = None
        self._get_bandinfo_method = False
        self._bandinfo_method = None
        self._get_bandinfo_comment = False
        self._bandinfo_comment = None

    def characters(self, content):
        if self._get_bandinfo_name:
            if len(self.band_info) < 1:
                msg = "Error: haven't yet encountered band information, "
                msg += "yet trying to store band information name."
                raise defusedxml.sax.SAXException(msg)
            self._bandinfo_name.append(content)

        elif self._get_bandinfo_var_name:
            if len(self.band_info) < 1:
                msg = "Error: haven't yet encountered band information, "
                msg += "yet trying to store band information variable name."
                raise defusedxml.sax.SAXException(msg)
            self._bandinfo_var_name.append(content)

        elif self._get_bandinfo_var_unit:
            if len(self.band_info) < 1:
                msg = "Error: haven't yet encountered band information, "
                msg += "yet trying to store band information variable unit."
                raise defusedxml.sax.SAXException(msg)
            self._bandinfo_var_unit.append(content)

        elif self._get_bandinfo_method:
            if len(self.band_info) < 1:
                msg = "Error: haven't yet encountered band information, "
                msg += "yet trying to store band information method."
                raise defusedxml.sax.SAXException(msg)
            self._bandinfo_method.append(content)

        elif self._get_bandinfo_comment:
            if len(self.band_info) < 1:
                msg = "Error: haven't yet encountered band information, "
                msg += "yet trying to store band information comment."
                raise defusedxml.sax.SAXException(msg)
            self._bandinfo_comment.append(content)

    def startElement(self, name, attrs):
        if name == 'hsterms:BandInformation':
            if self._get_bandinfo:
                raise defusedxml.sax.SAXException("Error: nested hsterms:BandInformation elements.")
            self._get_bandinfo = True

        elif name == 'rdf:Description':
            if self._get_bandinfo:
                if self._get_bandinfo_details:
                    msg = "Error: nested rdf:Description elements within hsterms:BandInformation element."
                    raise defusedxml.sax.SAXException(msg)
                # Create new band info
                self.band_info.append(RasterResourceMeta.BandInformation())
                self._get_bandinfo_details = True

        elif name == 'hsterms:name':
            if self._get_bandinfo_details:
                if self._get_bandinfo_name:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:name elements within hsterms:BandInformation.")
                self._get_bandinfo_name = True
                self._bandinfo_name = []

        elif name == 'hsterms:variableName':
            if self._get_bandinfo_details:
                if self._get_bandinfo_var_name:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:variableName elements within hsterms:BandInformation.")
                self._get_bandinfo_var_name = True
                self._bandinfo_var_name = []

        elif name == 'hsterms:variableUnit':
            if self._get_bandinfo_details:
                if self._get_bandinfo_var_unit:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:variableUnit elements within hsterms:BandInformation.")
                self._get_bandinfo_var_unit = True
                self._bandinfo_var_unit = []

        elif name == 'hsterms:method':
            if self._get_bandinfo_details:
                if self._get_bandinfo_method:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:method elements within hsterms:BandInformation.")
                self._get_bandinfo_method = True
                self._bandinfo_method = []

        elif name == 'hsterms:comment':
            if self._get_bandinfo_details:
                if self._get_bandinfo_comment:
                    raise defusedxml.sax.SAXException("Error: nested hsterms:comment elements within hsterms:BandInformation.")
                self._get_bandinfo_comment = True
                self._bandinfo_comment = []

    def endElement(self, name):
        if name == 'hsterms:BandInformation':
            if not self._get_bandinfo:
                msg = "Error: close hsterms:BandInformation tag without corresponding open tag."
                raise defusedxml.sax.SAXException(msg)
            self._get_bandinfo = False

        elif name == 'rdf:Description':
            if self._get_bandinfo:
                if not self._get_bandinfo_details:
                    msg = "Error: close rdf:Description tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self._get_bandinfo_details = False

        elif name == 'hsterms:name':
            if self._get_bandinfo_details:
                if not self._get_bandinfo_name:
                    msg = "Error: close hsterms:name tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self.band_info[-1].name = "".join(self._bandinfo_name)
                self._bandinfo_name = None
                self._get_bandinfo_name = False

        elif name == 'hsterms:variableName':
            if self._get_bandinfo_details:
                if not self._get_bandinfo_var_name:
                    msg = "Error: close hsterms:variableName tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self.band_info[-1].variableName = "".join(self._bandinfo_var_name)
                self._bandinfo_var_name = None
                self._get_bandinfo_var_name = False

        elif name == 'hsterms:variableUnit':
            if self._get_bandinfo_details:
                if not self._get_bandinfo_var_unit:
                    msg = "Error: close hsterms:variableUnit tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self.band_info[-1].variableUnit = "".join(self._bandinfo_var_unit)
                self._bandinfo_var_unit = None
                self._get_bandinfo_var_unit = False

        elif name == 'hsterms:method':
            if self._get_bandinfo_details:
                if not self._get_bandinfo_method:
                    msg = "Error: close hsterms:method tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self.band_info[-1].method = "".join(self._bandinfo_method)
                self._bandinfo_method = None
                self._get_bandinfo_method = False

        elif name == 'hsterms:comment':
            if self._get_bandinfo_details:
                if not self._get_bandinfo_comment:
                    msg = "Error: close hsterms:comment tag without corresponding open tag "
                    msg += "within hsterms:BandInformation."
                    raise defusedxml.sax.SAXException(msg)
                self.band_info[-1].comment = "".join(self._bandinfo_comment)
                self._bandinfo_comment = None
                self._get_bandinfo_comment = False
