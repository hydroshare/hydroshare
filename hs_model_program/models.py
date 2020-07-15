from dateutil import parser

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for
from rdflib import Literal, URIRef

from hs_core.hs_rdf import rdf_terms
from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement

from lxml import etree


@rdf_terms(None)
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

    def rdf_triples(self, subject, graph):
        for field in self._meta.fields:
            if self.ignored_fields and field.name in self.ignored_fields:
                continue
            field_value = getattr(self, field.name)
            if not field_value:
                continue
            if field.name in ['modelEngine', 'modelReleaseNotes', 'modelDocumentation', 'modelSoftware']:
                field_term = self.get_field_term(field.name)
                for f in field_value.split(';'):
                    graph.add((subject, field_term, Literal('/data/contents/' + f)))
            else:
                field_term = self.get_field_term(field.name)
                # urls should be a URIRef term, all others should be a Literal term
                if field_value and field_value != 'None':
                    if isinstance(field_value, str) and field_value.startswith('http'):
                        field_value = URIRef(field_value)
                    else:
                        field_value = Literal(field_value)
                    graph.add((subject, field_term, field_value))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for field in cls._meta.fields:
            field_term = cls.get_field_term(field.name)
            value_dict = {}
            if cls.ignored_fields and field.name in cls.ignored_fields:
                continue
            if field.name in ['modelEngine', 'modelReleaseNotes', 'modelDocumentation', 'modelSoftware']:
                values = []
                for o in graph.objects(subject=subject, predicate=field_term):
                    values.append(o.lstrip('/data/contents/'))
                value_dict[field.name] = ';'.join(values)
            else:
                val = graph.value(subject, field_term)
                if val:
                    value_dict[field.name] = str(val)
        if value_dict:
            cls.create(content_object=content_object, **value_dict)


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
        from .serializers import ModelProgramMetaDataSerializer
        return ModelProgramMetaDataSerializer(self)

    @property
    def program(self):
        return self._mpmetadata.all().first()

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = list(metadata.keys())
        if 'mpmetadata' in keys_to_update:
            parsed_metadata.append({"mpmetadata": metadata.pop('mpmetadata')})

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelProgramMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('MpMetadata')
        return elements

    def delete_all_elements(self):
        super(ModelProgramMetaData, self).delete_all_elements()
        self._mpmetadata.all().delete()

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from .forms import ModelProgramMetadataValidationForm

        super(ModelProgramMetaData, self).update(metadata, user)
        attribute_mappings = {'mpmetadata': 'program'}
        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in list(attribute_mappings.keys()):
                for dict_item in metadata:
                    if element_name in dict_item:
                        if 'modelReleaseDate' in dict_item[element_name]:
                            release_date = dict_item[element_name]['modelReleaseDate']
                            if isinstance(release_date, str):
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

    def build_xml_for_uploaded_content(self, parent_container, element_name, content_list):
        # create an XML element for each content file
        for content in content_list:
            content = '/data/contents/' + content
            element = etree.SubElement(parent_container, '{%s}%s' % (self.NAMESPACES['hsterms'], element_name) )
            element.text = content
    


from . import receivers
