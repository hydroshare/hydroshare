from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from mezzanine.pages.page_processors import processor_for

from dominate.tags import legend, table, tbody, tr, td, th, h4, div
from rdflib import RDF, BNode, Literal

from hs_core.hs_rdf import HSTERMS, rdf_terms
from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement


@rdf_terms(HSTERMS.spatialReference)
class OriginalCoverage(AbstractMetaDataElement):
    term = 'OriginalCoverage'

    northlimit = models.FloatField(null=False, blank=False)
    southlimit = models.FloatField(null=False, blank=False)
    westlimit = models.FloatField(null=False, blank=False)
    eastlimit = models.FloatField(null=False, blank=False)
    projection_string = models.TextField(null=True, blank=True)
    projection_name = models.TextField(max_length=256, null=True, blank=True)
    datum = models.TextField(max_length=256, null=True, blank=True)
    unit = models.TextField(max_length=256, null=True, blank=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, cov in graph.triples((subject, cls.get_class_term(), None)):
            value = graph.value(subject=cov, predicate=RDF.value)
            value_dict = {}
            for key_value in value.split(";"):
                key_value = key_value.strip()
                k, v = key_value.split("=")
                if k == 'units':
                    value_dict['unit'] = v
                else:
                    value_dict[k] = v
            OriginalCoverage.create(**value_dict, content_object=content_object)

    def rdf_triples(self, subject, graph):
        coverage = BNode()
        graph.add((subject, self.get_class_term(), coverage))
        graph.add((coverage, RDF.type, HSTERMS.box))
        value_dict = {}
        value_dict['northlimit'] = self.northlimit
        value_dict['southlimit'] = self.southlimit
        value_dict['westlimit'] = self.westlimit
        value_dict['eastlimit'] = self.eastlimit
        value_dict['projection_string'] = self.projection_string
        value_dict['projection_name'] = self.projection_name
        value_dict['datum'] = self.datum
        value_dict['units'] = self.unit
        value_string = "; ".join(["=".join([key, str(val)]) for key, val in value_dict.items()])
        graph.add((coverage, RDF.value, Literal(value_string)))

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="content-block")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Spatial Reference')
            div('Coordinate Reference System', cls='text-muted')
            div(self.projection_name)
            div('Datum', cls='text-muted space-top')
            div(self.datum)
            div('Coordinate String Text', cls='text-muted space-top')
            div(self.projection_string)
            h4('Extent', cls='space-top')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('North')
                        td(self.northlimit)
                    with tr():
                        get_th('West')
                        td(self.westlimit)
                    with tr():
                        get_th('South')
                        td(self.southlimit)
                    with tr():
                        get_th('East')
                        td(self.eastlimit)
                    with tr():
                        get_th('Unit')
                        td(self.unit)

        return root_div.render(pretty=pretty)

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for an instance of this metadata element so
        that this element can be edited"""

        from .forms import OriginalCoverageForm

        ori_cov_dict = {}
        if element is not None:
            ori_cov_dict['northlimit'] = element.northlimit
            ori_cov_dict['eastlimit'] = element.eastlimit
            ori_cov_dict['southlimit'] = element.southlimit
            ori_cov_dict['westlimit'] = element.westlimit
            ori_cov_dict['projection_string'] = element.projection_string
            ori_cov_dict['projection_name'] = element.projection_name
            ori_cov_dict['datum'] = element.datum
            ori_cov_dict['unit'] = element.unit

        orig_coverage_form = OriginalCoverageForm(initial=ori_cov_dict,
                                                  res_short_id=resource.short_id if
                                                  resource else None,
                                                  allow_edit=allow_edit,
                                                  element_id=element.id if element else None,
                                                  file_type=file_type)
        return orig_coverage_form


class FieldInformation(AbstractMetaDataElement):
    term = 'FieldInformation'

    fieldName = models.CharField(max_length=128, null=False, blank=False)
    fieldType = models.CharField(max_length=128, null=False, blank=False)
    fieldTypeCode = models.CharField(max_length=50, null=True, blank=True)
    fieldWidth = models.IntegerField(null=True, blank=True)
    fieldPrecision = models.IntegerField(null=True, blank=True)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        field_infor_tr = tr(cls='row')
        with field_infor_tr:
            td(self.fieldName)
            td(self.fieldType)
            td(self.fieldWidth)
            td(self.fieldPrecision)
        if pretty:
            return field_infor_tr.render(pretty=pretty)
        return field_infor_tr


class GeometryInformation(AbstractMetaDataElement):
    term = 'GeometryInformation'

    featureCount = models.IntegerField(null=False, blank=False, default=0)
    geometryType = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        # GeometryInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="content-block", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Geometry Information')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('Geometry Type')
                        td(self.geometryType)
                    with tr():
                        get_th('Feature Count')
                        td(self.featureCount)
        return root_div.render(pretty=pretty)

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for an instance of this metadata element so
        that this element can be edited"""

        from .forms import GeometryInformationForm

        geom_info_data_dict = {}
        if element is not None:
            geom_info_data_dict['geometryType'] = element.geometryType
            geom_info_data_dict['featureCount'] = element.featureCount

        geom_information_form = GeometryInformationForm(initial=geom_info_data_dict,
                                                        res_short_id=resource.short_id if
                                                        resource else None,
                                                        allow_edit=allow_edit,
                                                        element_id=element.id if element else None,
                                                        file_type=file_type)
        return geom_information_form


# TODO Deprecated
class GeographicFeatureResource(BaseResource):
    objects = ResourceManager("GeographicFeatureResource")

    @classmethod
    def get_metadata_class(cls):
        return GeographicFeatureMetaData

    @classmethod
    def get_supported_upload_file_types(cls):

        # See Shapefile format:
        # http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs")

    def has_required_content_files(self):
        if self.files.all().count() < 3:
            return False
        file_extensions = [f.extension.lower() for f in self.files.all()]
        return all(ext in file_extensions for ext in ['.shp', '.shx', '.dbf'])

    def get_hs_term_dict(self):
        # get existing hs_term_dict from base class
        hs_term_dict = super(GeographicFeatureResource, self).get_hs_term_dict()
        geometryinformation = self.metadata.geometryinformation
        if geometryinformation is not None:
            hs_term_dict["HS_GFR_FEATURE_COUNT"] = geometryinformation.featureCount
        else:
            hs_term_dict["HS_GFR_FEATURE_COUNT"] = 0
        return hs_term_dict

    discovery_content_type = 'Geographic Feature (ESRI Shapefiles)'  # used during discovery

    class Meta:
        verbose_name = 'Geographic Feature (ESRI Shapefiles)'
        proxy = True


processor_for(GeographicFeatureResource)(resource_processor)


class GeographicFeatureMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""
    geometryinformations = GenericRelation(GeometryInformation)
    fieldinformations = GenericRelation(FieldInformation)
    originalcoverages = GenericRelation(OriginalCoverage)

    class Meta:
        abstract = True

    @property
    def geometryinformation(self):
        return self.geometryinformations.all().first()

    @property
    def originalcoverage(self):
        return self.originalcoverages.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeographicFeatureMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('FieldInformation')
        elements.append('OriginalCoverage')
        elements.append('GeometryInformation')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(GeographicFeatureMetaDataMixin, self). \
            get_required_missing_elements()
        if not (self.coverages.all().filter(type='box').first() or
                self.coverages.all().filter(type='point').first()):
            missing_required_elements.append('Spatial Coverage')
        if not self.originalcoverage:
            missing_required_elements.append('Spatial Reference')
        if not self.geometryinformation:
            missing_required_elements.append('Geometry Information')

        return missing_required_elements

    def delete_all_elements(self):
        super(GeographicFeatureMetaDataMixin, self).delete_all_elements()
        self.reset()

    def reset(self):
        """
        This helper method should be used to reset metadata when essential files are removed
        from the resource
        :return:
        """
        self.geometryinformations.all().delete()
        self.fieldinformations.all().delete()
        self.originalcoverages.all().delete()


class GeographicFeatureMetaData(GeographicFeatureMetaDataMixin, CoreMetaData):
    @property
    def resource(self):
        return GeographicFeatureResource.objects.filter(object_id=self.id).first()
