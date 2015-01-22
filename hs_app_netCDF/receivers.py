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

            # For dict key name and structure refer to the hs_core/models.py
            # TODO add title
            # title = {'title': {'value': res_dublin_core_meta['title']}
            # add description
            description = {'description': {'abstract': res_dublin_core_meta['description']}}
            metadata.append(description)
            # add source
            source = {'source': {'derived_from': res_dublin_core_meta['source']}}
            metadata.append(source)
            # add relation
            relation = {'relation': {'type': 'cites', 'value': res_dublin_core_meta['references']}}
            metadata.append(relation)
            # add coverage - period
            period = {'coverage': {'type': 'period', 'value': res_dublin_core_meta['period']}}
            metadata.append(period)
            # add coverage - box
            box = {'coverage': {'type': 'box', 'value': res_dublin_core_meta['box']}}
            metadata.append(box)

            # Save extended meta to metadata variable
            for var_name, var_meta in res_type_specific_meta.items():
                meta_info = {}
                for element, value in var_meta.items():
                    if value != '':
                        meta_info[element] = value
                metadata.append({'variable': meta_info})

            return metadata

