import json
from dateutil import parser
from operator import lt, gt


def update_resource_coverage_element(resource):
    # update resource spatial coverage based on coverage metadata from the
    # logical files in the resource
    spatial_coverages = [lf.metadata.spatial_coverage for lf in resource.logical_files
                         if lf.metadata.spatial_coverage is not None]

    bbox_limits = {'box': {'northlimit': 'northlimit', 'southlimit': 'southlimit',
                           'eastlimit': 'eastlimit', 'westlimit': 'westlimit'},
                   'point': {'northlimit': 'north', 'southlimit': 'north',
                             'eastlimit': 'east', 'westlimit': 'east'}
                   }

    def set_coverage_data(res_coverage_value, lfo_coverage_element, box_limits):
        comparison_operator = {'northlimit': lt, 'southlimit': gt, 'eastlimit': lt,
                               'westlimit': gt}
        for key in comparison_operator.keys():
            if comparison_operator[key](res_coverage_value[key],
                                        lfo_coverage_element.value[box_limits[key]]):
                res_coverage_value[key] = lfo_coverage_element.value[box_limits[key]]

    cov_type = "point"
    bbox_value = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                  'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}

    if len(spatial_coverages) > 1:
        # check if one of the coverage is of type box
        if any(sp_cov.type == 'box' for sp_cov in spatial_coverages):
            cov_type = 'box'
        else:
            # check if the coverages represent different locations
            unique_lats = set([sp_cov.value['north'] for sp_cov in spatial_coverages])
            unique_lons = set([sp_cov.value['east'] for sp_cov in spatial_coverages])
            if len(unique_lats) == 1 and len(unique_lons) == 1:
                cov_type = 'point'
            else:
                cov_type = 'box'
        if cov_type == 'point':
            sp_cov = spatial_coverages[0]
            bbox_value = dict()
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['north'] = sp_cov.value['north']
            bbox_value['east'] = sp_cov.value['east']
        else:
            for sp_cov in spatial_coverages:
                if sp_cov.type == "box":
                    box_limits = bbox_limits['box']
                    set_coverage_data(bbox_value, sp_cov, box_limits)
                else:
                    # point type coverage
                    box_limits = bbox_limits['point']
                    set_coverage_data(bbox_value, sp_cov, box_limits)

    elif len(spatial_coverages) == 1:
        sp_cov = spatial_coverages[0]
        if sp_cov.type == "box":
            cov_type = 'box'
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['northlimit'] = sp_cov.value['northlimit']
            bbox_value['eastlimit'] = sp_cov.value['eastlimit']
            bbox_value['southlimit'] = sp_cov.value['southlimit']
            bbox_value['westlimit'] = sp_cov.value['westlimit']
        else:
            # point type coverage
            cov_type = "point"
            bbox_value = dict()
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['north'] = sp_cov.value['north']
            bbox_value['east'] = sp_cov.value['east']

    spatial_cov = resource.metadata.coverages.all().exclude(type='period').first()
    if len(spatial_coverages) > 0:
        if spatial_cov:
            spatial_cov.type = cov_type
            spatial_cov._value = json.dumps(bbox_value)
            spatial_cov.save()
        else:
            resource.metadata.create_element("coverage", type=cov_type, value=bbox_value)
    else:
        # delete spatial coverage element for the resource since the content files don't have any
        # spatial coverage
        if spatial_cov:
            spatial_cov.delete()

    # update resource temporal coverage
    temporal_coverages = [lf.metadata.temporal_coverage for lf in resource.logical_files
                          if lf.metadata.temporal_coverage is not None]

    date_data = {'start': None, 'end': None}

    def set_date_value(date_data, coverage_element, key):
        comparison_operator = gt if key == 'start' else lt
        if date_data[key] is None:
            date_data[key] = coverage_element.value[key]
        else:
            if comparison_operator(parser.parse(date_data[key]),
                                   parser.parse(coverage_element.value[key])):
                date_data[key] = coverage_element.value[key]

    for temp_cov in temporal_coverages:
        set_date_value(date_data, temp_cov, 'start')
        set_date_value(date_data, temp_cov, 'end')

    temp_cov = resource.metadata.coverages.all().filter(type='period').first()
    if date_data['start'] is not None and date_data['end'] is not None:
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            resource.metadata.create_element("coverage", type='period', value=date_data)
    elif temp_cov:
        # delete the temporal coverage for the resource since the content files don't have
        # temporal coverage
        temp_cov.delete()
