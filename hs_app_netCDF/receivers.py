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
def netcdf_pre_create_resource(sender, **kwargs):
    if sender is NetcdfResource:
        files = kwargs['files']
        metadata = kwargs['metadata']
        validate_files_dict = kwargs['validate_files']
        res_title = kwargs['title']

        if files:
            infile = files[0]

            # file validation and metadata extraction
            import nc_functions.nc_utils as nc_utils
            import netCDF4
            nc_dataset = nc_utils.get_nc_dataset(infile.file.name)

            if isinstance(nc_dataset, netCDF4.Dataset):
                # Extract the metadata from netcdf file
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
                    if res_title == 'Untitled resource':
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

                # Save extended meta to original spatial coverage
                if res_dublin_core_meta.get('original-box'):
                    if res_dublin_core_meta.get('projection-info'):
                        ori_cov = {'originalcoverage': {'value': res_dublin_core_meta['original-box'],
                                                        'projection_string_type': res_dublin_core_meta['projection-info']['type'],
                                                        'projection_string_text': res_dublin_core_meta['projection-info']['text']}}
                    else:
                        ori_cov = {'originalcoverage': {'value': res_dublin_core_meta['original-box']}}

                    metadata.append(ori_cov)


                #create the ncdump text file
                import nc_functions.nc_dump as nc_dump
                if nc_dump.get_nc_dump_string_by_ncdump(infile.file.name):
                    dump_str = nc_dump.get_nc_dump_string_by_ncdump(infile.file.name)
                else:
                    dump_str = nc_dump.get_nc_dump_string(infile.file.name)

                if dump_str:
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    import StringIO, os
                    # refine dump_str first line
                    nc_file_name = '.'.join(os.path.basename(infile.name).split('.')[:-1])
                    first_line = list('netcdf {0} '.format(nc_file_name))
                    first_line_index = dump_str.index('{')
                    dump_str_list = first_line + list(dump_str)[first_line_index:]
                    dump_str = "".join(dump_str_list)

                    # write dump_str to temporary file
                    io = StringIO.StringIO()
                    io.write(dump_str)
                    dump_file_name = nc_file_name + '_header_info.txt'
                    dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
                    files.append(dump_file)

            else:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = 'Please check if the uploaded file is in valid NetCDF format.'



# # receiver used to create netcdf header text after user click on "create resource"
# not working need to wait for the irods api finished
# @receiver(post_create_resource, sender=NetcdfResource)
# def netcdf_post_create_resource(sender, **kwargs):
#     # Add ncdump text file to resource
#     if sender is NetcdfResource:
#         nc_res = kwargs['resource']
#         nc_files = nc_res.files.all()
#         if nc_files:
#             nc_file = nc_res.files.all()[0]
#             nc_file_name = nc_file.resource_file.path
#             # create InMemoryUploadedFile text file to store the dump info and add it to resource
#             import nc_functions.nc_dump as nc_dump
#             if nc_dump.get_nc_dump_string_by_ncdump(nc_file_name):
#                 dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_file_name)
#             else:
#                 dump_str = nc_dump.get_nc_dump_string(nc_file_name)
#
#             if dump_str:
#                 from django.core.files.uploadedfile import InMemoryUploadedFile
#                 import StringIO, os
#                 io = StringIO.StringIO()
#                 io.write(dump_str)
#                 dump_file_name = '.'.join(os.path.basename(nc_file_name).split('.')[:-1])+'_header_info.txt'
#                 dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
#                 dump_file.seek(0)
#                 hydroshare.add_resource_files(nc_res.short_id, dump_file)
#                 # add file format for text file
#                 file_format_type = utils.get_file_mime_type(dump_file_name)
#                 if file_format_type not in [mime.value for mime in nc_res.metadata.formats.all()]:
#                     nc_res.metadata.create_element('format', value=file_format_type)

# receiver used after user clicks on "delete file" for existing netcdf file
@receiver(pre_delete_file_from_resource, sender=NetcdfResource)
def netcdf_pre_delete_file_from_resource(sender, **kwargs):
    if sender is NetcdfResource:
        nc_res = kwargs['resource']
        del_file = kwargs['file']
        del_file_ext = os.path.splitext(del_file.resource_file.name)[-1]

        # TODO: update resource modification info
        # user = kwargs['user']
        # resource_modified(resource, user)

        if del_file_ext == '.nc':
            # delete the netcdf header text file
            for f in ResourceFile.objects.filter(object_id=nc_res.id):
                ext = os.path.splitext(f.resource_file.name)[-1]
                if ext == '.txt':
                    f.resource_file.delete()
                    f.delete()
                    break
            # delete all the coverage info
            nc_res.metadata.coverages.all().delete()
            # cov_box = nc_res.metadata.coverages.all().filter(type='box').first()
            # cov_period = nc_res.metadata.coverages.all().filter(type='period').first()
            # if cov_box:
            #
            #         from collections import OrderedDict
            #         box_info = OrderedDict([
            #                 ('units', "Decimal degrees"),
            #                 ('projection', 'WGS 84 EPSG:4326'),
            #                 ('northlimit', 0.0),
            #                 ('southlimit', 0.0),
            #                 ('eastlimit', 0.0),
            #                 ('westlimit', 0.0)
            #             ])
            #         nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=box_info)
            # if cov_period:
            #     pass

            # delete all the extended meta info
            nc_res.metadata.variables.all().delete()


# receiver used after user clicks on "add file" for existing resource netcdf file
@receiver(pre_add_files_to_resource, sender=NetcdfResource)
def netcdf_pre_add_files_to_resource(sender, **kwargs):
    if sender is NetcdfResource:
        nc_res = kwargs['resource']
        files = kwargs['files']
        validate_files_dict = kwargs['validate_files']


        if len(files) >1:
            # file number validation
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Only one file can be uploaded.'
        elif len(files) == 1:
            # file type validation and existing metadata update and create new ncdump text file
            infile = files[0]
            import nc_functions.nc_utils as nc_utils
            import netCDF4
            nc_dataset = nc_utils.get_nc_dataset(infile.file.name)
            if isinstance(nc_dataset, netCDF4.Dataset):
                # delete all existing resource files and metadata related
                for f in ResourceFile.objects.filter(object_id=nc_res.id):
                        f.resource_file.delete()
                        f.delete()

                # TODO: update resource modification info
                # user = kwargs['user']
                # resource_modified(resource, user)

                # extract metadata
                import nc_functions.nc_meta as nc_meta
                try:
                    res_dublin_core_meta = nc_meta.get_dublin_core_meta(nc_dataset)
                except:
                    res_dublin_core_meta = {}

                try:
                    res_type_specific_meta = nc_meta.get_type_specific_meta(nc_dataset)
                except:
                    res_type_specific_meta = {}

                # update box info
                nc_res.metadata.coverages.all().delete()
                if res_dublin_core_meta.get('box'):
                    nc_res.metadata.create_element('coverage', type='box', value=res_dublin_core_meta['box'])
                #cov_box = nc_res.metadata.coverages.all().filter(type='box').first()
                # if cov_box:
                #
                #
                #     from collections import OrderedDict
                #     box_info = OrderedDict([
                #             ('units', "Decimal degrees"),
                #             ('projection', 'WGS 84 EPSG:4326'),
                #             ('northlimit', 0.0),
                #             ('southlimit', 0.0),
                #             ('eastlimit', 0.0),
                #             ('westlimit', 0.0)
                #         ])
                #     nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=box_info)
                # if res_dublin_core_meta.get('box'):
                #     if cov_box:
                #         nc_res.metadata.update_element('coverage', cov_box.id, type='box', value=res_dublin_core_meta['box'])
                #     else:
                #         nc_res.metadata.create_element('coverage', type='box', value=res_dublin_core_meta['box'])

                # update period info
                if res_dublin_core_meta.get('period'):
                    nc_res.metadata.create_element('coverage', type='period', value=res_dublin_core_meta['period'])
                # cov_period = nc_res.metadata.coverages.all().filter(type='period').first()
                # if cov_period:
                #     pass
                # if res_dublin_core_meta.get('period'):
                #     if cov_period:
                #         nc_res.metadata.update_element('coverage', cov_period.id, type='period', value=res_dublin_core_meta['period'])
                #     else:
                #         nc_res.metadata.create_element('coverage', type='period', value=res_dublin_core_meta['period'])


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


                # update the original spatial coverage meta
                nc_res.metadata.ori_coverage.all().delete()
                if res_dublin_core_meta.get('original-box'):
                    if res_dublin_core_meta.get('projection-info'):
                        nc_res.metadata.create_element('originalcoverage',
                                                        value=res_dublin_core_meta['original-box'],
                                                        projection_string_type=res_dublin_core_meta['projection-info']['type'],
                                                        projection_string_text=res_dublin_core_meta['projection-info']['text'])
                    else:
                        nc_res.metadata.create_element('originalcoverage', value=res_dublin_core_meta['original-box'])

                # create the ncdump text file
                import nc_functions.nc_dump as nc_dump
                if nc_dump.get_nc_dump_string_by_ncdump(infile.file.name):
                    dump_str = nc_dump.get_nc_dump_string_by_ncdump(infile.file.name)
                else:
                    dump_str = nc_dump.get_nc_dump_string(infile.file.name)

                if dump_str:
                    from django.core.files.uploadedfile import InMemoryUploadedFile
                    import StringIO, os
                    # refine dump_str first line
                    nc_file_name = '.'.join(os.path.basename(infile.name).split('.')[:-1])
                    first_line = list('netcdf {0} '.format(nc_file_name))
                    first_line_index = dump_str.index('{')
                    dump_str_list = first_line + list(dump_str)[first_line_index:]
                    dump_str = "".join(dump_str_list)

                    # write dump_str to temporary file
                    io = StringIO.StringIO()
                    io.write(dump_str)
                    dump_file_name = nc_file_name + '_header_info.txt'
                    dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
                    files.append(dump_file)

            else:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = 'Please check if the uploaded file is in valid NetCDF format.'

# @receiver(post_add_files_to_resource, sender=NetcdfResource)
# def netcdf_post_add_files_to_resource(sender, **kwargs):
#     # Add ncdump text file to resource
#     if sender is NetcdfResource:
#         nc_res = kwargs['resource']
#         nc_files = nc_res.files.all()
#         if nc_files:
#             nc_file = nc_res.files.all()[0]
#             nc_file_name = nc_file.resource_file.path
#
#             # create InMemoryUploadedFile text file to store the dump info and add it to resource
#             import nc_functions.nc_dump as nc_dump
#             if nc_dump.get_nc_dump_string_by_ncdump(nc_file_name):
#                 dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_file_name)
#             else:
#                 dump_str = nc_dump.get_nc_dump_string(nc_file_name)
#             if dump_str:
#                 from django.core.files.uploadedfile import InMemoryUploadedFile
#                 import StringIO, os
#                 io = StringIO.StringIO()
#                 io.write(dump_str)
#                 dump_file_name = '.'.join(os.path.basename(nc_file_name).split('.')[:-1])+'_header_info.txt'
#                 dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len, None)
#                 dump_file.seek(0)
#                 hydroshare.add_resource_files(nc_res.short_id, dump_file)
#                 # add file format for text file
#                 file_format_type = utils.get_file_mime_type(dump_file_name)
#                 if file_format_type not in [mime.value for mime in nc_res.metadata.formats.all()]:
#                     nc_res.metadata.create_element('format', value=file_format_type)


@receiver(pre_metadata_element_create, sender=NetcdfResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name']
    if element_name == "variable":
        element_form = VariableForm(data=request.POST)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageForm(data=request.POST)

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

    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}