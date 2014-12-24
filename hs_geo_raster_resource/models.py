from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page
from mezzanine.core.models import Ownable
from hs_core.models import AbstractResource, resource_processor
from django.shortcuts import get_object_or_404
import django.dispatch
from mezzanine.pages.page_processors import processor_for
from django.utils.timezone import now
import cStringIO as StringIO
import os

class RasterBand(models.Model):
    bandName = models.CharField(max_length=50, null=True)
    variableName = models.CharField(max_length=50, null=True)
    variableUnit = models.CharField(max_length=50, null=True)
    method = models.CharField(max_length=100, null=True)
    comment = models.TextField(null=True)

#
# To create a new resource, use these two super-classes.
#
class RasterResource(Page, AbstractResource):
    class Meta:
        verbose_name = 'Geographic Raster Resource'
    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellSizeUnit = models.CharField(max_length=50, null=True)
    cellDataType = models.CharField(max_length=50, null=True)
    cellNoDataValue = models.FloatField(null=True)
    bandCount =models.IntegerField(null=True)
    bands = models.ManyToManyField(RasterBand,
                                    related_name='bands_of_raster',
                                    help_text='All band info of the raster resource'
    )
    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

processor_for(RasterResource)(resource_processor)
# page processor to populate raster resource specific metadata into my-resources template page
@processor_for(RasterResource)
def main_page(request, page):
    from dublincore import models as dc
    from django import forms
    from collections import OrderedDict
    class DCTerm(forms.ModelForm):
        class Meta:
            model=dc.QualifiedDublinCoreElement
            fields = ['term', 'content']

    content_model = page.get_content_model()

    # create Coverage metadata
    md_dict = OrderedDict()

    md_dict['rows'] = content_model.rows
    md_dict['columns'] = content_model.columns
    md_dict['cellSizeXValue'] = content_model.cellSizeXValue
    md_dict['cellSizeYValue'] = content_model.cellSizeYValue
    md_dict['cellSizeUnit'] = content_model.cellSizeUnit
    md_dict['cellDataType'] = content_model.cellDataType
    md_dict['cellNoDataValue'] = content_model.cellNoDataValue
    md_dict['bandCount'] = content_model.bandCount

    i = 1
    for band in content_model.bands.all():
        md_dict['bandName_'+str(i)] = band.bandName
        md_dict['variableName_'+str(i)] = band.variableName
        md_dict['variableUnit_'+str(i)] = band.variableUnit
        md_dict['method_'+str(i)] = band.method
        md_dict['comment_'+str(i)] = band.comment
        i = i+1
    cvg = content_model.metadata.coverages.all()
    core_md = {}
    if cvg:
        coverage = cvg[0]
        core_md = OrderedDict()
        core_md['name'] = coverage.value['name']
        core_md['northLimit'] = coverage.value['northlimit']
        core_md['eastLimit'] = coverage.value['eastlimit']
        core_md['southLimit'] = coverage.value['southlimit']
        core_md['westLimit'] = coverage.value['westlimit']

        core_md_dict = {'Coverage': core_md}
        return  { 'res_add_metadata': md_dict,
                  'resource_type' : content_model._meta.verbose_name,
                  'dublin_core' : [t for t in content_model.dublin_metadata.all().exclude(term='AB')],
                  'core_metadata' : core_md_dict,
                  'dcterm_frm' : DCTerm()
                }
    else:
        return  { 'res_add_metadata': md_dict,
                  'resource_type' : content_model._meta.verbose_name,
                  'dublin_core' : [t for t in content_model.dublin_metadata.all().exclude(term='AB')],
                  'dcterm_frm' : DCTerm()
                }
import receivers
