import re
import os
import StringIO
import shutil

import netCDF4

from django.dispatch import receiver
from django.core.files.uploadedfile import InMemoryUploadedFile

from hs_core.signals import *
from hs_core.hydroshare.resource import ResourceFile, delete_resource_file_only
from hs_core.hydroshare import utils
from hs_app_netCDF.forms import *
import nc_functions.nc_utils as nc_utils
import nc_functions.nc_dump as nc_dump
import nc_functions.nc_meta as nc_meta


# receiver used to extract metadata after user click on "create resource"
@receiver(pre_create_resource, sender=NetcdfResource)
def netcdf_pre_create_resource(sender, **kwargs):

    files = kwargs['files']
    metadata = kwargs['metadata']
    validate_files_dict = kwargs['validate_files']
    fed_res_fnames = kwargs['fed_res_file_names']

    file_selected = False
    in_file_name = ''

    if files:
        file_selected = True
        in_file_name = files[0].file.name
    elif fed_res_fnames:
        ref_tmpfiles = utils.get_fed_zone_files(fed_res_fnames)
        if ref_tmpfiles:
            in_file_name = ref_tmpfiles[0]
            file_selected = True

    if file_selected and in_file_name:
        # file validation and metadata extraction
        nc_dataset = nc_utils.get_nc_dataset(in_file_name)

        if isinstance(nc_dataset, netCDF4.Dataset):
            # Extract the metadata from netcdf file
            try:
                res_md_dict = nc_meta.get_nc_meta_dict(in_file_name)
                res_dublin_core_meta = res_md_dict['dublin_core_meta']
                res_type_specific_meta = res_md_dict['type_specific_meta']
            except:
                res_dublin_core_meta = {}
                res_type_specific_meta = {}

            # add creator:
            if res_dublin_core_meta.get('creator_name'):
                name = res_dublin_core_meta['creator_name']
                email = res_dublin_core_meta.get('creator_email', '')
                url = res_dublin_core_meta.get('creator_url', '')
                creator = {'creator': {'name': name, 'email': email, 'homepage': url}}
                metadata.append(creator)

            # add contributor:
            if res_dublin_core_meta.get('contributor_name'):
                name_list = res_dublin_core_meta['contributor_name'].split(',')
                for name in name_list:
                    contributor = {'contributor': {'name': name}}
                    metadata.append(contributor)

            # add title
            if res_dublin_core_meta.get('title'):
                res_title = {'title': {'value': res_dublin_core_meta['title']}}
                metadata.append(res_title)

            # add description
            if res_dublin_core_meta.get('description'):
                description = {'description': {'abstract': res_dublin_core_meta['description']}}
                metadata.append(description)

            # add keywords
            if res_dublin_core_meta.get('subject'):
                keywords = res_dublin_core_meta['subject'].split(',')
                for keyword in keywords:
                    metadata.append({'subject': {'value': keyword}})

            # add source
            if res_dublin_core_meta.get('source'):
                source = {'source': {'derived_from': res_dublin_core_meta['source']}}
                metadata.append(source)

            # add relation
            if res_dublin_core_meta.get('references'):
                relation = {'relation': {'type': 'cites',
                                         'value': res_dublin_core_meta['references']}}
                metadata.append(relation)

            # add coverage - period
            if res_dublin_core_meta.get('period'):
                period = {'coverage': {'type': 'period', 'value': res_dublin_core_meta['period']}}
                metadata.append(period)

            # add coverage - box
            if res_dublin_core_meta.get('box'):
                box = {'coverage': {'type': 'box', 'value': res_dublin_core_meta['box']}}
                metadata.append(box)

            # add rights
            if res_dublin_core_meta.get('rights'):
                raw_info = res_dublin_core_meta.get('rights')
                b = re.search("(?P<url>https?://[^\s]+)", raw_info)
                url = b.group('url') if b else ''
                statement = raw_info.replace(url, '') if url else raw_info
                rights = {'rights': {'statement': statement, 'url': url}}
                metadata.append(rights)

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
                    ori_cov = {'originalcoverage': {
                        'value': res_dublin_core_meta['original-box'],
                        'projection_string_type': res_dublin_core_meta['projection-info']['type'],
                        'projection_string_text': res_dublin_core_meta['projection-info']['text'],
                        'datum': res_dublin_core_meta['projection-info']['datum']}
                    }
                else:
                    ori_cov = {'originalcoverage': {'value': res_dublin_core_meta['original-box']}}

                metadata.append(ori_cov)

            # create the ncdump text file
            if nc_dump.get_nc_dump_string_by_ncdump(in_file_name):
                dump_str = nc_dump.get_nc_dump_string_by_ncdump(in_file_name)
            else:
                dump_str = nc_dump.get_nc_dump_string(in_file_name)

            if dump_str:
                # refine dump_str first line
                nc_file_name = os.path.splitext(files[0].name)[0]
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
            validate_files_dict['message'] = 'Please check if the uploaded file ' \
                                             'is in valid NetCDF format.'

        if fed_res_fnames and in_file_name:
            shutil.rmtree(os.path.dirname(in_file_name))


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
#                 dump_file_name = '.'.join(os.path.basename(nc_file_name).split('.')[:-1])
#                                   +'_header_info.txt'
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
    nc_res = kwargs['resource']
    del_file = kwargs['file']
    del_file_ext = utils.get_resource_file_name_and_extension(del_file)[2]

    # update resource modification info
    user = nc_res.creator
    utils.resource_modified(nc_res, user)

    # delete the netcdf header file or .nc file
    file_ext = {'.nc': 'application/x-netcdf',
                '.txt': 'text/plain'}

    if del_file_ext in file_ext:
        del file_ext[del_file_ext]
        for f in ResourceFile.objects.filter(object_id=nc_res.id):
            ext = utils.get_resource_file_name_and_extension(f)[2]
            if ext in file_ext:
                delete_resource_file_only(nc_res, f)
                nc_res.metadata.formats.filter(value=file_ext[ext]).delete()
                break

    # delete all the coverage info
    nc_res.metadata.coverages.all().delete()
    # delete all the extended meta info
    nc_res.metadata.variables.all().delete()
    nc_res.metadata.ori_coverage.all().delete()


# receiver used after user clicks on "add file" for existing resource netcdf file
@receiver(pre_add_files_to_resource, sender=NetcdfResource)
def netcdf_pre_add_files_to_resource(sender, **kwargs):
    nc_res = kwargs['resource']
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']
    fed_res_fnames = kwargs['fed_res_file_names']

    if len(files) > 1:
        # file number validation
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Only one file can be uploaded.'

    file_selected = False
    in_file_name = ''
    if files:
        file_selected = True
        in_file_name = files[0].file.name
    elif fed_res_fnames:
        ref_tmpfiles = utils.get_fed_zone_files(fed_res_fnames)
        if ref_tmpfiles:
            in_file_name = ref_tmpfiles[0]
            file_selected = True

    if file_selected and in_file_name:
        # file type validation and existing metadata update and create new ncdump text file
        nc_dataset = nc_utils.get_nc_dataset(in_file_name)
        if isinstance(nc_dataset, netCDF4.Dataset):
            # delete all existing resource files and metadata related
            for f in ResourceFile.objects.filter(object_id=nc_res.id):
                delete_resource_file_only(nc_res, f)

            # update resource modification info
            user = kwargs['user']
            utils.resource_modified(nc_res, user)

            # extract metadata
            try:
                res_dublin_core_meta = nc_meta.get_dublin_core_meta(nc_dataset)
            except Exception:
                res_dublin_core_meta = {}

            try:
                res_type_specific_meta = nc_meta.get_type_specific_meta(nc_dataset)
            except Exception:
                res_type_specific_meta = {}

            # update title info
            if res_dublin_core_meta.get('title'):
                if nc_res.metadata.title:
                    nc_res.metadata.title.delete()
                nc_res.metadata.create_element('title', value=res_dublin_core_meta['title'])

            # update description info
            if res_dublin_core_meta.get('description'):
                if nc_res.metadata.description:
                    nc_res.metadata.description.delete()
                nc_res.metadata.create_element('description',
                                               abstract=res_dublin_core_meta.get('description'))

            # update creator info
            if res_dublin_core_meta.get('creator_name'):
                name = res_dublin_core_meta.get('creator_name')
                email = res_dublin_core_meta.get('creator_email', '')
                url = res_dublin_core_meta.get('creator_url', '')
                arguments = dict(name=name, email=email, homepage=url)
                creator = nc_res.metadata.creators.all().filter(name=name).first()
                if creator:
                    order = creator.order
                    if order != 1:
                        creator.delete()
                        arguments['order'] = order
                        nc_res.metadata.create_element('creator', **arguments)
                else:
                    nc_res.metadata.create_element('creator', **arguments)

            # update contributor info
            if res_dublin_core_meta.get('contributor_name'):
                name_list = res_dublin_core_meta['contributor_name'].split(',')
                existing_contributor_names = [contributor.name
                                              for contributor in nc_res.metadata.contributors.all()]
                for name in name_list:
                    if name not in existing_contributor_names:
                        nc_res.metadata.create_element('contributor', name=name)

            # update subject info
            if res_dublin_core_meta.get('subject'):
                keywords = res_dublin_core_meta['subject'].split(',')
                existing_keywords = [subject.value for subject in nc_res.metadata.subjects.all()]
                for keyword in keywords:
                    if keyword not in existing_keywords:
                        nc_res.metadata.create_element('subject', value=keyword)

            # update source
            if res_dublin_core_meta.get('source'):
                for source in nc_res.metadata.sources.all():
                    source.delete()
                nc_res.metadata.create_element('source',
                                               derived_from=res_dublin_core_meta.get('source'))

            # update license element:
            if res_dublin_core_meta.get('rights'):
                raw_info = res_dublin_core_meta.get('rights')
                b = re.search("(?P<url>https?://[^\s]+)", raw_info)
                url = b.group('url') if b else ''
                statement = raw_info.replace(url, '') if url else raw_info
                if nc_res.metadata.rights:
                    nc_res.metadata.rights.delete()
                nc_res.metadata.create_element('rights', statement=statement, url=url)

            # update relation
            if res_dublin_core_meta.get('references'):
                for cite in nc_res.metadata.relations.all().filter(type='cites'):
                    cite.delete()
                nc_res.metadata.create_element('relation', type='cites',
                                               value=res_dublin_core_meta['references'])

            # update box info
            nc_res.metadata.coverages.all().delete()
            if res_dublin_core_meta.get('box'):
                nc_res.metadata.create_element('coverage', type='box',
                                               value=res_dublin_core_meta['box'])

            # update period info
            if res_dublin_core_meta.get('period'):
                nc_res.metadata.create_element('coverage', type='period',
                                               value=res_dublin_core_meta['period'])

            # update variable info
            nc_res.metadata.variables.all().delete()
            for var_info in res_type_specific_meta.values():
                nc_res.metadata.create_element('variable',
                                               name=var_info['name'],
                                               unit=var_info['unit'],
                                               type=var_info['type'],
                                               shape=var_info['shape'],
                                               missing_value=var_info['missing_value'],
                                               descriptive_name=var_info['descriptive_name'],
                                               method=var_info['method'])

            # update the original spatial coverage meta
            nc_res.metadata.ori_coverage.all().delete()
            if res_dublin_core_meta.get('original-box'):
                if res_dublin_core_meta.get('projection-info'):
                    nc_res.metadata.create_element(
                        'originalcoverage',
                        value=res_dublin_core_meta['original-box'],
                        projection_string_type=res_dublin_core_meta['projection-info']['type'],
                        projection_string_text=res_dublin_core_meta['projection-info']['text'],
                        datum=res_dublin_core_meta['projection-info']['datum'])
                else:
                    nc_res.metadata.create_element('originalcoverage',
                                                   value=res_dublin_core_meta['original-box'])

            # create the ncdump text file
            if nc_dump.get_nc_dump_string_by_ncdump(in_file_name):
                dump_str = nc_dump.get_nc_dump_string_by_ncdump(in_file_name)
            else:
                dump_str = nc_dump.get_nc_dump_string(in_file_name)

            if dump_str:
                # refine dump_str first line
                nc_file_name = files[0].name[:-3]
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
            validate_files_dict['message'] = 'Please check if the uploaded file is in ' \
                                             'valid NetCDF format.'

        if fed_res_fnames and in_file_name:
            shutil.rmtree(os.path.dirname(in_file_name))

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
#                 dump_file_name = '.'.join(os.path.basename(nc_file_name).split('.')[:-1])
#                                  +'_header_info.txt'
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
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=NetcdfResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
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
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}