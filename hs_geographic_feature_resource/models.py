from lxml import etree

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from mezzanine.pages.page_processors import processor_for

from dominate.tags import legend, table, tbody, tr, td, th, h4, div

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement

from hs_core.hydroshare.utils import add_metadata_element_to_xml


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

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="col-xs-6 col-sm-6", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Spatial Reference')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('Coordinate Reference System')
                        td(self.projection_name)
                    with tr():
                        get_th('Datum')
                        td(self.datum)
                    with tr():
                        get_th('Coordinate String Text')
                        td(self.projection_string)
            h4('Extent')
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

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        NAMESPACES = CoreMetaData.NAMESPACES
        cov = etree.SubElement(container, '{%s}spatialReference' % NAMESPACES['hsterms'])
        cov_term = '{%s}' + 'box'
        coverage_terms = etree.SubElement(cov, cov_term % NAMESPACES['hsterms'])
        rdf_coverage_value = etree.SubElement(coverage_terms,
                                              '{%s}value' % NAMESPACES['rdf'])
        # original coverage is of box type
        cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                    % (self.northlimit, self.eastlimit,
                       self.southlimit, self.westlimit,
                       self.unit)

        if self.projection_name:
            cov_value += '; projection_name={}'.format(self.projection_name)

        if self.projection_string:
            cov_value += '; projection_string={}'.format(self.projection_string)

        if self.datum:
            cov_value += '; datum={}'.format(self.datum)

        rdf_coverage_value.text = cov_value


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

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        # element attribute name : name in xml
        md_fields = {
            "fieldName": "fieldName",
            "fieldType": "fieldType",
            "fieldTypeCode": "fieldTypeCode",
            "fieldWidth": "fieldWidth",
            "fieldPrecision": "fieldPrecision"
        }
        add_metadata_element_to_xml(container, self, md_fields)


class GeometryInformation(AbstractMetaDataElement):
    term = 'GeometryInformation'

    featureCount = models.IntegerField(null=False, blank=False, default=0)
    geometryType = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        # GeometryInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="col-xs-12 col-sm-12", style="margin-bottom:40px;")

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

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        # element attribute name : name in xml
        md_fields = {
            "geometryType": "geometryType",
            "featureCount": "featureCount"
        }

        add_metadata_element_to_xml(container, self, md_fields)


# TODO Deprecated
class GeographicFeatureResource(BaseResource):
    objects = ResourceManager("GeographicFeatureResource")

    @property
    def metadata(self):
        md = GeographicFeatureMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):

        # See Shapefile format:
        # http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs")

    def has_required_content_files(self):
        if self.files.all().count < 3:
            return False
        file_extensions = [f.extension for f in self.files.all()]
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

    def get_xml(self, pretty_print=True, include_format_elements=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(GeographicFeatureMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.geometryinformation:
            self.geometryinformation.add_to_xml_container(container)

        for field_info in self.fieldinformations.all():
            field_info.add_to_xml_container(container)

        if self.originalcoverage:
            self.originalcoverage.add_to_xml_container(container)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)
