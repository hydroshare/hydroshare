
import rdflib

from hs_core.serialization import GenericResourceMeta


class RasterResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of RasterResource instances.
    """
    cell_info = None
    band_info = None
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
            print("\t\tCellInformation: name {0}".format(self.cell_info.name))
            # Get rows
            rows_lit = self._rmeta_graph.value(o, hsterms.rows)
            if rows_lit is None:
                msg = "Rows attribute was not found for CellInformation for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.rows = int(str(rows_lit))
            print("\t\tCellInformation: rows {0}".format(self.cell_info.rows))
            # Get columns
            columns_lit = self._rmeta_graph.value(o, hsterms.columns)
            if columns_lit is None:
                msg = "Columns attribute was not found for CellInformation for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.columns = int(str(columns_lit))
            print("\t\tCellInformation: columns {0}".format(self.cell_info.columns))
            # Get cellSizeXValue
            cellX_lit = self._rmeta_graph.value(o, hsterms.cellSizeXValue)
            if cellX_lit is None:
                msg = "cellSizeXValue attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellSizeXValue = float(str(cellX_lit))
            print("\t\tCellInformation: cellSizeXValue {0}".format(self.cell_info.cellSizeXValue))
            # Get cellSizeYValue
            cellY_lit = self._rmeta_graph.value(o, hsterms.cellSizeYValue)
            if cellY_lit is None:
                msg = "cellSizeYValue attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellSizeYValue = float(str(cellY_lit))
            print("\t\tCellInformation: cellSizeYValue {0}".format(self.cell_info.cellSizeYValue))
            # Get cellDataType
            celldt_lit = self._rmeta_graph.value(o, hsterms.cellDataType)
            if celldt_lit is None:
                msg = "cellDataType attribute was not found for CellInformation "
                msg += "for resource {0}"
                msg = msg.format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.cell_info.cellDataType = str(celldt_lit)
            print("\t\tCellInformation: cellDataType {0}".format(self.cell_info.cellDataType))
            # Get noDateValue
            nodata_lit = self._rmeta_graph.value(o, hsterms.noDataValue)
            if nodata_lit is not None:
                self.cell_info.noDataValue = float(str(nodata_lit))
                print("\t\tCellInformation: noDataValue {0}".format(self.cell_info.noDataValue))

        # Get BandInformation
        for s, p, o in self._rmeta_graph.triples((None, hsterms.BandInformation, None)):
            self.band_info = RasterResourceMeta.BandInformation()
            # Get name
            name_lit = self._rmeta_graph.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for BandInformation was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.band_info.name = str(name_lit)
            print("\t\tBandInformation: name {0}".format(self.band_info.name))
            # Get variableName
            varname_lit = self._rmeta_graph.value(o, hsterms.variableName)
            if varname_lit is None:
                msg = "variableName for BandInformation was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.band_info.variableName = str(varname_lit)
            print("\t\tBandInformation: variableName {0}".format(self.band_info.variableName))
            # Get variableUnit
            varunit_lit = self._rmeta_graph.value(o, hsterms.variableUnit)
            if varunit_lit is None:
                msg = "variableUnit for BandInformation was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.band_info.variableUnit = str(varunit_lit)
            print("\t\tBandInformation: variableUnit {0}".format(self.band_info.variableUnit))
            # Get method
            method_lit = self._rmeta_graph.value(o, hsterms.method)
            if method_lit is not None:
                self.band_info.method = str(method_lit)
                print("\t\tBandInformation: method {0}".format(self.band_info.method))
            # Get comment
            comment_lit = self._rmeta_graph.value(o, hsterms.comment)
            if comment_lit is not None:
                self.band_info.comment = str(comment_lit)
                print("\t\tBandInformation: comment {0}".format(self.band_info.comment))

        # Get spatialReference
        for s, p, o in self._rmeta_graph.triples((None, hsterms.spatialReference, None)):
            print("Subject: {0}\npred: {1}\nobj: {2}\n".format(s, p, o))
            # coverage_lit = self._rmeta_graph.value(o, rdflib.namespace.RDF.value)
            # if coverage_lit is None:
            #     msg = "Coverage value not found for {0}.".format(o)
            #     raise GenericResourceMeta.ResourceMetaException(msg)
            # coverage = GenericResourceMeta.ResourceCoverageBox(str(coverage_lit))
            # self.coverages.append(coverage)

    def write_metadata_to_resource(self, resource):
        super(RasterResourceMeta, self).write_metadata_to_resource(resource)

    class CellInformation(object):
        name = None
        rows = None
        columns = None
        cellSizeXValue = None
        cellSizeYValue = None
        cellDataType = None
        noDataValue = None  # Optional

    class BandInformation(object):
        name = None
        variableName = None
        variableUnit = None
        method = None  # Optional
        comment = None  # Optional

    class SpatialReference(object):
        northlimit = None
        eastlimit = None
        southlimit = None
        westlimit = None
        units = None
        projection = None  # Optional
