import pytest

from hs_file_types.models import ModelInstanceLogicalFile


# TODO: implement tests for linking model instance aggregation to model program aggregation using the
# FK (executed_by) attribute of model instance aggregation
# The following tests cases for linking needs to be implemented:
# 1. linking aggregations within the same resource
#     a. linking one mp aggregation to one mi aggregation
#     b. linking one mp aggregation to two mi aggregations
# 2. linking aggregations that do not belong to the same resource
# 3. test linking is not allowed if user does not have access to the resource that contains the mp aggregation
# 4. test that mi aggregation does not get deleted if the linked mp aggregation gets deleted
# 5. test that mi aggregation does not get deleted if the resource containing the linked mp aggregation gets deleted

@pytest.mark.django_db(transaction=True)
def test_set_metadata(composite_resource_with_mi_aggregation, mock_irods):
    """Test that we can store all metadata items for a model instance aggregation"""

    res, user = composite_resource_with_mi_aggregation
    # mi_aggr = next(res.logical_files)
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert isinstance(mi_aggr, ModelInstanceLogicalFile)

    # test extra metadata
    assert not mi_aggr.metadata.extra_metadata
    extra_meta = {'key1': 'value 1', 'key2': 'value 2'}
    mi_aggr.metadata.extra_metadata = extra_meta
    mi_aggr.metadata.save()
    assert mi_aggr.metadata.extra_metadata == extra_meta

    # test keywords
    assert not mi_aggr.metadata.keywords
    keywords = ['kw-1', 'kw-2']
    mi_aggr.metadata.keywords = keywords
    mi_aggr.metadata.save()
    assert mi_aggr.metadata.keywords == keywords

    # test coverage metadata
    assert not mi_aggr.metadata.coverages.all()
    value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
    temp_cov = mi_aggr.metadata.create_element('coverage', type='period', value=value_dict)
    assert temp_cov.value['name'] == 'Name for period coverage'
    assert temp_cov.value['start'] == '1/1/2000'
    assert temp_cov.value['end'] == '12/12/2012'
    assert mi_aggr.metadata.coverages.all().count() == 1

    value_dict = {'east': '56.45678', 'north': '12.6789', 'units': 'Decimal degree'}
    spatial_cov = mi_aggr.metadata.create_element('coverage', type='point', value=value_dict)
    assert spatial_cov.value['projection'] == 'WGS 84 EPSG:4326'
    assert spatial_cov.value['units'] == 'Decimal degree'
    assert spatial_cov.value['north'] == 12.6789
    assert spatial_cov.value['east'] == 56.45678
    assert mi_aggr.metadata.coverages.all().count() == 2
    # test model output metadata
    assert not mi_aggr.metadata.has_model_output
    mi_aggr.metadata.has_model_output = True
    mi_aggr.metadata.save()
    # test setting metadata json
    assert not mi_aggr.metadata.metadata_json
    # set mi metadata json from the content of the following file
    schema_file_path = 'pytest/assets/mi_metadata.json'
    with open(schema_file_path, 'r') as file_obj:
        meta_json = file_obj.read()
    assert len(meta_json) > 0
    mi_aggr.metadata.metadata_json = meta_json
    mi_aggr.metadata.save()
    mi_aggr = ModelInstanceLogicalFile.objects.first()
    assert mi_aggr.metadata.metadata_json


