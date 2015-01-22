from django.dispatch import receiver
from hs_core.signals import *
from hs_app_netCDF.models import NetcdfResource, NetcdfMetaData, Variable


# receiver used to extract metadata after user click on "create resource"
@receiver(pre_create_resource, sender=NetcdfResource)
def netcdf_create_resource_trigger(sender, **kwargs):
    if sender is NetcdfResource:
        files = kwargs['files']
        metadata = kwargs['metadata']
        if files:
            # Extract the metadata from netcdf file
            infile = files[0]
            import nc_functions.nc_meta as nc_meta
            res_md_dict = nc_meta.get_nc_meta_dict(infile.file.name)
            res_dublin_core_meta = res_md_dict['dublin_core_meta']
            res_type_specific_meta = res_md_dict['type_specific_meta']

            # Save dublin core meta to metadata variable
            # res_sci_md = {
            #     'Description': res_dublin_core_meta['description'],
            #     'Title': res_dublin_core_meta['title'],
            #     'Coverage temporal': res_dublin_core_meta['temporal'],
            #     'Coverage spatial': res_dublin_core_meta['spatial'],
            #     'Source': res_dublin_core_meta['source'],
            #     'References': res_dublin_core_meta['references'],
            # }

            # Save extended meta to metadata variable
            for var_name, var_meta in res_type_specific_meta.items():
                meta_info = {}
                for element, value in var_meta.items():
                    if value != '':
                        meta_info[element] = value
                metadata.append({'variable': meta_info})

            return metadata

