from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement
import datetime as dt
from mezzanine.pages.page_processors import processor_for
from hs_core.signals import *
from django.dispatch import receiver


class MpMetadata(AbstractMetaDataElement):

    # version
    software_version = models.CharField(verbose_name='Software Version ',null=True,blank=True,default='1.0',max_length=255,help_text='The software version of the model program')

    # program language
    software_language = models.CharField(verbose_name="Software Language", null=True,default='',max_length=100,help_text="The programming language that the model program was written in")

    # operating system
    operating_sys = models.CharField(verbose_name='Operating System',null=True,blank=True,default='unknown',max_length=255, help_text='Identify the operating system used by the model program')

    # release date
    date_released = models.DateTimeField(verbose_name='Date of Software Release',null=True, default=dt.datetime.now(), help_text='The date of the software release (mm/dd/yyyy hh:mm)')

    # web page
    program_website = models.CharField(verbose_name='Model Website', null=True, default= None, max_length=255,help_text='A URL providing addition information about the software')

    # repository
    software_repo = models.CharField(verbose_name='Software Repository', null=True, default= None, max_length=255,help_text='A URL for the source code repository')

   # release notes
    release_notes = models.CharField(verbose_name="Release Notes", null=True,default="",max_length=400, help_text="Notes about the software release (e.g. bug fixes, new functionality)", choices=(('-','    '),))

    # user manual
    user_manual = models.CharField(verbose_name='User Manual',name='user_manual', null=True, default=None,max_length=400, help_text='User manual for the model program (e.g. .doc, .md, .rtf, .pdf', choices=(('-','    '),))

    # theoretical manual
    theoretical_manual = models.CharField(verbose_name='Theoretical Manual',name='theoretical_manual', null=True, default=None, max_length=400, help_text='Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf', choices=(('-','    '),))

    # source code
    source_code = models.CharField(verbose_name='Model Source Code',name='source_code', default=None, null=True,max_length=400, help_text='Upload Model Source Code as *.ZIP', choices=(('-','    '),))


    @classmethod
    def create(cls, **kwargs):

       # todo: add validation

        mpmetadata = MpMetadata.objects.create(**kwargs)

        return mpmetadata


    @classmethod
    def update(cls, element_id, **kwargs):


        metadata = MpMetadata.objects.get(id=element_id)

        #todo: validate

        metadata.software_version = kwargs['software_version']
        metadata.software_language = kwargs['software_language']
        metadata.operating_sys = kwargs['operating_sys']
        metadata.date_released = kwargs['date_released']
        metadata.program_website = kwargs['program_website']
        metadata.software_repo = kwargs['software_repo']
        metadata.release_notes = kwargs['release_notes']
        metadata.user_manual = kwargs['user_manual']
        metadata.theoretical_manual = kwargs['theoretical_manual']
        metadata.source_code = kwargs['source_code']
        metadata.save()



    # @classmethod
    # def remove(cls, element_id):
    #     metadata = MpMetadata.objects.get(id=element_id)
    #     metadata.delete()


class ModelProgramResource(Page, AbstractResource):

    @property
    def metadata(self):
        md = ModelProgramMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

    class Meta:
        verbose_name = 'Model Program Resource'



processor_for(ModelProgramResource)(resource_processor)



class ModelProgramMetaData(CoreMetaData):
    mpmetadata = generic.GenericRelation(MpMetadata)
    _mp_resource = generic.GenericRelation(ModelProgramResource)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelProgramMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('mpmetadata')
        return elements

    @property
    def resource(self):
        return self._mp_resource.all().first()

import recievers