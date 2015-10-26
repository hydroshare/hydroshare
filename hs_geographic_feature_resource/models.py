from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes import generic

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor,\
                           CoreMetaData, AbstractMetaDataElement

# Create your models here.
class OriginalFileInfo(AbstractMetaDataElement):

    term = 'OriginalFileInfo'

    fileTypeEnum = (
                    (None, 'Unknown'),
                    ("SHP", "ESRI Shapefiles"),
                    ("ZSHP", "Zipped ESRI Shapefiles"),
                    ("KML", "KML"),
                    ("KMZ", "KMZ"),
                    ("GML", "GML"),
                    ("SQLITE", "SQLite")
                   )
    fileType = models.TextField(max_length=128, choices=fileTypeEnum, default=None)
    baseFilename = models.TextField(max_length=256, null=False, blank=False)
    fileCount = models.IntegerField(null=False, blank=False, default=0)
    filenameString = models.TextField(null=True, blank=True)

    class Meta:
        # OriginalFileInfo element is not repeatable
        unique_together = ("content_type", "object_id")

# Define original spatial coverage metadata info
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

class FieldInformation(AbstractMetaDataElement):
    term = 'FieldInformation'

    fieldName = models.CharField(max_length=128, null=False, blank=False)
    fieldType = models.CharField(max_length=128, null=False, blank=False)
    fieldTypeCode = models.CharField(max_length=50, null=True, blank=True)
    fieldWidth = models.IntegerField(null=True, blank=True)
    fieldPrecision = models.IntegerField(null=True, blank=True)

class GeometryInformation(AbstractMetaDataElement):
    term = 'GeometryInformation'

    featureCount = models.IntegerField(null=False, blank=False, default=0)
    geometryType = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        # GeometryInformation element is not repeatable
        unique_together = ("content_type", "object_id")

# Define the Geographic Feature
class GeographicFeatureResource(BaseResource):

    objects = ResourceManager("GeographicFeatureResource")

    @property
    def metadata(self):
        md = GeographicFeatureMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # See Shapefile format: http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj", ".sbx", ".sbn", ".cpg", ".xml", ".fbn", ".fbx", ".ain",
                ".aih", ".atx", ".ixs", ".mxs")

    @classmethod
    def can_have_multiple_files(cls):
        # can have more than one files
        return True

    class Meta:
        verbose_name = 'Geographic Feature (ESRI Shapefiles)'
        proxy = True

processor_for(GeographicFeatureResource)(resource_processor)

# define the GeographicFeatureMetaData metadata
class GeographicFeatureMetaData(CoreMetaData):
    geometryinformation = generic.GenericRelation(GeometryInformation)
    fieldinformation = generic.GenericRelation(FieldInformation)
    originalcoverage = generic.GenericRelation(OriginalCoverage)
    originalfileinfo = generic.GenericRelation(OriginalFileInfo)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeographicFeatureMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('FieldInformation')
        elements.append('OriginalCoverage')
        elements.append('GeometryInformation')
        elements.append('OriginalFileInfo')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements() != "":
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(GeographicFeatureMetaData, self).get_required_missing_elements()
        if not (self.coverages.all().filter(type='box').first() or self.coverages.all().filter(type='point').first()):
            missing_required_elements.append('Spatial Coverage')
        if not self.originalcoverage.all().first():
            missing_required_elements.append('Spatial Reference')
        if not self.geometryinformation.all().first():
            missing_required_elements.append('Geometry Information')
        if not self.originalfileinfo.all().first():
            missing_required_elements.append('Resource File Information')

        return missing_required_elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(GeographicFeatureMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.originalcoverage.all().first():
            hsterms_ori_cov = etree.SubElement(container, '{%s}spatialReference' % self.NAMESPACES['hsterms'])
            hsterms_ori_cov_rdf_Description = etree.SubElement(hsterms_ori_cov, '{%s}Description' % self.NAMESPACES['rdf'])
            ori_cov_obj = self.originalcoverage.all().first()

            # add extent info
            if ori_cov_obj.northlimit:
                cov_box = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s' \
                        %(ori_cov_obj.northlimit, ori_cov_obj.eastlimit,
                          ori_cov_obj.southlimit, ori_cov_obj.westlimit)

                hsterms_ori_cov_box = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}extent' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_box.text = str(cov_box)
            if ori_cov_obj.projection_string:
                hsterms_ori_cov_projection = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}crsRepresentationText' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_projection.text = str(ori_cov_obj.projection_string)

        hsterms_ori_file_info = etree.SubElement(container, '{%s}originalFileInfo' % self.NAMESPACES['hsterms'])
        hsterms_ori_file_info_rdf_Description = etree.SubElement(hsterms_ori_file_info, '{%s}Description' % self.NAMESPACES['rdf'])
        ori_file_info = self.originalfileinfo.all().first()
        if ori_file_info:
            hsterms_ori_file_info_file_type = etree.SubElement(hsterms_ori_file_info_rdf_Description, '{%s}fileType' % self.NAMESPACES['hsterms'])
            hsterms_ori_file_info_file_type.text = str(ori_file_info.fileType)
            hsterms_ori_file_info_file_count = etree.SubElement(hsterms_ori_file_info_rdf_Description, '{%s}fileCount' % self.NAMESPACES['hsterms'])
            hsterms_ori_file_info_file_count.text = str(ori_file_info.fileCount)
            hsterms_ori_file_info_filename_string = etree.SubElement(hsterms_ori_file_info_rdf_Description, '{%s}filenameString' % self.NAMESPACES['hsterms'])
            hsterms_ori_file_info_filename_string.text = str(ori_file_info.filenameString)
            hsterms_ori_file_info_base_filename = etree.SubElement(hsterms_ori_file_info_rdf_Description, '{%s}baseFilename' % self.NAMESPACES['hsterms'])
            hsterms_ori_file_info_base_filename.text = str(ori_file_info.baseFilename)


        hsterms_geom_info = etree.SubElement(container, '{%s}geometryInformation' % self.NAMESPACES['hsterms'])
        hsterms_geom_info_rdf_Description = etree.SubElement(hsterms_geom_info, '{%s}Description' % self.NAMESPACES['rdf'])
        geom_info_obj = self.geometryinformation.all().first()
        if geom_info_obj:
            hsterms_geom_info_geom_type = etree.SubElement(hsterms_geom_info_rdf_Description, '{%s}geometryType' % self.NAMESPACES['hsterms'])
            hsterms_geom_info_geom_type.text = str(geom_info_obj.geometryType)
            hsterms_geom_info_fea_count = etree.SubElement(hsterms_geom_info_rdf_Description, '{%s}featureCount' % self.NAMESPACES['hsterms'])
            hsterms_geom_info_fea_count.text = str(geom_info_obj.featureCount)

        hsterms_field_info = etree.SubElement(container, '{%s}fieldInformation' % self.NAMESPACES['hsterms'])
        field_info_obj_list = self.fieldinformation.all()
        if field_info_obj_list:
            for field in field_info_obj_list:
                hsterms_field_info_rdf_Description = etree.SubElement(hsterms_field_info, '{%s}Description' % self.NAMESPACES['rdf'])
                hsterms_field_info_fieldName = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldName' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldName.text = str(field.fieldName)
                hsterms_field_info_fieldType = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldType' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldType.text = str(field.fieldType)
                hsterms_field_info_fieldTypeCode = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldTypeCode' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldTypeCode.text = str(field.fieldTypeCode)
                hsterms_field_info_fieldWidth = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldWidth' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldWidth.text = str(field.fieldWidth)
                hsterms_field_info_fieldPrecision = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldPrecision' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldPrecision.text = str(field.fieldPrecision)

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers # never delete this otherwise non of the receiver function will work
