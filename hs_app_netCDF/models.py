import json
from lxml import etree

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation

from mezzanine.pages.page_processors import processor_for

from dominate.tags import legend, table, tbody, tr, td, th, h4, div, strong, form, button, input

from hs_core.models import BaseResource, ResourceManager
from hs_core.models import resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare.utils import get_resource_file_name_and_extension, \
    add_metadata_element_to_xml, get_resource_files_by_extension


# Define original spatial coverage metadata info
class OriginalCoverage(AbstractMetaDataElement):
    PRO_STR_TYPES = (
        ('', '---------'),
        ('WKT String', 'WKT String'),
        ('Proj4 String', 'Proj4 String')
    )

    term = 'OriginalCoverage'
    """
    _value field stores a json string. The content of the json as box coverage info
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                    'units:units applying to 4 limits (north, east, south & east),
                    'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024, null=True)
    projection_string_type = models.CharField(max_length=20, choices=PRO_STR_TYPES, null=True)
    projection_string_text = models.TextField(null=True, blank=True)
    datum = models.CharField(max_length=300, blank=True)

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
        required information and convert 'value' dict as Json string to be the '_value'
        subelement value.) The base class create() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
                       the '_value' in kwargs is a serialized json string
        """
        value_arg_dict = None
        if 'value' in kwargs:
            value_arg_dict = kwargs['value']
        elif '_value' in kwargs:
            value_arg_dict = json.loads(kwargs['_value'])

        if value_arg_dict:
            # check that all the required sub-elements exist and create new original coverage meta
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if value_item not in value_arg_dict:
                    raise ValidationError("For original coverage meta, one or more bounding "
                                          "box limits or 'units' is missing.")

            value_dict = {k: v for k, v in value_arg_dict.iteritems()
                          if k in ('units', 'northlimit', 'eastlimit', 'southlimit',
                                   'westlimit', 'projection')}

            cls._validate_bounding_box(value_dict)
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
        The '_value' subelement needs special processing. (Convert 'value' dict as Json string
        to be the '_value' subelement value) and the base class update() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
        """

        ori_cov = OriginalCoverage.objects.get(id=element_id)
        if 'value' in kwargs:
            value_dict = ori_cov.value

            for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit',
                              'westlimit', 'projection'):
                if item_name in kwargs['value']:
                    value_dict[item_name] = kwargs['value'][item_name]

            cls._validate_bounding_box(value_dict)
            value_json = json.dumps(value_dict)
            del kwargs['value']
            kwargs['_value'] = value_json
            super(OriginalCoverage, cls).update(element_id, **kwargs)

    @classmethod
    def _validate_bounding_box(cls, box_dict):
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
            try:
                float(box_dict[limit])
            except ValueError:
                raise ValidationError("Bounding box data is not numeric")

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        NAMESPACES = CoreMetaData.NAMESPACES
        cov = etree.SubElement(container, '{%s}spatialReference' % NAMESPACES['hsterms'])
        cov_term = '{%s}' + 'box'
        coverage_terms = etree.SubElement(cov, cov_term % NAMESPACES['hsterms'])
        rdf_coverage_value = etree.SubElement(coverage_terms,
                                              '{%s}value' % NAMESPACES['rdf'])
        # netcdf original coverage is of box type
        cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                    % (self.value['northlimit'], self.value['eastlimit'],
                       self.value['southlimit'], self.value['westlimit'],
                       self.value['units'])

        for meta_element in self.value:
            if meta_element == 'projection':
                if self.value[meta_element]:
                    cov_value += '; projection_name={}'.format(self.value[meta_element])

        if self.projection_string_text:
            cov_value += '; projection_string={}'.format(self.projection_string_text)

        if self.datum:
            cov_value += '; datum={}'.format(self.datum)

        rdf_coverage_value.text = cov_value

    @classmethod
    def get_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Generates html form code for this metadata element so that this element can be edited"""

        from .forms import OriginalCoverageForm

        ori_coverage_data_dict = dict()
        if element is not None:
            ori_coverage_data_dict['projection'] = element.value.get('projection', None)
            ori_coverage_data_dict['datum'] = element.datum
            ori_coverage_data_dict['projection_string_type'] = element.projection_string_type
            ori_coverage_data_dict['projection_string_text'] = element.projection_string_text
            ori_coverage_data_dict['units'] = element.value['units']
            ori_coverage_data_dict['northlimit'] = element.value['northlimit']
            ori_coverage_data_dict['eastlimit'] = element.value['eastlimit']
            ori_coverage_data_dict['southlimit'] = element.value['southlimit']
            ori_coverage_data_dict['westlimit'] = element.value['westlimit']

        originalcov_form = OriginalCoverageForm(
            initial=ori_coverage_data_dict, allow_edit=allow_edit,
            res_short_id=resource.short_id if resource else None,
            element_id=element.id if element else None, file_type=file_type)

        return originalcov_form

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
                        td(self.value.get('projection', ''))
                    with tr():
                        get_th('Datum')
                        td(self.datum)
                    with tr():
                        get_th('Coordinate String Type')
                        td(self.projection_string_type)
                    with tr():
                        get_th('Coordinate String Text')
                        td(self.projection_string_text)
            h4('Extent')
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
                    with tr():
                        get_th('Unit')
                        td(self.value['units'])

        return root_div.render(pretty=pretty)


# Define netCDF variable metadata
class Variable(AbstractMetaDataElement):
    # variable types are defined in OGC enhanced_data_model_extension_standard
    # left is the given value stored in database right is the value for the drop down list
    VARIABLE_TYPES = (
        ('Char', 'Char'),  # 8-bit byte that contains uninterpreted character data
        ('Byte', 'Byte'),  # integer(8bit)
        ('Short', 'Short'),  # signed integer (16bit)
        ('Int', 'Int'),  # signed integer (32bit)
        ('Float', 'Float'),  # floating point (32bit)
        ('Double', 'Double'),  # floating point(64bit)
        ('Int64', 'Int64'),  # integer(64bit)
        ('Unsigned Byte', 'Unsigned Byte'),
        ('Unsigned Short', 'Unsigned Short'),
        ('Unsigned Int', 'Unsigned Int'),
        ('Unsigned Int64', 'Unsigned Int64'),
        ('String', 'String'),  # variable length character string
        ('User Defined Type', 'User Defined Type'),  # compound, vlen, opaque, enum
        ('Unknown', 'Unknown')
    )
    term = 'Variable'
    # required variable attributes
    name = models.CharField(max_length=1000)
    unit = models.CharField(max_length=1000)
    type = models.CharField(max_length=1000, choices=VARIABLE_TYPES)
    shape = models.CharField(max_length=1000)
    # optional variable attributes
    descriptive_name = models.CharField(max_length=1000, null=True, blank=True,
                                        verbose_name='long name')
    method = models.TextField(null=True, blank=True, verbose_name='comment')
    missing_value = models.CharField(max_length=1000, null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("The variable of the resource can't be deleted.")

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        md_fields = {
            "md_element": "netcdfVariable",
            "name": "name",
            "unit": "unit",
            "type": "type",
            "shape": "shape",
            "descriptive_name": "longName",
            "method": "comment",
            "missing_value": "missingValue"
        }  # element name : name in xml
        add_metadata_element_to_xml(container, self, md_fields)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        root_div = div(cls="col-xs-12 pull-left", style="margin-top:10px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Unit')
                            td(self.unit)
                        with tr():
                            get_th('Type')
                            td(self.type)
                        with tr():
                            get_th('Shape')
                            td(self.shape)
                        if self.descriptive_name:
                            with tr():
                                get_th('Long Name')
                                td(self.descriptive_name)
                        if self.missing_value:
                            with tr():
                                get_th('Missing Value')
                                td(self.missing_value)
                        if self.method:
                            with tr():
                                get_th('Comment')
                                td(self.method)

        return root_div.render(pretty=pretty)


# TODO Deprecated
class NetcdfResource(BaseResource):
    objects = ResourceManager("NetcdfResource")

    @property
    def metadata(self):
        md = NetcdfMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # only file with extension .nc is supported for uploading
        return (".nc",)

    @classmethod
    def allow_multiple_file_upload(cls):
        # can upload only 1 file
        return False

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False

    # add resource-specific HS terms
    def get_hs_term_dict(self):
        # get existing hs_term_dict from base class
        hs_term_dict = super(NetcdfResource, self).get_hs_term_dict()
        # add new terms for NetCDF res
        hs_term_dict["HS_FILE_NAME"] = ""
        for res_file in self.files.all():
            _, f_fullname, f_ext = get_resource_file_name_and_extension(res_file)
            if f_ext.lower() == '.nc':
                hs_term_dict["HS_FILE_NAME"] = f_fullname
                break
        return hs_term_dict

    def update_netcdf_file(self, user):
        if not self.metadata.is_dirty:
            return

        nc_res_file = get_resource_files_by_extension(self, ".nc")
        txt_res_file = get_resource_files_by_extension(self, ".txt")

        from hs_file_types.models.netcdf import netcdf_file_update  # avoid recursive import
        if nc_res_file and txt_res_file:
            netcdf_file_update(self, nc_res_file[0], txt_res_file[0], user)

    discovery_content_type = 'Multidimensional (NetCDF)'  # used during discovery

    class Meta:
        verbose_name = 'Multidimensional (NetCDF)'
        proxy = True

processor_for(NetcdfResource)(resource_processor)


class NetCDFMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""
    variables = GenericRelation(Variable)
    ori_coverage = GenericRelation(OriginalCoverage)

    class Meta:
        abstract = True

    @property
    def originalCoverage(self):
        return self.ori_coverage.all().first()

    def has_all_required_elements(self):
        # checks if all required metadata elements have been created
        if not super(NetCDFMetaDataMixin, self).has_all_required_elements():
            return False
        if not self.variables.all():
            return False
        if not (self.coverages.all().filter(type='box').first() or
                self.coverages.all().filter(type='point').first()):
            return False
        if not self.originalCoverage:
            return False
        return True

    def get_required_missing_elements(self):
        # get a list of missing required metadata element names
        missing_required_elements = super(NetCDFMetaDataMixin, self).get_required_missing_elements()
        if not (self.coverages.all().filter(type='box').first() or
                self.coverages.all().filter(type='point').first()):
            missing_required_elements.append('Spatial Coverage')
        if not self.variables.all().first():
            missing_required_elements.append('Variable')
        if not self.originalCoverage:
            missing_required_elements.append('Spatial Reference')
        return missing_required_elements

    def delete_all_elements(self):
        super(NetCDFMetaDataMixin, self).delete_all_elements()
        self.ori_coverage.all().delete()
        self.variables.all().delete()

    @classmethod
    def get_supported_element_names(cls):
        # get the class names of all supported metadata elements for this resource type
        # or file type
        elements = super(NetCDFMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Variable')
        elements.append('OriginalCoverage')
        return elements


# define the netcdf metadata
class NetcdfMetaData(NetCDFMetaDataMixin, CoreMetaData):
    is_dirty = models.BooleanField(default=False)

    @property
    def resource(self):
        return NetcdfResource.objects.filter(object_id=self.id).first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import NetCDFMetaDataSerializer
        return NetCDFMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'originalcoverage' in keys_to_update:
            parsed_metadata.append({"originalcoverage": metadata.pop('originalcoverage')})

        if 'variables' in keys_to_update:
            for variable in metadata.pop('variables'):
                parsed_metadata.append({"variable": variable})

    def set_dirty(self, flag):
        """
        Overriding the base class method
        """

        if self.resource.files.all():
            self.is_dirty = flag
            self.save()

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from forms import VariableValidationForm, OriginalCoverageValidationForm
        super(NetcdfMetaData, self).update(metadata, user)
        missing_file_msg = "Resource specific metadata can't be updated when there is no " \
                           "content files"
        with transaction.atomic():
            # update/create non-repeatable element (originalcoverage)
            for dict_item in metadata:
                if 'originalcoverage' in dict_item:
                    if not self.resource.files.all():
                        raise ValidationError(missing_file_msg)
                    coverage_data = dict_item['originalcoverage']
                    for key in ('datum', 'projection_string_type', 'projection_string_text'):
                        coverage_data.pop(key, None)
                    if 'value' not in coverage_data:
                        raise ValidationError("Coverage value data is missing")
                    if 'projection' in coverage_data['value']:
                        coverage_data['value'].pop('projection')
                    coverage_value_dict = coverage_data.pop('value')
                    validation_form = OriginalCoverageValidationForm(coverage_value_dict)
                    coverage_data['value'] = coverage_value_dict
                    if not validation_form.is_valid():
                        err_string = self.get_form_errors_as_string(validation_form)
                        raise ValidationError(err_string)
                    if self.originalCoverage:
                        self.update_element('originalcoverage', self.originalCoverage.id,
                                            **coverage_data)
                    else:
                        self.create_element('originalcoverage', **coverage_data)
                    break

            # update repeatable element (variable)
            for dict_item in metadata:
                if 'variable' in dict_item:
                    if not self.resource.files.all():
                        raise ValidationError(missing_file_msg)
                    variable_data = dict_item['variable']
                    if 'name' not in variable_data:
                        raise ValidationError("Invalid variable data")
                    # find the matching (lookup by name) variable element to update
                    var_element = self.variables.filter(name=variable_data['name']).first()
                    if var_element is None:
                        raise ValidationError("No matching variable element was found")
                    for key in ('name', 'type', 'shape'):
                        variable_data.pop(key, None)
                    variable_data['name'] = var_element.name
                    variable_data['type'] = var_element.type
                    variable_data['shape'] = var_element.shape
                    if 'unit' not in variable_data:
                        variable_data['unit'] = var_element.unit
                    validation_form = VariableValidationForm(variable_data)
                    if not validation_form.is_valid():
                        err_string = self.get_form_errors_as_string(validation_form)
                        raise ValidationError(err_string)
                    self.update_element('variable', var_element.id, **variable_data)

        # write updated metadata to netcdf file
        self.resource.update_netcdf_file(user)

    def get_xml(self, pretty_print=True, include_format_elements=True):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(NetcdfMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject netcdf resource specific metadata element 'variable' to container element
        for variable in self.variables.all():
            variable.add_to_xml_container(container)

        ori_cov_obj = self.ori_coverage.all().first()
        if ori_cov_obj is not None:
            ori_cov_obj.add_to_xml_container(container)

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def update_element(self, element_model_name, element_id, **kwargs):
        super(NetcdfMetaData, self).update_element(element_model_name, element_id, **kwargs)
        if self.resource.files.all() and element_model_name in ['variable', 'title', 'description',
                                                                'rights', 'source', 'coverage',
                                                                'relation', 'creator',
                                                                'contributor']:

            if element_model_name != 'relation':
                self.is_dirty = True
            elif kwargs.get('type', None) == 'cites':
                self.is_dirty = True

            self.save()

    def create_element(self, element_model_name, **kwargs):
        element = super(NetcdfMetaData, self).create_element(element_model_name, **kwargs)
        if self.resource.files.all() and element_model_name in ['description', 'subject', 'source',
                                                                'coverage', 'relation', 'creator',
                                                                'contributor']:

            if element_model_name != 'relation':
                self.is_dirty = True
            elif kwargs.get('type', None) == 'cites':
                self.is_dirty = True

            self.save()

        return element

    def delete_element(self, element_model_name, element_id):
        super(NetcdfMetaData, self).delete_element(element_model_name, element_id)
        if self.resource.files.all() and element_model_name in ['source', 'contributor', 'creator',
                                                                'relation']:
            self.is_dirty = True
            self.save()

    def get_update_netcdf_file_html_form(self):
        form_action = "/hsapi/_internal/netcdf_update/{}/".\
            format(self.resource.short_id)
        style = "display:none;"
        if self.is_dirty:
            style = "margin-bottom:10px"
        root_div = div(id="netcdf-file-update", cls="row", style=style)

        with root_div:
            with div(cls="col-sm-12"):
                with div(cls="alert alert-warning alert-dismissible", role="alert"):
                    strong("NetCDF file needs to be synced with metadata changes.")

                    input(id="metadata-dirty", type="hidden", value="{{ cm.metadata.is_dirty }}")
                    with form(action=form_action, method="post", id="update-netcdf-file",):
                        div('{% csrf_token %}')
                        button("Update NetCDF File", type="submit", cls="btn btn-primary",
                               id="id-update-netcdf-file",
                               )

        return root_div
