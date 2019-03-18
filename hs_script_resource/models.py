from lxml import etree

from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement


# TODO Deprecated
class ScriptResource(BaseResource):
    objects = ResourceManager('ScriptResource')

    discovery_content_type = 'Script'  # used during discovery

    class Meta:
        proxy = True
        verbose_name = 'Script Resource'

    @classmethod
    def get_supported_upload_file_types(cls):
        # one file type is supported
        return ".r", ".py", ".m"

    @classmethod
    def get_metadata_class(cls):
        return ScriptMetaData


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
    scriptCodeRepository = models.URLField(verbose_name='Script Repository', blank=True, max_length=255,
                                            help_text='A URL to the source code repository (e.g. git, mercurial, svn)')

    class Meta:
        # ScriptSpecificMetadata element is not repeatable
        unique_together = ("content_type", "object_id")


class ScriptMetaData(CoreMetaData):
    scriptspecificmetadata = GenericRelation(ScriptSpecificMetadata)

    @property
    def resource(self):
        return ScriptResource.objects.filter(object_id=self.id).first()

    @property
    def program(self):
        return self.scriptspecificmetadata.all().first()

    @property
    def script_specific_metadata(self):
        return self.program

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import ScriptMetaDataSerializer
        return ScriptMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'scriptspecificmetadata' in keys_to_update:
            parsed_metadata.append({"scriptspecificmetadata":
                                    metadata.pop('scriptspecificmetadata')})

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

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from forms import ScriptFormValidation

        super(ScriptMetaData, self).update(metadata, user)
        attribute_mappings = {'scriptspecificmetadata': 'program'}
        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in attribute_mappings.keys():
                for dict_item in metadata:
                    if element_name in dict_item:
                        validation_form = ScriptFormValidation(dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                        element_property_name = attribute_mappings[element_name]
                        self.update_non_repeatable_element(element_name, metadata,
                                                           element_property_name)
                        break

    def get_xml(self, pretty_print=True, include_format_elements=True):

        # get the xml string for R Script
        xml_string = super(ScriptMetaData, self).get_xml(pretty_print=pretty_print)

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

        xml_string = etree.tostring(RDF_ROOT, pretty_print=pretty_print)

        return xml_string

import receivers # never delete this otherwise none of the receiver function will work
