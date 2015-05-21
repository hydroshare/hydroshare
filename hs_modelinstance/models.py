from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.db import models
from django.contrib.sites.models import get_current_site
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for

from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_model_program.models import ModelProgramResource
from hs_core.signals import *



# extended metadata elements for Model Instance resource type
class ModelOutput(AbstractMetaDataElement):
    term = 'ModelOutput'
    includes_output = models.BooleanField(default=False)

    @classmethod
    def create(cls, **kwargs):
        return ModelOutput.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_output = ModelOutput.objects.get(id=element_id)
        if model_output:
            for key, value in kwargs.iteritems():
                setattr(model_output, key, value)

            model_output.save()
        else:
            raise ObjectDoesNotExist("No ModelOutput element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelOutput element of a resource can't be deleted.")


class ExecutedBy(AbstractMetaDataElement):
    term = 'ExecutedBY'
    model_name = models.CharField(max_length=500, choices=(('-', '    '),))
    model_program_fk = models.ForeignKey('hs_model_program.ModelProgramResource', null=True, blank=True)


    def __unicode__(self):
        self.model_name

    @classmethod
    def create(cls, **kwargs):
        shortid = kwargs['model_name']

        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()

        kwargs['model_program_fk'] = obj
        metadata_obj = kwargs['content_object']
        title = obj.title
        mp_fk = ExecutedBy.objects.create(model_program_fk=obj,
                                          model_name=title,
                                          content_object=metadata_obj)

        return mp_fk


    @classmethod
    def update(cls, element_id, **kwargs):
        shortid = kwargs['model_name']

        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()

        kwargs['model_program_fk'] = obj

        executed_by = ExecutedBy.objects.get(id=element_id)
        if executed_by:
            for key, value in kwargs.iteritems():
                setattr(executed_by, key, value)

            executed_by.save()

        else:
            raise ObjectDoesNotExist("No ExecutedBy element was found for the provided id:%s" % kwargs['id'])


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ExecutedBy element of a resource can't be deleted.")


# Model Instance Resource type
class ModelInstanceResource(Page, AbstractResource):
    class Meta:
        verbose_name = 'Model Instance Resource'


    @property
    def metadata(self):
        md = ModelInstanceMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)


processor_for(ModelInstanceResource)(resource_processor)

# metadata container class
class ModelInstanceMetaData(CoreMetaData):
    _model_output = generic.GenericRelation(ModelOutput)
    _executed_by = generic.GenericRelation(ExecutedBy)

    @property
    def model_output(self):
        return self._model_output.all().first()

    @property
    def executed_by(self):
        return self._executed_by.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('ModelOutput')
        elements.append('ExecutedBy')
        return elements

    def has_all_required_elements(self):
        if not super(ModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_output:
            return False
        if not self.executed_by:
            return False

        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(ModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_output:
            missing_required_elements.append('ModelOutput')
        if not self.executed_by:
            missing_required_elements.append('ExecutedBy')
        return missing_required_elements

    def get_xml(self, pretty_print=True):
        from lxml import etree

        # get the xml string representation of the core metadata elements
        xml_string = super(ModelInstanceMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_output:
            hsterms_model_output = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_model_output_rdf_Description = etree.SubElement(hsterms_model_output,
                                                                    '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_output_value = etree.SubElement(hsterms_model_output_rdf_Description,
                                                          '{%s}IncludesModelOutput' % self.NAMESPACES['hsterms'])
            if self.model_output.includes_output == True:
                hsterms_model_output_value.text = "Yes"
            else:
                hsterms_model_output_value.text = "No"
        if self.executed_by:
            hsterms_executed_by = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_rdf_Description = etree.SubElement(hsterms_executed_by,
                                                                   '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_executed_by_name = etree.SubElement(hsterms_executed_by_rdf_Description,
                                                        '{%s}ModelProgramName' % self.NAMESPACES['hsterms'])

            title = self.executed_by.model_program_fk.title if self.executed_by.model_program_fk else "Unknown"
            hsterms_executed_by_name.text = title

            hsterms_executed_by_url = etree.SubElement(hsterms_executed_by_rdf_Description,
                                                       '{%s}ModelProgramURL' % self.NAMESPACES['hsterms'])

            url = 'http://%s%s' % (get_current_site(None).domain,
                                   self.executed_by.model_program_fk.get_absolute_url()) if self.executed_by.model_program_fk else "None"
            hsterms_executed_by_url.text = url

        return etree.tostring(RDF_ROOT, pretty_print=True)


import recievers