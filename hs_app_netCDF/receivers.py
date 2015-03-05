from django.dispatch import receiver
from hs_core.signals import *
from hs_app_netCDF.models import NetcdfResource, NetcdfMetaData, Variable
from hs_app_netCDF.forms import *
from hs_core import hydroshare
from hs_core.hydroshare.resource import ResourceFile
import os
from hs_core.hydroshare import utils


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
            try:
                res_md_dict = nc_meta.get_nc_meta_dict(infile.file.name)
                res_dublin_core_meta = res_md_dict['dublin_core_meta']
                res_type_specific_meta = res_md_dict['type_specific_meta']
            except:
                res_dublin_core_meta = {}
                res_type_specific_meta = {}

            # add title
            if res_dublin_core_meta.get('title'):
                title = {'title': {'value': res_dublin_core_meta['title']}}
                metadata.append(title)
            # add description
            if res_dublin_core_meta.get('description'):
                description = {'description': {'abstract': res_dublin_core_meta['description']}}
                metadata.append(description)
            # add source
            if res_dublin_core_meta.get('source'):
                source = {'source': {'derived_from': res_dublin_core_meta['source']}}
                metadata.append(source)
            # add relation
            if res_dublin_core_meta.get('references'):
                relation = {'relation': {'type': 'cites', 'value': res_dublin_core_meta['references']}}
                metadata.append(relation)
            # add coverage - period
            if res_dublin_core_meta.get('period'):
                period = {'coverage': {'type': 'period', 'value': res_dublin_core_meta['period']}}
                metadata.append(period)
            # add coverage - box
            if res_dublin_core_meta.get('box'):
                box = {'coverage': {'type': 'box', 'value': res_dublin_core_meta['box']}}
                metadata.append(box)

            # Save extended meta to metadata variable
            for var_name, var_meta in res_type_specific_meta.items():
                meta_info = {}
                for element, value in var_meta.items():
                    if value != '':
                        meta_info[element] = value
                metadata.append({'variable': meta_info})

# receiver used to create netcdf header text after user click on "create resource"
@receiver(post_create_resource,sender=NetcdfResource)
def netcdf_create_ncdump_file(sender, **kwargs):
    if sender is NetcdfResource:
        nc_res = kwargs['resource']
        nc_files = nc_res.files.all()
        if nc_files:
            nc_file = nc_res.files.all()[0]
            nc_file_name = nc_file.resource_file.path
            # create InMemoryUploadedFile text file to store the dump info and add it to resource
            import nc_functions.nc_dump as nc_dump
            if nc_dump.get_nc_dump_string_by_ncdump(nc_file_name):
                dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_file_name)
            else:
                dump_str = nc_dump.get_nc_dump_string(nc_file_name)

            if dump_str:
                from django.core.files.uploadedfile import InMemoryUploadedFile
                import StringIO, os
                io = StringIO.StringIO()
                io.write(dump_str)
                dump_file_name = '.'.join(os.path.basename(nc_file_name).split('.')[:-1])+'_header_info.txt'
                dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
                dump_file.seek(0)
                hydroshare.add_resource_files(nc_res.short_id, dump_file)

                # add file format for text file
                file_format_type = utils.get_file_mime_type(dump_file_name)
                if file_format_type not in [mime.value for mime in nc_res.metadata.formats.all()]:
                    nc_res.metadata.create_element('format', value=file_format_type)

# receiver used after user clicks on "delete file" for existing netcdf file
@receiver(pre_delete_file_from_resource, sender=NetcdfResource)
def netcdf_pre_delete_file_from_resource(sender, **kwargs):
    if sender is NetcdfResource:
        nc_res = kwargs['resource']
        del_file = kwargs['file']
        del_file_ext = os.path.splitext(del_file.resource_file.name)[-1]
        if del_file_ext == '.nc':
            # delete the netcdf header text file
            for f in ResourceFile.objects.filter(object_id=nc_res.id):
                ext = os.path.splitext(f.resource_file.name)[-1]
                if ext == '.txt':
                    f.resource_file.delete()
                    f.delete()
                    break
            # delete all the coverage info
            cov_box = nc_res.metadata.coverages.all().filter(type='box').first()
            cov_period = nc_res.metadata.coverages.all().filter(type='period').first()
            if cov_box:
                    # TODO: delete old box info, currently it just updates the values
                    from collections import OrderedDict
                    box_info = OrderedDict([
                            ('units', "Decimal degrees"),
                            ('projection', 'WGS 84 EPSG:4326'),
                            ('northlimit', 0.0),
                            ('southlimit', 0.0),
                            ('eastlimit', 0.0),
                            ('westlimit', 0.0)
                        ])
                    nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=box_info)
            if cov_period:
                pass # TODO: delete the old period info, currently it just keeps the old period info

            # delete all the extended meta info
            nc_res.metadata.variables.all().delete()


# receiver used after user clicks on "add file" for existing resource netcdf file
@receiver(pre_add_files_to_resource, sender=NetcdfResource)
def netcdf_pre_add_files_to_resource(sender, **kwargs):
    if sender is NetcdfResource:
        nc_res = kwargs['resource']
        files = kwargs['files']
        if files:
            infile = files[0]
            if infile.name[-3:] == '.nc':
                # delete all existing resource files and metadata related
                for f in ResourceFile.objects.filter(object_id=nc_res.id):
                        f.resource_file.delete()
                        f.delete()

                # extract metadata
                import nc_functions.nc_meta as nc_meta
                try:
                    res_md_dict = nc_meta.get_nc_meta_dict(infile.file.name)
                    res_dublin_core_meta = res_md_dict['dublin_core_meta']
                    res_type_specific_meta = res_md_dict['type_specific_meta']
                except:
                    res_dublin_core_meta = {}
                    res_type_specific_meta = {}

                # update box info
                cov_box = nc_res.metadata.coverages.all().filter(type='box').first()
                if cov_box:
                    # TODO: delete old box info, currently it just updates the values
                    from collections import OrderedDict
                    box_info = OrderedDict([
                            ('units', "Decimal degrees"),
                            ('projection', 'WGS 84 EPSG:4326'),
                            ('northlimit', 0.0),
                            ('southlimit', 0.0),
                            ('eastlimit', 0.0),
                            ('westlimit', 0.0)
                        ])
                    nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=box_info)
                if res_dublin_core_meta.get('box'):
                    if cov_box:
                        nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=res_dublin_core_meta['box'])
                    else:
                        nc_res.metadata.create_element('coverage', type='box', value=res_dublin_core_meta['box'])

                # update period info
                cov_period = nc_res.metadata.coverages.all().filter(type='period').first()
                if cov_period:
                    # TODO delete the old period info, currently it just keeps the old period info
                    pass
                if res_dublin_core_meta.get('period'):
                    if cov_period:
                        nc_res.metadata.update_element('coverage', cov_period.id, type='period', value=res_dublin_core_meta['period'])
                    else:
                        nc_res.metadata.create_element('coverage', type='period', value=res_dublin_core_meta['period'])

                # update variable info
                nc_res.metadata.variables.all().delete()
                for var_info in res_type_specific_meta.values():
                    nc_res.metadata.create_element('variable',
                                                   name=var_info['name'],
                                                   unit=var_info['unit'],
                                                   type=var_info['type'],
                                                   shape=var_info['shape'],
                                                   missing_value=var_info['missing_value'],
                                                   descriptive_name=var_info['descriptive_name'])

                # create a header text file and add to resource
                nc_file_name = infile.file.name
                # create InMemoryUploadedFile text file to store the dump info and add it to resource
                import nc_functions.nc_dump as nc_dump
                if nc_dump.get_nc_dump_string_by_ncdump(nc_file_name):
                    dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_file_name)
                else:
                    dump_str = nc_dump.get_nc_dump_string(nc_file_name)
                if dump_str:
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    import StringIO,os
                    io = StringIO.StringIO()
                    io.write(dump_str)
                    dump_file_name = infile.name[:-3] +'_header_info.txt'
                    dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
                    dump_file.seek(0)
                    hydroshare.add_resource_files(nc_res.short_id, dump_file)
                    # add file format for text file
                    file_format_type = utils.get_file_mime_type(dump_file_name)
                    if file_format_type not in [mime.value for mime in nc_res.metadata.formats.all()]:
                        nc_res.metadata.create_element('format', value=file_format_type)


@receiver(pre_metadata_element_create, sender=NetcdfResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name']
    if element_name == "variable":
        element_form = VariableForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=NetcdfResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == 'variable':
        form_data = {}
        for field_name in VariableValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = VariableValidationForm(form_data)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}