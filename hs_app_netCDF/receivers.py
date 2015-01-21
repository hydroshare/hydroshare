from django.dispatch import receiver
#from hs_core.hydroshare import pre_describe_resource, pre_create_resource, post_create_resource
from hs_core.signals import *
from hs_app_netCDF.models import NetcdfResource, NetcdfMetaData, Variable


res_md_dict = {}
# signal handler to extract metadata from uploaded netcdf file and return template contexts
# to populate create-resource.html template page
@receiver(pre_describe_resource, sender=NetcdfResource)
def netcdf_describe_resource_trigger(sender, **kwargs):
    if sender is NetcdfResource:
        files = kwargs['files']
        if files:
            # Extract the metadata as dictionary from netcdf file
            infile = files[0]
            import nc_functions.nc_meta as nc_meta
            global res_md_dict
            res_md_dict = nc_meta.get_netcdf_meta_dict(infile.file.name)
            res_dublin_core_meta = res_md_dict['dublin_core_meta']
            res_type_specific_meta = res_md_dict['type_specific_meta']

            # Create res_sci_metadata context info
            res_sci_md = {
                'Description': res_dublin_core_meta['description'],
                'Title': res_dublin_core_meta['title'],
                'Coverage temporal': res_dublin_core_meta['temporal'],
                'Coverage spatial': res_dublin_core_meta['spatial'],
                'Source': res_dublin_core_meta['source'],
                'References': res_dublin_core_meta['references'],
            }

            # Create res_add_metadata context info
            res_ext_md = res_type_specific_meta

            return {"res_sci_metadata": res_sci_md,
                    "res_add_metadata": res_ext_md}

