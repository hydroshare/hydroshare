import logging
from django.dispatch import receiver
from hs_core.signals import pre_create_resource
from ref_ts.models import RefTimeSeriesResource
from . import ts_utils

logger = logging.getLogger(__name__)

# redirect to render custom create-resource template
@receiver(pre_create_resource, sender=RefTimeSeriesResource)
def ref_time_series_describe_resource_trigger(sender, **kwargs):
    url_key = kwargs['url_key']
    if url_key is not None:
        # the call is from UI
        page_url_dict = kwargs['page_url_dict']
        page_url_dict[url_key] = "pages/create-ref-time-series.html"
    else:
        # the call is from rest api
        metadata = kwargs['metadata']
        try:
            reference_url_dict = None
            site_dict = None
            variable_dict = None
            for metadata_dict in metadata:
                if "referenceurl" in metadata_dict:
                    reference_url_dict = metadata_dict["referenceurl"]
                elif "site" in metadata_dict:
                    site_dict = metadata_dict["site"]
                elif "variable" in metadata_dict:
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
                if ref_type == "soap" and (site_code is None or variable_code is None):
                    raise Exception("site_code and variable_code should be provided with soap url")
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
            logger.exception("Failed to create refts res from rest api: " + ex.message)
            raise ex
