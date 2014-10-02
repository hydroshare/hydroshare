import json
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from ga_resources.models import DataResource


def kmz_resource(request, *args, **kwargs):
    slug = kwargs['slug']
    ff = kwargs['filename']
    ds = get_object_or_404(DataResource, slug=slug)

    if ds.driver != 'ga_resources.drivers.kmz':
        raise Http404(slug)
    else:
        _, _, cfg = ds.driver_instance.ready_data_resource(*args, **kwargs)

        try:
            return HttpResponse(ds.driver_instance.open_stream(ff), mimetype='application/x-binary')
        except Exception, e:
            raise Http404(str(e))


def kmz_features(request, *args, **kwargs):
    slug = kwargs['slug']
    ds = get_object_or_404(DataResource, slug=slug)

    if ds.driver != 'ga_resources.drivers.kmz':
        raise Http404(slug)
    else:
        _, _, cfg = ds.driver_instance.ready_data_resource(*args, **kwargs)
        return HttpResponse(ds.driver_instance.features(), mimetype='application/vnd.google-earth.kml+xml')


def kmz_ground_overlays_json(request, *args, **kwargs):
    slug = kwargs['slug']
    ds = get_object_or_404(DataResource, slug=slug)

    if ds.driver != 'ga_resources.drivers.kmz':
        raise Http404(slug)
    else:
        _, _, cfg = ds.driver_instance.ready_data_resource(*args, **kwargs)
        ground_overlays = ds.driver_instance.ground_overlays()
        for i, g in enumerate(ground_overlays):
            ground_overlays[i]['href'] = '/ga_resources/kmz-resource/{slug}:{href}'.format(slug=slug,
                                                                                           href=ground_overlays[i][
                                                                                               'href'])
        return HttpResponse(json.dumps(ground_overlays, indent=4), mimetype='application/javascript')
