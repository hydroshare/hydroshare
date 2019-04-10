import json
from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for

from dominate.tags import legend, table, tbody, tr, td, th, h4, div, strong

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement
from hs_core.hydroshare.utils import add_metadata_element_to_xml, \
    get_resource_file_name_and_extension


# extended metadata for raster resource type to store the original box type coverage
# since the core metadata coverage stores the converted WGS84 geographic coordinate
# system projection coverage, see issue #210 on github for details
class OriginalCoverage(AbstractMetaDataElement):
    term = 'OriginalCoverage'

    """
    _value field stores a json string as shown below for box coverage type
     _value = "{'northlimit':northenmost coordinate value,
                'eastlimit':easternmost coordinate value,
                'southlimit':southernmost coordinate value,
                'westlimit':westernmost coordinate value,
                'units:units applying to 4 limits (north, east, south & east),
                'projection': name of the projection (optional),
                'projection_string: OGC WKT string of the projection (optional),
                'datum: projection datum name (optional),
                }"
    """
    _value = models.CharField(max_length=10000, null=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def value(self):
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        """
        The '_value' subelement needs special processing. (Check if the 'value' includes the
        required info and convert 'value' dict as Json string to be the '_value' subelement value.)
        The base class create() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary

        """

        value_arg_dict = None
        if 'value' in kwargs:
            value_arg_dict = kwargs['value']
        elif '_value' in kwargs:
            value_arg_dict = json.loads(kwargs['_value'])

        if value_arg_dict:
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if value_item not in value_arg_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more "
                                          "bounding box limits or 'units' is missing.")

            value_dict = {k: v for k, v in value_arg_dict.iteritems()
                          if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit',
                                   'projection', 'projection_string', 'datum')}

            value_json = json.dumps(value_dict)
            if 'value' in kwargs:
                del kwargs['value']
            kwargs['_value'] = value_json
            return super(OriginalCoverage, cls).create(**kwargs)
        else:
            raise ValidationError('Coverage value is missing.')

    @classmethod
    def update(cls, element_id, **kwargs):
        """
        The '_value' subelement needs special processing.
        (Convert the 'value' dict as Json string to be the "_value" subelement value.)
        The base class update() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
        """

        cov = OriginalCoverage.objects.get(id=element_id)

        if 'value' in kwargs:
            value_dict = cov.value

            for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit',
                              'projection', 'projection_string', 'datum'):
                if item_name in kwargs['value']:
                    value_dict[item_name] = kwargs['value'][item_name]

            value_json = json.dumps(value_dict)
            del kwargs['value']
            kwargs['_value'] = value_json
            super(OriginalCoverage, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Coverage element can't be deleted.")

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        NAMESPACES = CoreMetaData.NAMESPACES
        cov = etree.SubElement(container, '{%s}spatialReference' % NAMESPACES['hsterms'])
        cov_term = '{%s}' + 'box'
        coverage_terms = etree.SubElement(cov, cov_term % NAMESPACES['hsterms'])
        rdf_coverage_value = etree.SubElement(coverage_terms,
                                              '{%s}value' % NAMESPACES['rdf'])
        # raster original coverage is of box type
        cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                    % (self.value['northlimit'], self.value['eastlimit'],
                       self.value['southlimit'], self.value['westlimit'],
                       self.value['units'])

        for meta_element in self.value:
            if meta_element == 'projection':
                cov_value += '; projection_name={}'.format(self.value[meta_element])
            if meta_element in ['projection_string', 'datum']:
                cov_value += '; {}={}'.format(meta_element, self.value[meta_element])

        rdf_coverage_value.text = cov_value

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for an instance of this metadata element so
        that this element can be edited"""

        from .forms import OriginalCoverageSpatialForm

        ori_coverage_data_dict = {}
        if element is not None:
            ori_coverage_data_dict['projection'] = element.value.get('projection', None)
            ori_coverage_data_dict['datum'] = element.value.get('datum', None)
            ori_coverage_data_dict['projection_string'] = element.value.get('projection_string',
                                                                            None)
            ori_coverage_data_dict['units'] = element.value['units']
            ori_coverage_data_dict['northlimit'] = element.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = element.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = element.value['southlimit']
            ori_coverage_data_dict['westlimit'] = element.value['westlimit']

        originalcov_form = OriginalCoverageSpatialForm(
            initial=ori_coverage_data_dict, allow_edit=allow_edit,
            res_short_id=resource.short_id if resource else None,
            element_id=element.id if element else None, file_type=file_type)

        return originalcov_form

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="content-block")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Spatial Reference')
            div('Coordinate Reference System', cls='text-muted space-top')
            div(self.value.get('projection', ''))
            div('Coordinate Reference System Unit', cls='text-muted space-top')
            div(self.value['units'])
            div('Datum', cls='text-muted space-top')
            div(self.value.get('datum', ''))
            div('Coordinate String', cls='text-muted space-top')
            div(self.value.get('projection_string', ''), style="word-break: break-all;")
            h4('Extent', cls='space-top')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('North')
                        td(self.value['northlimit'])
                    with tr():
                        get_th('West')
                        td(self.value['westlimit'])
                    with tr():
                        get_th('South')
                        td(self.value['southlimit'])
                    with tr():
                        get_th('East')
                        td(self.value['eastlimit'])

        return root_div.render(pretty=pretty)


class BandInformation(AbstractMetaDataElement):
    term = 'BandInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by
    # the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    name = models.CharField(max_length=500, null=True)
    variableName = models.TextField(max_length=100, null=True)
    variableUnit = models.CharField(max_length=50, null=True)

    # optional fields
    method = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    noDataValue = models.TextField(null=True, blank=True)
    maximumValue = models.TextField(null=True, blank=True)
    minimumValue = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("BandInformation element of the raster resource cannot be deleted.")

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of this metadata element"""

        bandinfo_fields = ['name', 'variableName', 'variableUnit', 'noDataValue',
                           'maximumValue', 'minimumValue',
                           'method', 'comment']
        add_metadata_element_to_xml(container, self, bandinfo_fields)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div()

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Variable Name')
                            td(self.variableName)
                        with tr():
                            get_th('Variable Unit')
                            td(self.variableUnit)
                        if self.noDataValue:
                            with tr():
                                get_th('No Data Value')
                                td(self.noDataValue)
                        if self.maximumValue:
                            with tr():
                                get_th('Maximum Value')
                                td(self.maximumValue)
                        if self.minimumValue:
                            with tr():
                                get_th('Minimum Value')
                                td(self.minimumValue)
                        if self.method:
                            with tr():
                                get_th('Method')
                                td(self.method)
                        if self.comment:
                            with tr():
                                get_th('Comment')
                                td(self.comment)

        return root_div.render(pretty=pretty)


class CellInformation(AbstractMetaDataElement):
    term = 'CellInformation'
    # required fields
    name = models.CharField(max_length=500, null=True)
    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellDataType = models.CharField(max_length=50, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        # CellInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CellInformation element of a raster resource cannot be removed")

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of this metadata element"""

        cellinfo_fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue',
                           'cellDataType']
        add_metadata_element_to_xml(container, self, cellinfo_fields)

    def get_html_form(self, resource):
        """Generates html form code for this metadata element so that this element can be edited"""

        from .forms import CellInfoForm
        cellinfo_form = CellInfoForm(instance=self,
                                     res_short_id=resource.short_id if resource else None,
                                     element_id=self.id if self else None)
        return cellinfo_form

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="content-block")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Cell Information')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('Rows')
                        td(self.rows)
                    with tr():
                        get_th('Columns')
                        td(self.columns)
                    with tr():
                        get_th('Cell Size X Value')
                        td(self.cellSizeXValue)
                    with tr():
                        get_th('Cell Size Y Value')
                        td(self.cellSizeYValue)
                    with tr():
                        get_th('Cell Data Type')
                        td(self.cellDataType)

        return root_div.render(pretty=pretty)


# TODO Deprecated
# To create a new resource, use these two super-classes.
class RasterResource(BaseResource):
    objects = ResourceManager("RasterResource")

    discovery_content_type = 'Geographic Raster'  # used during discovery

    class Meta:
        verbose_name = 'Geographic Raster'
        proxy = True

    @classmethod
    def get_metadata_class(cls):
        return RasterMetaData

    @classmethod
    def get_supported_upload_file_types(cls):
        # only tif file type is supported
        return (".tiff", ".tif", ".vrt", ".zip")

    @classmethod
    def allow_multiple_file_upload(cls):
        # can upload multiple files
        return True

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False

    # add resource-specific HS terms
    def get_hs_term_dict(self):
        # get existing hs_term_dict from base class
        hs_term_dict = super(RasterResource, self).get_hs_term_dict()
        # add new terms for Raster res
        hs_term_dict["HS_FILE_NAME"] = ""
        for res_file in self.files.all():
            _, f_fullname, f_ext = get_resource_file_name_and_extension(res_file)
            if f_ext.lower() == '.vrt':
                hs_term_dict["HS_FILE_NAME"] = f_fullname
                break
        return hs_term_dict

# this would allow us to pick up additional form elements for the template
# before the template is displayed via Mezzanine page processor
processor_for(RasterResource)(resource_processor)


class GeoRasterMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""

    # required non-repeatable cell information metadata elements
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)

    class Meta:
        abstract = True

    @property
    def cellInformation(self):
        return self._cell_information.all().first()

    @property
    def bandInformations(self):
        return self._band_information.all()

    @property
    def originalCoverage(self):
        return self._ori_coverage.all().first()

    def has_all_required_elements(self):
        if not super(GeoRasterMetaDataMixin, self).has_all_required_elements():
            return False
        if not self.cellInformation:
            return False
        if self.bandInformations.count() == 0:
            return False
        if not self.coverages.all().filter(type='box').first():
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(GeoRasterMetaDataMixin,
                                          self).get_required_missing_elements()
        if not self.coverages.all().filter(type='box').first():
            missing_required_elements.append('Spatial Coverage')
        if not self.cellInformation:
            missing_required_elements.append('Cell Information')
        if not self.bandInformations:
            missing_required_elements.append('Band Information')

        return missing_required_elements

    def delete_all_elements(self):
        super(GeoRasterMetaDataMixin, self).delete_all_elements()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()
        self.bandInformations.delete()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeoRasterMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        return elements


class RasterMetaData(GeoRasterMetaDataMixin, CoreMetaData):

    @property
    def resource(self):
        return RasterResource.objects.filter(object_id=self.id).first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import GeoRasterMetaDataSerializer
        return GeoRasterMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()

        if 'bandinformations' in keys_to_update:
            for bandinformation in metadata.pop('bandinformations'):
                parsed_metadata.append({"bandinformation": bandinformation})

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata

        from forms import BandInfoValidationForm
        # update any core metadata
        super(RasterMetaData, self).update(metadata, user)
        # update resource specific metadata
        # for geo raster resource type only band information can be updated
        missing_file_msg = "Resource specific metadata can't be updated when there is no " \
                           "content files"

        # update repeatable element (BandInformation)
        for dict_item in metadata:
            if 'bandinformation' in dict_item:
                if not self.resource.files.all():
                    raise ValidationError(missing_file_msg)
                bandinfo_data = dict_item['bandinformation']
                if 'original_band_name' not in bandinfo_data:
                    raise ValidationError("Invalid band information data")
                # find the matching (lookup by name) bandinformation element to update
                band_element = self.bandInformations.filter(
                    name=bandinfo_data['original_band_name']).first()
                if band_element is None:
                    raise ValidationError("No matching band information element was found")

                bandinfo_data.pop('original_band_name')
                if 'name' not in bandinfo_data:
                    bandinfo_data['name'] = band_element.name
                if 'variableName' not in bandinfo_data:
                    bandinfo_data['variableName'] = band_element.variableName
                if 'variableUnit' not in bandinfo_data:
                    bandinfo_data['variableUnit'] = band_element.variableUnit
                validation_form = BandInfoValidationForm(bandinfo_data)
                if not validation_form.is_valid():
                    err_string = self.get_form_errors_as_string(validation_form)
                    raise ValidationError(err_string)
                self.update_element('bandinformation', band_element.id, **bandinfo_data)

    def get_xml(self, pretty_print=True, include_format_elements=True):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(RasterMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject raster resource specific metadata elements to container element
        if self.cellInformation:
            self.cellInformation.add_to_xml_container(container)

        for band_info in self.bandInformations:
            band_info.add_to_xml_container(container)

        if self.originalCoverage:
            self.originalCoverage.add_to_xml_container(container)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)
