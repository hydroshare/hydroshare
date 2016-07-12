from django.dispatch import receiver
from hs_core.signals import pre_create_resource
from ref_ts.models import RefTimeSeriesResource
from . import ts_utils

# redirect to render custom create-resource template
@receiver(pre_create_resource, sender=RefTimeSeriesResource)
def ref_time_series_describe_resource_trigger(sender, **kwargs):
    page_url_dict = kwargs['page_url_dict']
    url_key = kwargs['url_key']
    page_url_dict[url_key] = "pages/create-ref-time-series.html"
    validate_files_dict = kwargs['validate_files']
    metadata = kwargs['metadata']
    try:
        reference_url_dict = None
        site_dict = None
        variable_dict = None
        for metadata_dict in metadata:
            if metadata_dict.has_key("referenceurl"):
                reference_url_dict = metadata_dict["referenceurl"]
            elif metadata_dict.has_key("site"):
                site_dict = metadata_dict["site"]
            elif metadata_dict.has_key("variable"):
                variable_dict = metadata_dict["variable"]
        if reference_url_dict:
            ref_url = reference_url_dict["value"]
            ref_type = reference_url_dict["type"]
            site_code = None
            variable_code = None
            if site_dict:
                site_code = site_dict["code"]
            if variable_dict:
                variable_code = variable_dict["code"]
            ts_dict = ts_utils.QueryHydroServerGetParsedWML(service_url=ref_url,
                                                            soap_or_rest=ref_type,
                                                            site_code=site_code,
                                                            variable_code=variable_code)
            del metadata[:]
            ts_utils.prepare_metadata_list(metadata=metadata,
                                           ts_dict=ts_dict,
                                           url=ref_url,
                                           reference_type=ref_type)
        else:
            raise Exception("Missing parameter 'referenceurl' in request")

    except Exception as ex:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = ex.message
        kwargs['files'].append(None)
