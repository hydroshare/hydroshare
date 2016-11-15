import os
import xmltodict
import re
from osgeo import ogr, osr
try:
    #  Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    #  Python 3
    from html.parser import HTMLParser

from hs_core.models import Title


UNKNOWN_STR = "unknown"


def parse_shp(file_path):
    # output dictionary format
    # shp_metadata_dict["origin_projection_string"]: original projection string
    # shp_metadata_dict["origin_projection_name"]: origin_projection_name
    # shp_metadata_dict["origin_datum"]: origin_datum
    # shp_metadata_dict["origin_unit"]: origin_unit
    # shp_metadata_dict["field_meta_dict"]["field_list"]: list [fieldname1, fieldname2...]
    # shp_metadata_dict["field_meta_dict"]["field_attr_dic"]:
    #   dict {"fieldname": dict {
    #                         "fieldName":fieldName,
    #                         "fieldTypeCode":fieldTypeCode,
    #                         "fieldType":fieldType,
    #                         "fieldWidth:fieldWidth,
    #                         "fieldPrecision:fieldPrecision"
    #                          }
    #         }
    # shp_metadata_dict["feature_count"]: feature count
    # shp_metadata_dict["geometry_type"]: geometry_type
    # shp_metadata_dict["origin_extent_dict"]:
    # dict{"west": east, "north":north, "east":east, "south":south}
    # shp_metadata_dict["wgs84_extent_dict"]:
    # dict{"west": east, "north":north, "east":east, "south":south}

    shp_metadata_dict = {}
    # read shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(file_path)

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


def parse_shp_xml(shp_xml_full_path):
    """
    Parse ArcGIS 10.X ESRI Shapefile Metadata XML.
    :param shp_xml_full_path: Expected fullpath to the .shp.xml file
    :return: a list of metadata dict
    """
    metadata = []

    try:
        if os.path.isfile(shp_xml_full_path):
            with open(shp_xml_full_path) as fd:
                xml_dict = xmltodict.parse(fd.read())
                if 'metadata' in xml_dict:
                    if 'dataIdInfo' in xml_dict['metadata']:
                        dataIdInfo_dict = xml_dict['metadata']['dataIdInfo']
                        if 'idCitation' in dataIdInfo_dict:
                            if 'resTitle' in dataIdInfo_dict['idCitation']:
                                if '#text' in dataIdInfo_dict['idCitation']['resTitle']:
                                    title_value = dataIdInfo_dict['idCitation']['resTitle']['#text']
                                else:
                                    title_value = dataIdInfo_dict['idCitation']['resTitle']

                                title_max_length = Title._meta.get_field('value').max_length
                                if len(title_value) > title_max_length:
                                    title_value = title_value[:title_max_length-1]
                                title = {'title': {'value': title_value}}
                                metadata.append(title)

                        if 'idAbs' in dataIdInfo_dict:
                            description_value = clean_text(dataIdInfo_dict['idAbs'])
                            description = {'description': {'abstract': description_value}}
                            metadata.append(description)

                        if 'searchKeys' in dataIdInfo_dict:
                            searchKeys_dict = dataIdInfo_dict['searchKeys']
                            if 'keyword' in searchKeys_dict:
                                keyword_list = []
                                if type(searchKeys_dict["keyword"]) is list:
                                    keyword_list += searchKeys_dict["keyword"]
                                else:
                                    keyword_list.append(searchKeys_dict["keyword"])
                                for k in keyword_list:
                                    metadata.append({'subject': {'value': k}})

    except Exception:
        # Catch any exception silently and return an empty list
        # Due to the variant format of ESRI Shapefile Metadata XML
        # among different ArcGIS versions, an empty list will be returned
        # if any exception occurs
        metadata = []
    finally:
        return metadata


def clean_text(text):
    #  Decode html

    h = HTMLParser()
    return h.unescape(clean_html(text))


def clean_html(raw_html):
    # Remove html tag from raw_html

    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext
