import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ga_ows.views import wms, wfs
from ga_resources import models, dispatch
from ga_resources.drivers import shapefile, render, CacheManager
from ga_resources.models import RenderedLayer
from ga_resources.utils import authorize
from matplotlib.finance import md5
from osgeo import osr, ogr

class WMSAdapter(wms.WMSAdapterBase):
    def layerlist(self):
        return [l.slug for l in models.RenderedLayer.objects.all()]

    def get_2d_dataset(self, layers, srs, bbox, width, height, styles, bgcolor, transparent, time, elevation, v, filter,
                       **kwargs):
        """use the driver to render a tile"""
        return render(kwargs['format'], width, height, bbox, srs, styles, layers, **kwargs)

    def get_feature_info(self, wherex, wherey, layers, callback, format, feature_count, srs, filter, fuzziness=0,
                         **kwargs): # fuzziness of 30 meters by default
        """use the driver to get feature info"""

        if srs.lower().startswith('epsg'):
            s = osr.SpatialReference()
            s.ImportFromEPSG(int(srs[5:]))
            srs = s.ExportToProj4()

        feature_info = {
            layer: models.RenderedLayer.objects.get(slug=layer).data_resource.driver_instance.get_data_for_point(
                wherex, wherey, srs, fuzziness=fuzziness, **kwargs
            )
            for layer in layers}

        return feature_info

    def nativesrs(self, layer):
        """Use the resource record to get native SRS"""
        resource = models.RenderedLayer.objects.get(slug=layer).data_resource
        return resource.native_srs

    def nativebbox(self, layer=None):
        """Use the resource record to get the native bounding box"""
        if layer:
            resource = models.RenderedLayer.objects.get(slug=layer).data_resource
            return resource.native_bounding_box.extent
        else:
            return (-180, -90, 180, 90)

    def styles(self):
        """Use the resource record to get the available styles"""
        return list(models.Style.objects.all())

    def get_layer_descriptions(self):
        """
        This should return a list of dictionaries.  Each dictionary should follow this format::
            { ""name"" : layer_"name",
              "title" : human_readable_title,
              "srs" : spatial_reference_id,
              "queryable" : whether or not GetFeatureInfo is supported for this layer,
              "minx" : native_west_boundary,
              "miny" : native_south_boundary,
              "maxx" : native_east_boundary,
              "maxy" : native_north_boundary,
              "ll_minx" : west_boundary_epsg4326,
              "ll_miny" : south_boundary_epsg4326,
              "ll_maxx" : east_boundary_epsg4326,
              "ll_maxy" : north_boundary_epsg4326,
              "styles" : [list_of_style_descriptions]

        Each style description in list_of_style_descriptions should follow this format::
            { ""name"" : style_"name",
              "title" : style_title,
              "legend_width" : style_legend_width,
              "legend_height" : style_legend_height,
              "legend_url" : style_legend_url
            }
        """
        layers = models.RenderedLayer.objects.all()
        ret = []
        for layer in layers:
            desc = {}
            ret.append(desc)
            desc["name"] = layer.slug
            desc['title'] = layer.title
            desc['srs'] = layer.data_resource.native_srs
            desc['queryable'] = True
            desc['minx'], desc['miny'], desc['maxx'], desc[
                'maxy'] = layer.data_resource.native_bounding_box.extent  # FIXME this is not native
            desc['ll_minx'], desc['ll_miny'], desc['ll_maxx'], desc[
                'll_maxy'] = layer.data_resource.bounding_box.extent
            desc['styles'] = []
            desc['styles'].append({
                "name": layer.default_style.slug,
                'title': layer.default_style.title,
                'legend_width': layer.default_style.legend_width,
                'legend_height': layer.default_style.legend_height,
                'legend_url': layer.default_style.legend.url if layer.default_style.legend else ""
            })
            for style in layer.styles.all():
                desc['styles'].append({
                    "name": style.slug,
                    'title': style.title,
                    'legend_width': style.legend_width,
                    'legend_height': style.legend_height,
                    'legend_url': style.legend.url if style.legend else ""
                })
        return ret


    def get_service_boundaries(self):
        """Just go ahead and return the world coordinates"""

        return {
            "minx": -180.0,
            "miny": -90.0,
            "maxx": 180.0,
            "maxy": 90.0
        }

class WMS(wms.WMS):
    adapter = WMSAdapter([])


class WFSAdapter(wfs.WFSAdapter):
    def get_feature_descriptions(self, request, *types):
        namespace = request.build_absolute_uri().split('?')[
                        0] + "/schema" # todo: include https://bitbucket.org/eegg/django-model-schemas/wiki/Home

        for type_name in types:
            res = get_object_or_404(models.DataResource, slug=type_name)

            yield wfs.FeatureDescription(
                ns=namespace,
                ns_name='ga_resources',
                name=res.slug,
                abstract=res.description,
                title=res.title,
                keywords=res.keywords,
                srs=res.native_srs,
                bbox=res.bounding_box,
                schema=namespace + '/' + res.slug
            )

    def list_stored_queries(self, request):
        """list all the queries associated with drivers"""
        sq = super(WFSAdapter, self).list_stored_queries(request)
        return sq

    def get_features(self, request, parms):
        if parms.cleaned_data['stored_query_id']:
            squid = "SQ_" + parms.cleaned_data['stored_query_id']
            slug = parms.cleaned_data['type_names'] if isinstance(parms.cleaned_data['type_names'], basestring) else \
                parms.cleaned_data['type_names'][0]
            try:
                return models.DataResource.driver_instance.query_operation(squid)(request, **parms.cleaned_data)
            except:
                raise wfs.OperationNotSupported.at('GetFeatures', 'stored_query_id={squid}'.format(squid=squid))
        else:
            return self.AdHocQuery(request, **parms.cleaned_data)

    def AdHocQuery(self, req,
                   type_names=None,
                   filter=None,
                   filter_language=None,
                   bbox=None,
                   sort_by=None,
                   count=None,
                   start_index=None,
                   srs_name=None,
                   srs_format=None,
                   max_features=None,
                   **kwargs
    ):
        model = get_object_or_404(models.DataResource, slug=type_names[0])
        driver = model.driver_instance

        extra = {}
        if filter:
            extra['filter'] = json.loads(filter)

        if bbox:
            extra['bbox'] = bbox

        if srs_name:
            srs = osr.SpatialReference()
            if srs_name.lower().startswith('epsg'):
                srs.ImportFromEPSG(int(srs_name[5:]))
            else:
                srs.ImportFromProj4(srs_name)
            extra['srs'] = srs
        else:
            srs = model.srs

        if start_index:
            extra['start'] = start_index

        count = count or max_features
        if count:
            extra['count'] = count

        if "boundary" in kwargs:
            extra['boundary'] = kwargs['boundary']
            extra['boundary_type'] = kwargs['boundary_type']

        df = driver.as_dataframe(**extra)

        if sort_by:
            extra['sort_by'] = sort_by

        if filter_language and filter_language != 'json':
            raise wfs.OperationNotSupported('filter language must be JSON for now')

        filename = md5()

        filename.update("{name}.{bbox}.{srs_name}x{filter}".format(
            name=type_names[0],
            bbox=','.join(str(b) for b in bbox),
            srs_name=srs_name,
            filter=filter
        ))
        filename = filename.hexdigest()
        shapefile.ShapefileDriver.from_dataframe(df, filename, srs)
        ds = ogr.Open(filename)
        return ds

    def supports_feature_versioning(self):
        return False


class WFS(wfs.WFS):
    adapter = WFSAdapter()


def tms(request, layer, z, x, y, **kwargs):
    z = int(z)
    x = int(x)
    y = int(y)

    table = None
    if '#' in layer:
        layer_slug, table = layer.split('#')
    else:
        layer_slug = layer
    layer_instance = RenderedLayer.objects.get(slug=layer_slug)

    user = authorize(request, page=layer, view=True)
    dispatch.api_accessed.send(RenderedLayer, instance=layer_instance, user=user)
    style = request.GET.get('styles', layer_instance.default_style.slug)
    tms = CacheManager.get().get_tile_cache([layer], [style])
    return HttpResponse(tms.fetch_tile(z, x, y), mimetype='image/png')

def seed_layer(request, layer):
    mnz = int(request.GET['minz'])
    mxz = int(request.GET['maxz']) # anything greater would cause a DOS attack.  We should do it manually
    mnx = int(request.GET['minx'])
    mxx = int(request.GET['maxx'])
    mny = int(request.GET['miny'])
    mxy = int(request.GET['maxy'])

    layer = RenderedLayer.objects.get(slug=layer)
    style = request.GET.get('style', layer.default_style)

    user = authorize(request, page=layer, edit=True)
    dispatch.api_accessed.send(RenderedLayer, instance=layer, user=user)
    CacheManager.get().get_tile_cache(layers=[layer], styles=[style]).seed_tiles(mnz, mxz, mnx, mny, mxx, mxy)
    return HttpResponse()
