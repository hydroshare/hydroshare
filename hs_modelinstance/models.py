from lxml import etree

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.core.exceptions import ValidationError

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
    # model_name: the id of the model program used for execution
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

        # when creating a new resource version, we need to lookup the existing model_program_fk
        if 'model_program_fk' in kwargs:

            # get the foreign key id if one has been set (i.e. when creating a new version)
            mp_short_id = kwargs['model_program_fk']

            # get the MP object that matches.  Returns None if nothing is found
            obj = ModelProgramResource.objects.filter(id=mp_short_id).first()

        # when adding or changing the model_program_fk, we need to lookup the model obj based on mp_short_id
        else:
            # get the selected model program short id that has been submitted via the form
            mp_short_id = kwargs['model_name']

            # get the MP object that matches.  Returns None if nothing is found
            obj = ModelProgramResource.objects.filter(short_id=mp_short_id).first()


        if obj is None:
            # return Null
            return None
        else:
            # return an instance of the ExecutedBy class using the selected Model Program as a foreign key
            metadata_obj = kwargs['content_object']
            title = obj.title
            return super(ExecutedBy,cls).create(model_program_fk=obj, model_name=title, content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):

        # get the shortid of the selected model program (passed in from javascript)
        shortid = kwargs['model_name']

        # get the MP object that matches.  Returns None if nothing is found
        obj = ModelProgramResource.objects.filter(short_id=shortid).first()

        if obj is None:
            # return a Null instance of the ExecutedBy class
            return super(ExecutedBy,cls).update(model_program_fk=None, model_name='Unspecified', element_id=element_id)
        else:
            # return an instance of the ExecutedBy class using the selected Model Program as a foreign key
            title = obj.title
            return super(ExecutedBy,cls).update(model_program_fk=obj, model_name=title, element_id=element_id)


# Model Instance Resource type
class ModelInstanceResource(BaseResource):
    objects = ResourceManager("ModelInstanceResource")

    discovery_content_type = 'Model Instance'  # used during discovery

    class Meta:
        verbose_name = 'Model Instance Resource'
        proxy = True

    @property
    def metadata(self):
        md = ModelInstanceMetaData()
        return self._get_metadata(md)

processor_for(ModelInstanceResource)(resource_processor)


# metadata container class
class ModelInstanceMetaData(CoreMetaData):
    _model_output = GenericRelation(ModelOutput)
    _executed_by = GenericRelation(ExecutedBy)

    @property
    def resource(self):
        return ModelInstanceResource.objects.filter(object_id=self.id).first()

    @property
    def model_output(self):
        return self._model_output.all().first()

    @property
    def executed_by(self):
        return self._executed_by.all().first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import ModelInstanceMetaDataSerializer
        return ModelInstanceMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'modeloutput' in keys_to_update:
            parsed_metadata.append({"modeloutput": metadata.pop('modeloutput')})

        if 'executedby' in keys_to_update:
            parsed_metadata.append({"executedby": metadata.pop('executedby')})

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('ModelOutput')
        elements.append('ExecutedBy')
        return elements

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata
        from forms import ModelOutputValidationForm, ExecutedByValidationForm

        super(ModelInstanceMetaData, self).update(metadata, user)
        attribute_mappings = {'modeloutput': 'model_output', 'executedby': 'executed_by'}
        with transaction.atomic():
            # update/create non-repeatable element
            for element_name in attribute_mappings.keys():
                for dict_item in metadata:
                    if element_name in dict_item:
                        if element_name == 'modeloutput':
                            validation_form = ModelOutputValidationForm(dict_item[element_name])
                        else:
                            validation_form = ExecutedByValidationForm(dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                        element_property_name = attribute_mappings[element_name]
                        self.update_non_repeatable_element(element_name, metadata,
                                                           element_property_name)

    def get_xml(self, pretty_print=True, include_format_elements=True):
        # get the xml string representation of the core metadata elements
        xml_string = super(ModelInstanceMetaData, self).get_xml(pretty_print=pretty_print)

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

        return etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def delete_all_elements(self):
        super(ModelInstanceMetaData, self).delete_all_elements()
        self._model_output.all().delete()
        self._executed_by.all().delete()

import receivers
