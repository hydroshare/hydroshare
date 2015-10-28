import datetime as dt

from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for
from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.signals import *
from django.core import validators, checks
from django.utils import six
from django.utils.encoding import smart_text

# class SeparatedValuesField(models.Field):
#     # description = _("String (up to %(max_length)s)")
#
#     def __init__(self, *args, **kwargs):
#         self.token = kwargs.pop('token', ',')
#         super(SeparatedValuesField, self).__init__(*args, **kwargs)
#         self.validators.append(validators.MaxLengthValidator(self.max_length))
#
#     def check(self, **kwargs):
#         errors = super(SeparatedValuesField, self).check(**kwargs)
#         return errors
#
#     def get_internal_type(self):
#         return "SeparatedValuesField"
#
#     def to_python(self, value):
#         if not value: return
#         if isinstance(value, list):
#             return value
#         return value.split(self.token)
#
#         # if isinstance(value, six.string_types) or value is None:
#         #     return value
#         # return smart_text(value)
#
#     def get_prep_value(self, value):
#         if not value: return
#         assert(isinstance(value, list) or isinstance(value, tuple))
#         return self.token.join([unicode(s) for s in value])
# #         value = super(SeparatedValuesField, self).get_prep_value(value)
# #         return self.to_python(value)
#
#     # def value_to_string(self, obj):
#     #     value = self._get_val_from_obj(obj)
#     #     return self.get_db_prep_value(value)
#
#     # def get_db_prep_value(self, value):
#     #     if not value: return
#     #     assert(isinstance(value, list) or isinstance(value, tuple))
#     #     return self.token.join([unicode(s) for s in value])
#
#     def value_to_string(self, obj):
#         value = self._get_val_from_obj(obj)
#         return self.get_prep_value(value)

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
    modelReleaseNotes = models.CharField(verbose_name="Notes", null=True, blank=True, max_length=400,default='',
                                     help_text="Notes regarding the software release (e.g. bug fixes, new functionality, readme)")
                                     # choices=(('-', '    '),))

    # documentation
    modelDocumentation = models.CharField(verbose_name='Documentation', name="modelDocumentation", null=True,
                                          blank=True, default='',
                                          max_length=400,
                                          help_text='Documentation for the model (e.g. User manuals, theoretical manuals, reports, notes, etc.)')
                                          # choices=(('-', '    '),))

    # software
    modelSoftware = models.CharField(verbose_name='Software', name='modelSoftware', null=True,default='',
                                          blank=True, max_length=400,
                                          help_text='Uploaded archive containing model software (source code, executable, etc.)' )
                                          # choices=(('-', '    '),))





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

    def get_software_list(self):
        return self.modelSoftware.split(';')
    def get_documentation_list(self):
        return self.modelDocumentation.split(';')
    def get_releasenotes_list(self):
        return self.modelReleaseNotes.split(';')


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
        fields = [  'modelSoftware',
                    'modelDocumentation',
                    'modelReleaseNotes',
                    'modelReleaseDate',
                    'modelVersion',
                    'modelWebsite',
                    'modelProgramLanguage',
                    'modelOperatingSystem',
                    'modelCodeRepository',
                    ]

        model_program_object = self.program
        self.add_metadata_element_to_xml(container, model_program_object, fields)

        xml_string = etree.tostring(RDF_ROOT, pretty_print=True)

        return xml_string


import receivers
