
import rdflib

from hs_core.serialization import GenericResourceMeta


class NetcdfResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of NetcdfResource instances.
    """
    def __init__(self):
        super(NetcdfResourceMeta, self).__init__()

        self.variables = []
        self.spatial_reference = None

    def _read_resource_metadata(self):
        super(NetcdfResourceMeta, self)._read_resource_metadata()

        print("--- NetcdfResourceMeta ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get Variable
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
            print("\t\t{0}".format(var))
            self.variables.append(var)

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
            if crs_name_lit is None:
                msg = "crsName not found in spatial reference for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            crs_name = str(crs_name_lit)
            # Get crsRepresentationText
            crs_repr_text_lit = self._rmeta_graph.value(o, hsterms.crsRepresentationText)
            if crs_repr_text_lit is None:
                msg = "crsRepresentationText not found in spatial reference for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            crs_repr_text = str(crs_repr_text_lit)
            # Get crsRepresentationType
            crs_repr_type_lit = self._rmeta_graph.value(o, hsterms.crsRepresentationType)
            if crs_repr_type_lit is None:
                msg = "crsRepresentationType not found in spatial reference for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            crs_repr_type = str(crs_repr_type_lit)
            self.spatial_reference = NetcdfResourceMeta.SpatialReference(extent, crs_name, crs_repr_text,
                                                                         crs_repr_type)
            print("\t\t{0}".format(self.spatial_reference))


    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: NetcdfResource instance
        """
        super(NetcdfResourceMeta, self).write_metadata_to_resource(resource)

        if self.spatial_reference:
            resource.metadata.ori_coverage.delete()
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
            for variable in resource.metadata.variables:
                variable.delete()
            for v in self.variables:
                resource.metadata.create_element('variable', name=v.name,
                                                 shape=v.shape, type=v.type,
                                                 unit=v.unit,
                                                 descriptive_name=v.longNmae,
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