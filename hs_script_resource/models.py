from django.db import models
from django.contrib.contenttypes import generic

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement

from lxml import etree

class ScriptResource(BaseResource):
    objects = ResourceManager('ScriptResource')

    class Meta:
        proxy = True
        verbose_name = 'Script Resource'

    @classmethod
    def get_supported_upload_file_types(cls):
        # one file type is supported
        return ".r", ".py", ".m"

    @classmethod
    def can_have_multiple_files(cls):
        # can have multiple files
        return True

    @property
    def metadata(self):
        md = ScriptMetaData()
        return self._get_metadata(md)

processor_for(ScriptResource)(resource_processor)


class ScriptSpecificMetadata(AbstractMetaDataElement):
    term = "ScriptSpecificMetadata"

    # program language
    scriptLanguage = models.CharField(verbose_name='Programming Language', blank=True, max_length=100, default='R',
                                      help_text='The programming language that the script is written in')

    # language version
    languageVersion = models.CharField(verbose_name='Programming Language Version', blank=True, max_length=255,
                                       help_text='The software version of the script')

    # script version
    scriptVersion = models.CharField(verbose_name='Script Version', max_length=255, blank=True, default='1.0',
                                     help_text='The software version or build number of the script')

    # dependencies
    scriptDependencies = models.CharField(verbose_name='Dependencies', blank=True, max_length=400,
                                          help_text='Dependencies for the script (externally-imported packages)')

    # release date
    scriptReleaseDate = models.DateTimeField(verbose_name='Release Date', null=True, blank=True,
                                             help_text='The date that this version of the script was released')

    # repository
    scriptCodeRepository = models.CharField(verbose_name='Script Repository', blank=True, max_length=255,
                                            help_text='A URL to the source code repository (e.g. git, mercurial, svn)')

    class Meta:
        # ScriptSpecificMetadata element is not repeatable
        unique_together = ("content_type", "object_id")


class ScriptMetaData(CoreMetaData):
    scriptspecificmetadata = generic.GenericRelation(ScriptSpecificMetadata)

    @property
    def program(self):
        return self.scriptspecificmetadata.all().first()

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ScriptMetaData, cls).get_supported_element_names()
        elements.append('ScriptSpecificMetadata')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(ScriptMetaData, self).get_required_missing_elements()
        if not self.program:
            missing_required_elements.append('Script Language')
            missing_required_elements.append('Programming Language Version')
        else:
            if not self.program.scriptLanguage:
                missing_required_elements.append('Script Language')
            if not self.program.languageVersion:
                missing_required_elements.append('Programming Language Version')

        return missing_required_elements

    def get_xml(self):

        # get the xml string for R Script
        xml_string = super(ScriptMetaData, self).get_xml(pretty_print=False)

        # create  etree element
        RDF_ROOT = etree.fromstring(xml_string)

        # get the root 'Description' element, which contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.program:

            if self.program.scriptReleaseDate:
                script_release_date = etree.SubElement(container, '{%s}scriptReleaseDate' % self.NAMESPACES['hsterms'])
                script_release_date.text = self.program.scriptReleaseDate.isoformat()

            script_language = etree.SubElement(container, '{%s}scriptLanguage' % self.NAMESPACES['hsterms'])
            script_language.text = self.program.scriptLanguage

            language_version = etree.SubElement(container, '{%s}languageVersion' % self.NAMESPACES['hsterms'])
            language_version.text = self.program.scriptVersion

            script_version = etree.SubElement(container, '{%s}scriptVersion' % self.NAMESPACES['hsterms'])
            script_version.text = self.program.scriptVersion

            script_dependencies = etree.SubElement(container, '{%s}scriptDependencies' % self.NAMESPACES['hsterms'])
            script_dependencies.text = self.program.scriptVersion

            script_code_repository = etree.SubElement(container, '{%s}scriptCodeRepository' % self.NAMESPACES['hsterms'])
            script_code_repository.text = self.program.scriptCodeRepository

        xml_string = etree.tostring(RDF_ROOT, pretty_print=True)

        return xml_string

import receivers # never delete this otherwise none of the receiver function will work
