__author__ = 'Hong Yi'
## Note: this module has been imported in the models.py in order to receive signals
## at the end of the models.py for the import of this module
from django.dispatch import receiver
from hs_core.signals import *
from forms import *

# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page
@receiver(pre_create_resource, sender=RasterResource)
def raster_pre_create_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        files = kwargs['files']
        title = kwargs['title']

        metadata = kwargs['metadata']
        from collections import OrderedDict
        if(files):
            import raster_meta_extract
            infile = files[0]
            res_md_dict = raster_meta_extract.get_raster_meta_dict(infile.file.name)

            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': wgs_cov_info }}
            metadata.append(box)

            # Save extended meta to metadata variable
            ori_cov = {'OriginalCoverage': {'value': res_md_dict['spatial_coverage_info']['original_coverage_info'] }}
            metadata.append(ori_cov)

            # Save extended meta to metadata variable
            cellInfo = OrderedDict([
                ('name', infile.name),
                ('rows', res_md_dict['cell_and_band_info']['rows']),
                ('columns', res_md_dict['cell_and_band_info']['columns']),
                ('cellSizeXValue', res_md_dict['cell_and_band_info']['cellSizeXValue']),
                ('cellSizeYValue', res_md_dict['cell_and_band_info']['cellSizeYValue']),
                ('cellSizeUnit', res_md_dict['cell_and_band_info']['cellSizeUnit']),
                ('cellDataType', res_md_dict['cell_and_band_info']['cellDataType']),
                ('noDataValue', res_md_dict['cell_and_band_info']['noDataValue'])
                ])
            metadata.append({'CellInformation': cellInfo})
            bcount = res_md_dict['cell_and_band_info']['bandCount']
        else:
            # initialize required raster metadata to be place holders to be edited later by users
            cell_info = OrderedDict([
                ('name', title),
                ('rows', 0),
                ('columns', 0),
                ('cellSizeXValue', 0),
                ('cellSizeYValue', 0),
                ('cellSizeUnit', "NA"),
                ('cellDataType', "NA"),
                ('noDataValue', 0)
            ])
            metadata.append({'CellInformation': cell_info})
            bcount = 1
            spatial_coverage_info = OrderedDict([
                 ('units', "NA"),
                 ('projection', 'NA'),
                 ('northlimit', 'NA'),
                 ('southlimit', 'NA'),
                 ('eastlimit', 'NA'),
                 ('westlimit', 'NA')
            ])
            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': spatial_coverage_info}}
            metadata.append(box)

            # Save extended meta to metadata variable
            ori_cov = {'OriginalCoverage': {'value': spatial_coverage_info }}
            metadata.append(ori_cov)

        for i in range(bcount):
            band_dict = OrderedDict()
            band_dict['name'] = 'Band_' + str(i+1)
            band_dict['variableName'] = 'Unnamed'
            band_dict['variableUnit'] = 'Unnamed'
            band_dict['method'] = ''
            band_dict['comment'] = ''
            metadata.append({'BandInformation': band_dict})

@receiver(pre_add_files_to_resource, sender=RasterResource)
def raster_pre_add_files_to_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        files = kwargs['files']
        res = kwargs['resource']
        if(files):
            infile = files[0]
            import raster_meta_extract
            res_md_dict = raster_meta_extract.get_raster_meta_dict(infile.file.name)

            # update core metadata coverage - box
            #cov_box = res.metadata.coverages.all().filter(type='box').first()
            #res.metadata.update_element('coverage', cov_box.id, type='box', value=res_md_dict['spatial_coverage_info']['wgs84_coverage_info'])

            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            res.metadata.create_element('Coverage', type='box', value=res_md_dict['spatial_coverage_info']['wgs84_coverage_info'])

            # update extended original box coverage
            #ori_cov_box = res.metadata.originalCoverage
            #res.metadata.update_element('OriginalCoverage', ori_cov_box.id, type='box', value=res_md_dict['spatial_coverage_info']['original_coverage_info'])
            if res.metadata.originalCoverage is None:
                v = {'value': res_md_dict['spatial_coverage_info']['original_coverage_info'] }
                res.metadata.create_element('OriginalCoverage', **v)

            # update extended metadata CellInformation
            res.metadata.cellInformation.delete()
            res.metadata.create_element('CellInformation', name=infile.name, rows=res_md_dict['cell_and_band_info']['rows'],
                                        columns = res_md_dict['cell_and_band_info']['columns'],
                                        cellSizeXValue = res_md_dict['cell_and_band_info']['cellSizeXValue'],
                                        cellSizeYValue = res_md_dict['cell_and_band_info']['cellSizeYValue'],
                                        cellSizeUnit = res_md_dict['cell_and_band_info']['cellSizeUnit'],
                                        cellDataType = res_md_dict['cell_and_band_info']['cellDataType'],
                                        noDataValue = res_md_dict['cell_and_band_info']['noDataValue'])

            bcount = res_md_dict['cell_and_band_info']['bandCount']

            # update extended metadata BandInformation
            for band in res.metadata.bandInformation:
                band.delete()
            for i in range(bcount):
                res.metadata.create_element('BandInformation', name='Band_' + str(i+1), variableName='Unnamed', variableUnit='Unnamed', method='', comment='')

@receiver(pre_delete_file_from_resource, sender=RasterResource)
def raster_pre_delete_file_from_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        res = kwargs['resource']

        #cov_box = res.metadata.coverages.all().filter(type='box').first()
        # from collections import OrderedDict
        # spatial_coverage_info = OrderedDict([
        #         ('units', "NA"),
        #         ('projection', 'NA'),
        #         ('northlimit', 0),
        #         ('southlimit', 0),
        #         ('eastlimit', 0),
        #         ('westlimit', 0)
        #     ])
        # reset core metadata coverage - box to be null now that the only file is deleted
        #res.metadata.update_element('coverage', cov_box.id, type='box', value=spatial_coverage_info)

        #ori_cov_box = res.metadata.originalCoverage
        #reset extended OriginalCoverage now that the only file is deleted
        #res.metadata.update_element('OriginalCoverage', ori_cov_box.id, value=spatial_coverage_info)

        #delete core metadata coverage now that the only file is deleted
        res.metadata.coverages.all().delete()

        #delete extended OriginalCoverage now that the only file is deleted
        res.metadata.originalCoverage.delete()

        # reset extended metadata CellInformation now that the only file is deleted
        res.metadata.cellInformation.delete()
        res.metadata.create_element('CellInformation', name=res.title, rows=0, columns = 0,
                                        cellSizeXValue = 0, cellSizeYValue = 0,
                                        cellSizeUnit = "NA",
                                        cellDataType = "NA",
                                        noDataValue = 0)

        # reset extended metadata BandInformation now that the only file is deleted
        for band in res.metadata.bandInformation:
            band.delete()
        res.metadata.create_element('BandInformation', name='Band_1', variableName='Unnamed', variableUnit='Unnamed', method='', comment='')

@receiver(pre_metadata_element_create, sender=RasterResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        element_form = BandInfoValidationForm(request.POST)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

@receiver(pre_metadata_element_update, sender=RasterResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        form_data = {}
        for field_name in BandInfoValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]
        element_form = BandInfoValidationForm(form_data)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}
"""
Since each of the Raster metadata element is required no need to listen to any delete signal
The Raster landing page should not have delete UI functionality for the resource specific metadata elements
"""