from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for
from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.signals import *
from lxml import etree

class MpMetadata(AbstractMetaDataElement):
    term = "MpMetadata"

    # version
    modelVersion = models.CharField(verbose_name='Version', null=True, blank=True, max_length=255, default='',
                                        help_text='The software version or build number of the model')

    # program language
    modelProgramLanguage = models.CharField(verbose_name="Language", null=True, blank=True, max_length=100,default='',
                                         help_text="The programming language(s) that the model is written in")

    # operating system
    modelOperatingSystem = models.CharField(verbose_name='Operating System', null=True, blank=True,default='',
                                     max_length=255, help_text='Compatible operating systems to setup and run the model')

    # release date
    modelReleaseDate = models.DateTimeField(verbose_name='Release Date', null=True, blank=True,
                                         help_text='The date that this version of the model was released')

    # web page
    modelWebsite = models.CharField(verbose_name='Website', null=True, blank=True, max_length=255,default='',
                                       help_text='A URL to the website maintained by the model developers')

    # repository
    modelCodeRepository = models.CharField(verbose_name='Software Repository', null=True, blank=True,default='',
                                     max_length=255,
                                     help_text='A URL to the source code repository (e.g. git, mercurial, svn)')

    # release notes
    modelReleaseNotes = models.CharField(verbose_name="Release Notes", null=True, blank=True, max_length=400,default='',
                                     help_text="Notes regarding the software release (e.g. bug fixes, new functionality, readme)")

    # documentation
    modelDocumentation = models.CharField(verbose_name='Documentation', name="modelDocumentation", null=True,
                                          blank=True, default='',
                                          max_length=400,
                                          help_text='Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)')

    # software
    modelSoftware = models.CharField(verbose_name='Software', name='modelSoftware', null=True,default='',
                                          blank=True, max_length=400,
                                          help_text='Uploaded archive containing model software (e.g., utilities software, etc.)' )

    # software engine
    modelEngine = models.CharField(verbose_name='Computational Engine', name='modelEngine', null=True,default='',
                                          blank=True, max_length=400,
                                          help_text='Uploaded archive containing model software (source code, executable, etc.)' )



    def __unicode__(self):
        self.modelVersion

    @classmethod
    def remove(cls, element_id):
        metadata = MpMetadata.objects.get(id=element_id)
        metadata.delete()

    def get_software_list(self):
        return {name:path for (name, path) in [(i.split('/')[-1], i) for i in self.modelSoftware.split(';')]}
    def get_documentation_list(self):
        return {name:path for (name, path) in [(i.split('/')[-1], i) for i in self.modelDocumentation.split(';')]}
    def get_releasenotes_list(self):
        return {name:path for (name, path) in [(i.split('/')[-1], i) for i in self.modelReleaseNotes.split(';')]}
    def get_engine_list(self):
        return {name:path for (name, path) in [(i.split('/')[-1], i) for i in self.modelEngine.split(';')]}


class ModelProgramResource(BaseResource):
    objects = ResourceManager("ModelProgramResource")

    class Meta:
        verbose_name = 'Model Program Resource'
        proxy = True

    @property
    def metadata(self):
        md = ModelProgramMetaData()
        meta = self._get_metadata(md)
        return meta

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

processor_for(ModelProgramResource)(resource_processor)


class ModelProgramMetaData(CoreMetaData):
    _mpmetadata = GenericRelation(MpMetadata)

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

    def get_xml(self):


        # get the xml string for Model Program
        xml_string = super(ModelProgramMetaData, self).get_xml(pretty_print=False)

        # create  etree element
        RDF_ROOT = etree.fromstring(xml_string)

        # get the root 'Description' element, which contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.program:
            self.build_xml_for_uploaded_content(container, 'modelEngine', self.program.modelEngine.split(';'))
            self.build_xml_for_uploaded_content(container, 'modelSoftware', self.program.modelSoftware.split(';'))
            self.build_xml_for_uploaded_content(container, 'modelDocumentation', self.program.modelDocumentation.split(';'))
            self.build_xml_for_uploaded_content(container, 'modelReleaseNotes', self.program.modelReleaseNotes.split(';'))

            if self.program.modelReleaseDate:
                model_release_date = etree.SubElement(container, '{%s}modelReleaseDate' % self.NAMESPACES['hsterms'])
                model_release_date.text = self.program.modelReleaseDate.isoformat()

            model_version = etree.SubElement(container, '{%s}modelVersion' % self.NAMESPACES['hsterms'])
            model_version.text = self.program.modelVersion

            model_website = etree.SubElement(container, '{%s}modelWebsite' % self.NAMESPACES['hsterms'])
            model_website.text = self.program.modelWebsite

            model_program_language = etree.SubElement(container, '{%s}modelProgramLanguage' % self.NAMESPACES['hsterms'])
            model_program_language.text = self.program.modelProgramLanguage

            model_operating_system = etree.SubElement(container, '{%s}modelOperatingSystem' % self.NAMESPACES['hsterms'])
            model_operating_system.text = self.program.modelOperatingSystem

            model_code_repository = etree.SubElement(container, '{%s}modelCodeRepository' % self.NAMESPACES['hsterms'])
            model_code_repository.text = self.program.modelCodeRepository


        xml_string = etree.tostring(RDF_ROOT, pretty_print=True)

        return xml_string

    def build_xml_for_uploaded_content(self, parent_container, element_name, content_list):
        # create an XML element for each content file
        for content in content_list:
            element = etree.SubElement(parent_container, '{%s}%s' % (self.NAMESPACES['hsterms'], element_name) )
            element.text = content
    


import receivers
