
"""test the jaccard metric for the distance between two resources
point coverage: 5057577e8573433d8045b59db91b2550
box coverage: a173f02bd00b4eceb0a9f44cc77cee6d
box coverage negative longitude: cd8bc1c38b254031854b8b8aaee08a05
"""

# from hs_core.hydroshare.utils import get_resource_by_shortkey
from pprint import pprint

def geo_normalized_coverage(resource):
    if resource.metadata is not None: 
        c = resource.metadata.spatial_coverage
        pprint(c)
        if c is not None: 
            cc = c.value

            if c.type == 'point':
                if isinstance(cc['east'], str): 
                    cc['east'] = float(cc['east'])
                if isinstance(cc['east'], str): 
                    cc['north'] = float(cc['north'])

                if cc['east'] < 0:  # convert to east Longitude
                    cc['east'] = cc['east'] + 360
                cc['type'] = 'point'
                return cc

            if c.type == 'box':
                if isinstance(cc['eastlimit'], str): 
                    cc['eastlimit'] = float(cc['eastlimit'])
                if isinstance(cc['westlimit'], str): 
                    cc['westlimit'] = float(cc['westlimit'])
                if isinstance(cc['northlimit'], str): 
                    cc['northlimit'] = float(cc['northlimit'])
                if isinstance(cc['southlimit'], str): 
                    cc['southlimit'] = float(cc['southlimit'])

                if cc['eastlimit'] < 0:  # convert to east Longitude
                    cc['eastlimit'] = cc['eastlimit'] + 360
                if cc['westlimit'] < 0:  # convert to east Longitude
                    cc['westlimit'] = cc['westlimit'] + 360
                cc['type'] = 'box'

            return cc
    return None
   

def geo_one_degree(rc, sc):
    if abs(rc['east']-sc['east']) <= 1.0 and \
       abs(rc['north']-sc['north']) <= 1.0:
        return 1.0
    else:
        return 0.0  # could be exponential decay past a degree away via e^-alphat decay function


def geo_inside(rc, sc):
    assert(rc['type'] == 'point')
    assert(sc['type'] == 'box')
    if rc['east'] >= sc['westlimit'] and \
       rc['east'] <= sc['eastlimit'] and \
       rc['north'] >= sc['southlimit'] and \
       rc['north'] <= sc['northlimit']:
        return 1.0
    else:
        return 0.0  # could be exponentially smaller based upon distance between box and point.


def geo_area_union(rc, sc):
    west = min(rc['westlimit'], sc['westlimit'])
    east = max(rc['eastlimit'], sc['eastlimit'])
    south = min(rc['southlimit'], sc['southlimit'])
    north = max(rc['northlimit'], sc['northlimit'])
    return (east - west) * (north - south)


def geo_area_intersection(rc, sc):
    if rc['northlimit'] < sc['southlimit'] or \
       rc['southlimit'] > sc['northlimit'] or \
       rc['westlimit'] > sc['eastlimit'] or \
       rc['eastlimit'] < sc['westlimit']:
        return 0
    west = max(rc['westlimit'], sc['westlimit'])
    east = min(rc['eastlimit'], sc['eastlimit'])
    south = max(rc['southlimit'], sc['southlimit'])
    north = min(rc['northlimit'], sc['northlimit'])
    return (east - west) * (north - south)


def geo_jaccard(r, s):
    rc = geo_normalized_coverage(r)
    sc = geo_normalized_coverage(s)
    if rc is None or sc is None: 
        return 0.0
    return geo_jaccard_internal(rc, sc)


def geo_jaccard_internal(rc, sc):
    if rc['type'] == 'point' and sc['type'] == 'point':
        return geo_one_degree(rc, sc)
    elif rc['type'] == 'point' and sc['type'] == 'box':
        return geo_inside(rc, sc)
    elif rc['type'] == 'box' and sc['type'] == 'point':
        return geo_inside(sc, rc)
    else:
        return geo_area_intersection(rc, sc) / geo_area_union(rc, sc)
