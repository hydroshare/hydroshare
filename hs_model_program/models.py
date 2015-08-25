import datetime as dt

from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.signals import *


class MpMetadata(AbstractMetaDataElement):
    term = "MpMetadata"

    # version
    software_version = models.CharField(verbose_name='Version ', null=True, blank=True, max_length=255, default='',
                                        help_text='The software version of the model')

    # program language
    software_language = models.CharField(verbose_name="Language", null=True, blank=True, max_length=100,default='',
                                         help_text="The programming language(s) that the model was written in")

    # operating system
    operating_sys = models.CharField(verbose_name='Operating System', null=True, blank=True,default='',
                                     max_length=255, help_text='Compatible operating systems')

    # release date
    date_released = models.DateTimeField(verbose_name='Release Date', null=True, blank=True,
                                         help_text='The date of the software release (m/d/Y H:M)')

    # web page
    program_website = models.CharField(verbose_name='Website', null=True, blank=True, max_length=255,default='',
                                       help_text='A URL providing addition information about the software')

    # repository
    software_repo = models.CharField(verbose_name='Software Repository', null=True, blank=True,default='',
                                     max_length=255,
                                     help_text='A URL for the source code repository (e.g. git, mecurial, svn)')

    # release notes
    release_notes = models.CharField(verbose_name="Release Notes", null=True, blank=True, max_length=400,default='',
                                     help_text="Notes about the software release (e.g. bug fixes, new functionality)",
                                     choices=(('-', '    '),))

    # user manual
    user_manual = models.CharField(verbose_name='User Manual', name='user_manual', null=True, blank=True,default='',
                                   max_length=400,
                                   help_text='User manual for the model program (e.g. .doc, .md, .rtf, .pdf',
                                   choices=(('-', '    '),))

    # theoretical manual
    theoretical_manual = models.CharField(verbose_name='Theoretical Manual', name='theoretical_manual', null=True,default='',
                                          blank=True, max_length=400,
                                          help_text='Theoretical manual for the model program (e.g. .doc, .md, .rtf, .pdf',
                                          choices=(('-', '    '),))

    # source code
    source_code = models.CharField(verbose_name='Source Code', name='source_code', null=True, blank=True,default='',
                                   max_length=400,
                                   help_text='Archive of the  source code for the model (e.g. .zip, .tar)',
                                   choices=(('-', '    '),))
    def __unicode__(self):
        self.software_version

    class Meta:
        # site element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return MpMetadata.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        metadata = MpMetadata.objects.get(id=element_id)
        if metadata:
            for key, value in kwargs.iteritems():
                setattr(metadata, key, value)
            metadata.save()
        else:
            raise ObjectDoesNotExist("No Site element was found for the provided id:%s" % kwargs['id'])


    @classmethod
    def remove(cls, element_id):
        metadata = MpMetadata.objects.get(id=element_id)
        metadata.delete()


class ModelProgramResource(BaseResource):
    objects = ResourceManager()

    class Meta:
        verbose_name = 'Model Program Resource'
        proxy = True

    @property
    def metadata(self):
        md = ModelProgramMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return super(ModelProgramResource, self).can_add(self, request)

    def can_change(self, request):
        return super(ModelProgramResource, self).can_change(self, request)

    def can_delete(self, request):
        return super(ModelProgramResource, self).can_delete(self, request)

    def can_view(self, request):
        return super(ModelProgramResource, self).can_view(self, request)

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

processor_for(ModelProgramResource)(resource_processor)


class ModelProgramMetaData(CoreMetaData):
    _mpmetadata = generic.GenericRelation(MpMetadata)

    @property
    def program(self):
        return self._mpmetadata.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelProgramMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('MpMetadata')
        return elements

    def has_all_required_elements(self):
        if not super(ModelProgramMetaData, self).has_all_required_elements():
            return False
        if not self.program:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(ModelProgramMetaData, self).get_required_missing_elements()
        if not self.program:
            missing_required_elements.append('MpMetadata')
        return missing_required_elements

    def get_xml(self):
        from lxml import etree

        # get the xml string for Model Program
        xml_string = super(ModelProgramMetaData, self).get_xml(pretty_print=False)

        # create  etree element
        RDF_ROOT = etree.fromstring(xml_string)

        # get the root 'Description' element, which contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject raster resource specific metadata elements into container element
        fields = ['software_version',
                  'software_language',
                  'operating_sys',
                  'date_released',
                  'program_website',
                  'software_repo',
                  'release_notes',
                  'user_manual',
                  'theoretical_manual',
                  'source_code']

        model_program_object = self.program
        self.add_metadata_element_to_xml(container, model_program_object, fields)

        xml_string = etree.tostring(RDF_ROOT, pretty_print=True)

        return xml_string


import receivers
