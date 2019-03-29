from dateutil import parser

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement

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
        return self.modelSoftware.split(';')

    def get_documentation_list(self):
        return self.modelDocumentation.split(';')

    def get_releasenotes_list(self):
        return self.modelReleaseNotes.split(';')

    def get_engine_list(self):
        return self.modelEngine.split(';')


class ModelProgramResource(BaseResource):
    objects = ResourceManager("ModelProgramResource")

    discovery_content_type = 'Model Program'  # used during discovery

    class Meta:
        verbose_name = 'Model Program Resource'
        proxy = True

    @classmethod
    def get_metadata_class(cls):
        return ModelProgramMetaData

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

processor_for(ModelProgramResource)(resource_processor)


class ModelProgramMetaData(CoreMetaData):
    _mpmetadata = GenericRelation(MpMetadata)

    @property
    def resource(self):
        return ModelProgramResource.objects.filter(object_id=self.id).first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import ModelProgramMetaDataSerializer
        return ModelProgramMetaDataSerializer(self)

    @property
    def program(self):
        return self._mpmetadata.all().first()

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'mpmetadata' in keys_to_update:
            parsed_metadata.append({"mpmetadata": metadata.pop('mpmetadata')})

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelProgramMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('MpMetadata')
        return elements

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from forms import ModelProgramMetadataValidationForm

        super(ModelProgramMetaData, self).update(metadata, user)
        attribute_mappings = {'mpmetadata': 'program'}
        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in attribute_mappings.keys():
                for dict_item in metadata:
                    if element_name in dict_item:
                        if 'modelReleaseDate' in dict_item[element_name]:
                            release_date = dict_item[element_name]['modelReleaseDate']
                            if isinstance(release_date, basestring):
                                try:
                                    release_date = parser.parse(release_date)
                                except ValueError:
                                    raise ValidationError("Invalid modelReleaseDate")
                                dict_item[element_name]['modelReleaseDate'] = release_date
                        validation_form = ModelProgramMetadataValidationForm(
                            dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                    element_property_name = attribute_mappings[element_name]
                    self.update_non_repeatable_element(element_name, metadata,
                                                       element_property_name)
                    break

    def get_xml(self, pretty_print=True, include_format_elements=True):


        # get the xml string for Model Program
        xml_string = super(ModelProgramMetaData, self).get_xml(pretty_print=pretty_print)

        # create  etree element
        RDF_ROOT = etree.fromstring(xml_string)

        # get the root 'Description' element, which contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.program:
            self.build_xml_for_uploaded_content(container, 'modelEngine', self.program.get_engine_list())
            self.build_xml_for_uploaded_content(container, 'modelSoftware', self.program.get_software_list())
            self.build_xml_for_uploaded_content(container, 'modelDocumentation', self.program.get_documentation_list())
            self.build_xml_for_uploaded_content(container, 'modelReleaseNotes', self.program.get_releasenotes_list())

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

        xml_string = etree.tostring(RDF_ROOT, pretty_print=pretty_print)

        return xml_string

    def build_xml_for_uploaded_content(self, parent_container, element_name, content_list):
        # create an XML element for each content file
        for content in content_list:
            content = '/data/contents/' + content
            element = etree.SubElement(parent_container, '{%s}%s' % (self.NAMESPACES['hsterms'], element_name) )
            element.text = content
    


import receivers
