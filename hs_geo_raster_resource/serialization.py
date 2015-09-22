
import rdflib

from hs_core.serialization import GenericResourceMeta

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage


class RasterResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of RasterResource instances.
    """
    cell_info = None
    band_info = []
    spatial_reference = None

    def __init__(self):
        super(RasterResourceMeta, self).__init__()

    def _read_resource_metadata(self):
        super(RasterResourceMeta, self)._read_resource_metadata()

        print("--- RasterResourceMeta ---")

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
            print("\t\t{0}".format(band_info))
            self.band_info.append(band_info)

        # Get spatialReference
        for s, p, o in self._rmeta_graph.triples((None, hsterms.spatialReference, None)):
            print("Subject: {0}\npred: {1}\nobj: {2}\n".format(s, p, o))
            spat_ref_lit = self._rmeta_graph.value(o, rdflib.namespace.RDF.value)
            if spat_ref_lit is None:
                msg = "Spatial reference value not found for {0}.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.spatial_reference = RasterResourceMeta.SpatialReference(str(spat_ref_lit))
            print("\t\t{0}".format(self.spatial_reference))

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
            kwargs = {'value': values,
                      'content_object': resource}
            OriginalCoverage.create(**kwargs)

    class CellInformation(object):
        name = None
        rows = None
        columns = None
        cellSizeXValue = None
        cellSizeYValue = None
        cellDataType = None
        noDataValue = None  # Optional

        def __str__(self):
            msg = "CellInformation name: {name}, "
            msg += "rows: {rows}, columns: {columns}, "
            msg += "cellSizeXValue: {cellSizeXValue}, cellSizeYValue: {cellSizeYValue}, "
            msg += "cellDataType: {cellDataType}, noDataValue: {noDataValue}"
            msg = msg.format(name=self.name, rows=self.rows,
                             columns=self.columns, cellSizeXValue=self.cellSizeXValue,
                             cellSizeYValue=self.cellSizeYValue, cellDataType=self.cellDataType,
                             noDataValue=self.noDataValue)
            return msg.format(msg)

        def __unicode__(self):
            return unicode(str(self))

    class BandInformation(object):
        name = None
        variableName = None
        variableUnit = None
        method = None  # Optional
        comment = None  # Optional

        def __str__(self):
            msg = "BandInformation name: {name}, "
            msg += "variableName: {variableName}, variableUnit: {variableUnit}, "
            msg += "method: {method}, comment: {comment}"
            msg = msg.format(name=self.name, variableName=self.variableName,
                             variableUnit=self.variableUnit, method=self.method,
                             comment=self.comment)
            return msg.format(msg)

        def __unicode__(self):
            return unicode(str(self))

    class SpatialReference(object):
        northlimit = None
        eastlimit = None
        southlimit = None
        westlimit = None
        units = None
        projection = None  # Optional

        def __str__(self):
            msg = "SpatialReference northlimit: {northlimit}, "
            msg += "eastlimit: {eastlimit}, southlimit: {southlimit}, "
            msg += "westlimit: {westlimit}, units: {units}, projection: {projection}"
            msg = msg.format(northlimit=self.northlimit, eastlimit=self.eastlimit,
                             southlimit=self.southlimit, westlimit=self.westlimit,
                             units=self.units, projection=self.projection)
            return msg.format(msg)

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
