import os
import logging
import shutil

from osgeo import ogr, osr

from django.core.exceptions import ValidationError
from django.db import models

from hs_core.hydroshare import utils

from hs_geographic_feature_resource.models import GeographicFeatureMetaDataMixin, \
    OriginalCoverage, GeometryInformation, OriginalFileInfo, FieldInformation

from base import AbstractFileMetaData, AbstractLogicalFile

UNKNOWN_STR = "unknown"


class GeoFeatureFileMetaData(GeographicFeatureMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the geographic feature resource type app
    model_app_label = 'hs_geographic_feature_resource'

    def get_metadata_elements(self):
        elements = super(GeoFeatureFileMetaData, self).get_metadata_elements()
        elements += [self.originalcoverage, self.geometryinformation, self.originalfileinfo]
        elements += list(self.fieldinformations.all())
        return elements

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(GeoFeatureFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverage'] = OriginalCoverage
        metadata_model_classes['geometryinformation'] = GeometryInformation
        metadata_model_classes['originalfileinfo'] = OriginalFileInfo
        metadata_model_classes['fieldinformation'] = FieldInformation
        return metadata_model_classes


class GeoFeatureLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoFeatureFileMetaData, related_name="logical_file")
    data_type = "Geo feature data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .zip or .shp file can be set to this logical file group"""
        # See Shapefile format:
        # http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs")

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are the followings"""
        return [".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs"
                ]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        feature_metadata = GeoFeatureFileMetaData.objects.create()
        return cls.objects.create(metadata=feature_metadata)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_add(self):
        """doesn't allow a resource file to be added"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False

    @classmethod
    def set_file_type(cls, resource, file_id, user):
        """
            Sets a tif or zip raster resource file to GeoRasterFile type
            :param resource: an instance of resource type CompositeResource
            :param file_id: id of the resource file to be set as GeoRasterFile type
            :param user: user who is setting the file type
            :return:
            """

        # had to import it here to avoid import loop
        from hs_core.views.utils import create_folder

        log = logging.getLogger()

        # get the file from irods
        res_file = utils.get_resource_file_by_id(resource, file_id)

        if res_file is None:
            raise ValidationError("File not found.")

        if res_file.extension not in ('.zip', '.shp'):
            raise ValidationError("Not a valid geographic feature file.")

        if not res_file.has_generic_logical_file:
            raise ValidationError("Selected file must be generic file type.")

        if res_file.extension == '.shp':
            # check that the shp file is not at the root level
            if not res_file.file_folder:
                raise ValidationError("Selected shape file must be at the root level.")
            # get the names of all files where res_file exists
            shape_files = []
            shp_res_files = []
            for f in resource.files.all():
                if f.file_folder == res_file.file_folder:
                    shape_files.append(f.file_name)
                    shp_res_files.append(f)
            if not check_if_shape_files(shape_files):
                err_msg = "One or more dependent shape files are missing at location: " \
                          "{folder_path} or one or more files are of not shape file type."
                err_msg = err_msg.format(res_file.short_path)
                raise ValidationError(err_msg)
            # base file name (no path included)
            file_name = res_file.file_name
            # file name without the extension
            base_file_name = file_name.split(".")[0]
            # copy the needed shape files from irods to django to the same temp dir
            temp_dir = ''
            temp_shp_files = []
            for f in shp_res_files:
                temp_file = utils.get_file_from_irods(f)
                if not temp_dir:
                    temp_dir = os.path.dirname(temp_file)
                else:
                    file_temp_dir = os.path.dirname(temp_file)
                    dst_dir = os.path.join(temp_dir, os.path.basename(temp_file))
                    shutil.copy(temp_file, dst_dir)
                    shutil.rmtree(file_temp_dir)
                    temp_file = dst_dir
                temp_shp_files.append(temp_file)
                # TODO: need to figure out the best way to call the parse_shp_zshp()
                # parse_shp_zshp(uploadedFileType='shp', baseFilename=base_file_name,
                #                uploadedFileCount=len(temp_shp_files),  )
        else:
            # TODO:
            # process zip file
            pass




def check_if_shape_files(files):
    """
    checks if the list of file names in *files* are part of shape files
    must have one of these file extensions: (shp, shx, dbf)
    :param files: list of file name
    :return: True/False
    """
    # Note: this is the original function (check_fn_for_shp) in geo feature resource receivers.py
    # used by is_shapefiles

    shp, shx, dbf = False, False, False
    all_have_same_filename = False
    shp_filename, shx_filename, dbf_filename = None, None, None
    dir_count = 0  # can have 0 or 1 folder
    if len(files) >= 3:  # at least have 3 mandatory files: shp, shx, dbf
        for f in files:
            if f.endswith('/'):
                dir_count += 1
            else:
                fullName = f[f.rfind('/')+1:]
                fileName, fileExtension = os.path.splitext(fullName.lower())
                if fileExtension not in GeoFeatureLogicalFile.get_allowed_storage_file_types():
                    return False
                elif ".shp" == fileExtension:
                    shp_filename = fileName
                    if not shp:
                        shp = True
                    else:
                        return False
                elif ".shx" == fileExtension:
                    shx_filename = fileName
                    if not shx:
                        shx = True
                    else:
                        return False
                elif ".dbf" == fileExtension:
                    dbf_filename = fileName
                    if not dbf:
                        dbf = True
                    else:
                        return False

        if shp_filename == shx_filename and shp_filename == dbf_filename:
            all_have_same_filename = True

    if shp and shx and dbf and all_have_same_filename and (dir_count <= 1):
        return True
    else:
        return False


def parse_shp_zshp(uploadedFileType, baseFilename,
                   uploadedFileCount, uploadedFilenameString, shpFullPath):
    try:
        metadata_array = []
        metadata_dict = {}

        # fileTypeInfo_dict
        originalFileInfo_dict = {}
        originalFileInfo_dict["fileType"] = "SHP" if uploadedFileType == "shp" else "ZSHP"
        originalFileInfo_dict["baseFilename"] = baseFilename
        originalFileInfo_dict["fileCount"] = uploadedFileCount
        originalFileInfo_dict["filenameString"] = uploadedFilenameString
        metadata_array.append({"OriginalFileInfo": originalFileInfo_dict})
        metadata_dict["originalfileinfo"] = originalFileInfo_dict

        # wgs84 extent
        parsed_md_dict = parse_shp(shpFullPath)
        if parsed_md_dict["wgs84_extent_dict"]["westlimit"] != UNKNOWN_STR:
            wgs84_dict = parsed_md_dict["wgs84_extent_dict"]
            # if extent is a point, create point type coverage
            if wgs84_dict["westlimit"] == wgs84_dict["eastlimit"] \
               and wgs84_dict["northlimit"] == wgs84_dict["southlimit"]:
                coverage_dict = {"Coverage": {"type": "point",
                                 "value": {"east": wgs84_dict["eastlimit"],
                                           "north": wgs84_dict["northlimit"],
                                           "units": wgs84_dict["units"],
                                           "projection": wgs84_dict["projection"]}
                                }}
            else:  # otherwise, create box type coverage
                coverage_dict = {"Coverage": {"type": "box",
                                              "value": parsed_md_dict["wgs84_extent_dict"]}}
            metadata_array.append(coverage_dict)
            metadata_dict["coverage"] = coverage_dict

        # original extent
        original_coverage_dict = {}
        original_coverage_dict["originalcoverage"] = {"northlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["northlimit"],
                                                      "southlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["southlimit"],
                                                      "westlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["westlimit"],
                                                      "eastlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["eastlimit"],
                                                      "projection_string":
                                                      parsed_md_dict
                                                      ["origin_projection_string"],
                                                      "projection_name":
                                                      parsed_md_dict["origin_projection_name"],
                                                      "datum": parsed_md_dict["origin_datum"],
                                                      "unit": parsed_md_dict["origin_unit"]
                                                      }
        metadata_array.append(original_coverage_dict)
        metadata_dict["originalcoverage"] = original_coverage_dict

        # field
        field_info_array = []
        field_name_list = parsed_md_dict["field_meta_dict"]['field_list']
        for field_name in field_name_list:
            field_info_dict_item = {}
            field_info_dict_item['fieldinformation'] = \
                parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
            field_info_array.append(field_info_dict_item)
        metadata_array.extend(field_info_array)
        metadata_dict['field_info_array'] = field_info_array

        # geometry
        geometryinformation = {"featureCount": parsed_md_dict["feature_count"],
                               "geometryType": parsed_md_dict["geometry_type"]}
        metadata_array.append({"geometryinformation": geometryinformation})
        metadata_dict["geometryinformation"] = geometryinformation
        return metadata_array, metadata_dict
    except:
        raise Exception("Parse Shapefiles Failed!")


def parse_shp(shp_file_path):
    """
    :param shp_file_path: full file path fo the .shp file

    output dictionary format
    shp_metadata_dict["origin_projection_string"]: original projection string
    shp_metadata_dict["origin_projection_name"]: origin_projection_name
    shp_metadata_dict["origin_datum"]: origin_datum
    shp_metadata_dict["origin_unit"]: origin_unit
    shp_metadata_dict["field_meta_dict"]["field_list"]: list [fieldname1, fieldname2...]
    shp_metadata_dict["field_meta_dict"]["field_attr_dic"]:
       dict {"fieldname": dict {
                             "fieldName":fieldName,
                             "fieldTypeCode":fieldTypeCode,
                             "fieldType":fieldType,
                             "fieldWidth:fieldWidth,
                             "fieldPrecision:fieldPrecision"
                              }
             }
    shp_metadata_dict["feature_count"]: feature count
    shp_metadata_dict["geometry_type"]: geometry_type
    shp_metadata_dict["origin_extent_dict"]:
    dict{"west": east, "north":north, "east":east, "south":south}
    shp_metadata_dict["wgs84_extent_dict"]:
    dict{"west": east, "north":north, "east":east, "south":south}
    """

    shp_metadata_dict = {}
    # read shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(shp_file_path)

    # get layer
    layer = dataset.GetLayer()
    # get spatialRef from layer
    spatialRef_from_layer = layer.GetSpatialRef()

    if spatialRef_from_layer is not None:
        shp_metadata_dict["origin_projection_string"] = str(spatialRef_from_layer)
        prj_name = spatialRef_from_layer.GetAttrValue('projcs')
        if prj_name is None:
            prj_name = spatialRef_from_layer.GetAttrValue('geogcs')
        shp_metadata_dict["origin_projection_name"] = prj_name

        shp_metadata_dict["origin_datum"] = spatialRef_from_layer.GetAttrValue('datum')
        shp_metadata_dict["origin_unit"] = spatialRef_from_layer.GetAttrValue('unit')
    else:
        shp_metadata_dict["origin_projection_string"] = UNKNOWN_STR
        shp_metadata_dict["origin_projection_name"] = UNKNOWN_STR
        shp_metadata_dict["origin_datum"] = UNKNOWN_STR
        shp_metadata_dict["origin_unit"] = UNKNOWN_STR

    field_list = []
    filed_attr_dic = {}
    field_meta_dict = {"field_list": field_list, "field_attr_dict": filed_attr_dic}
    shp_metadata_dict["field_meta_dict"] = field_meta_dict
    # get Attributes
    layerDefinition = layer.GetLayerDefn()
    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        field_list.append(fieldName)
        attr_dict = {}
        field_meta_dict["field_attr_dict"][fieldName] = attr_dict

        attr_dict["fieldName"] = fieldName
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        attr_dict["fieldTypeCode"] = fieldTypeCode
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        attr_dict["fieldType"] = fieldType
        fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
        attr_dict["fieldWidth"] = fieldWidth
        fieldPrecision = layerDefinition.GetFieldDefn(i).GetPrecision()
        attr_dict["fieldPrecision"] = fieldPrecision

    # get layer extent
    layer_extent = layer.GetExtent()

    # get feature count
    featureCount = layer.GetFeatureCount()
    shp_metadata_dict["feature_count"] = featureCount

    # get a feature from layer
    feature = layer.GetNextFeature()

    # get geometry from feature
    geom = feature.GetGeometryRef()

    # get geometry name
    shp_metadata_dict["geometry_type"] = geom.GetGeometryName()

    # reproject layer extent
    # source SpatialReference
    source = spatialRef_from_layer
    # target SpatialReference
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    # create two key points from layer extent
    left_upper_point = ogr.Geometry(ogr.wkbPoint)
    left_upper_point.AddPoint(layer_extent[0], layer_extent[3])  # left-upper
    right_lower_point = ogr.Geometry(ogr.wkbPoint)
    right_lower_point.AddPoint(layer_extent[1], layer_extent[2])  # right-lower

    # source map always has extent, even projection is unknown
    shp_metadata_dict["origin_extent_dict"] = {}
    shp_metadata_dict["origin_extent_dict"]["westlimit"] = layer_extent[0]
    shp_metadata_dict["origin_extent_dict"]["northlimit"] = layer_extent[3]
    shp_metadata_dict["origin_extent_dict"]["eastlimit"] = layer_extent[1]
    shp_metadata_dict["origin_extent_dict"]["southlimit"] = layer_extent[2]

    # reproject to WGS84
    shp_metadata_dict["wgs84_extent_dict"] = {}

    if source is not None:
        # define CoordinateTransformation obj
        transform = osr.CoordinateTransformation(source, target)
        # project two key points
        left_upper_point.Transform(transform)
        right_lower_point.Transform(transform)
        shp_metadata_dict["wgs84_extent_dict"]["westlimit"] = left_upper_point.GetX()
        shp_metadata_dict["wgs84_extent_dict"]["northlimit"] = left_upper_point.GetY()
        shp_metadata_dict["wgs84_extent_dict"]["eastlimit"] = right_lower_point.GetX()
        shp_metadata_dict["wgs84_extent_dict"]["southlimit"] = right_lower_point.GetY()
        shp_metadata_dict["wgs84_extent_dict"]["projection"] = "WGS 84 EPSG:4326"
        shp_metadata_dict["wgs84_extent_dict"]["units"] = "Decimal degrees"
    else:
        shp_metadata_dict["wgs84_extent_dict"]["westlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["northlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["eastlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["southlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["projection"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["units"] = UNKNOWN_STR

    return shp_metadata_dict
