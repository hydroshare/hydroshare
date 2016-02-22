from lxml import etree

from django.contrib.contenttypes import generic
from django.db import models

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare import utils

from hs_model_program.models import ModelProgramResource

# extended metadata elements for Model Instance resource type
class ModelOutput(AbstractMetaDataElement):
    term = 'ModelOutput'
    includes_output = models.BooleanField(default=False)

    def __unicode__(self):
        return self.includes_output

    class Meta:
        # ModelOutput element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def includesModelOutput(self):
        if self.includes_output:
            return "Yes"
        else:
            return "No"

class ExecutedBy(AbstractMetaDataElement):

    term = 'ExecutedBY'
    model_name = models.CharField(max_length=500, default=None)
    model_program_fk = models.ForeignKey('hs_model_program.ModelProgramResource', null=True, blank=True, default=None, related_name='modelinstance')

    def __unicode__(self):
        return self.model_name

    class Meta:
        # ExecutedBy element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def modelProgramName(self):
        if self.model_program_fk:
            return self.model_program_fk.title
        else:
            return "Unspecified"

    @property
    def modelProgramIdentifier(self):
        if self.model_program_fk:
            return '%s%s' % (utils.current_site_url(), self.model_program_fk.get_absolute_url())
        else:
            return "None"

    @classmethod
    def create(cls, **kwargs):
        shortid = kwargs['model_name']
        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()
        metadata_obj = kwargs['content_object']
        title = obj.title
        return super(ExecutedBy,cls).create(model_program_fk=obj, model_name=title,content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        shortid = kwargs['model_name']
        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()
        return super(ExecutedBy,cls).update(model_program_fk=obj, element_id=element_id)

# Model Instance Resource type
class ModelInstanceResource(BaseResource):
    objects = ResourceManager("ModelInstanceResource")

    class Meta:
        verbose_name = 'Model Instance Resource'
        proxy = True

    @property
    def metadata(self):
        md = ModelInstanceMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

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

    def get_xml(self, pretty_print=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(ModelInstanceMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_output:
            modelOutputFields = ['includesModelOutput']
            self.add_metadata_element_to_xml(container,self.model_output,modelOutputFields)

        if self.executed_by:
            executed_by = self.executed_by
        else:
            executed_by = ExecutedBy()

        executedByFields = ['modelProgramName','modelProgramIdentifier']
        self.add_metadata_element_to_xml(container,executed_by,executedByFields)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(ModelInstanceMetaData, self).delete_all_elements()
        self._model_output.all().delete()
        self._executed_by.all().delete()

import receivers