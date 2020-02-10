from django.contrib.postgres.fields import JSONField
from django.core.exceptions import PermissionDenied
from django.db import models
from django.template import Template
from dominate import tags as dom_tags

from base_model_program_instance import AbstractModelLogicalFile
from generic import GenericFileMetaDataMixin
from model_program import ModelProgramLogicalFile


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="model_instances")
    # additional metadata in json format based on metadata schema of the related (executed_by)
    # model program aggregation
    metadata_json = JSONField(default=dict)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """This generates html form code to add/update the following metadata attributes
        has_model_output
        executed_by
        metadata_json

        """
        from hs_file_types import utils

        form_action = "/hsapi/_internal/{}/update-modelinstance-metadata/"
        form_action = form_action.format(self.logical_file.id)
        root_div = dom_tags.div("{% load crispy_forms_tags %}")
        base_div, context = super(ModelInstanceFileMetaData, self).get_html_forms(render=False)
        user = kwargs['user']

        def get_executed_by_form():
            executed_by_div = dom_tags.div()
            with executed_by_div:
                dom_tags.label('Select a Model Program', fr="id_executed_by",
                               cls="control-label")
                with dom_tags.select(cls="form-control"):
                    dom_tags.option("Select a model program", value="")
                    for mp_aggr in utils.get_model_program_aggregations(user):
                        res = mp_aggr.resource
                        option = "{} (Resource:{})".format(mp_aggr.aggregation_name, res.title)
                        if self.executed_by:
                            if self.executed_by.id == mp_aggr.id:
                                dom_tags.option(option, selected="selected",
                                                value=mp_aggr.id)
                            else:
                                dom_tags.option(option, value=mp_aggr.id)
                        else:
                            dom_tags.option(option, value=mp_aggr.id)
            return executed_by_div

        with root_div:
            dom_tags.div().add(base_div)
            with dom_tags.div():
                with dom_tags.form(action=form_action, id="filetype-generic",
                                   method="post", enctype="multipart/form-data"):
                    dom_tags.div("{% csrf_token %}")
                    with dom_tags.fieldset(cls="fieldset-border"):
                        with dom_tags.div(cls="form-group"):
                            with dom_tags.div(cls="control-group"):
                                with dom_tags.div(id="mi_includes_output"):
                                    dom_tags.label('Includes Output Files*', fr="id_mi_includes_output_yes",
                                                   cls="control-label")
                                    with dom_tags.div(cls='control-group'):
                                        with dom_tags.div(cls="controls"):
                                            if self.logical_file.metadata.has_model_output:
                                                checked = 'checked'
                                            else:
                                                checked = ''
                                            with dom_tags.label('Yes', fr="id_mi_includes_output_yes",
                                                                cls="radio"):
                                                dom_tags.input(type="radio", id="id_mi_includes_output_yes",
                                                               name="mi_includes_output",
                                                               cls="inline",
                                                               checked=checked,
                                                               value=self.logical_file.metadata.has_model_output)
                                            with dom_tags.label('No', fr="id_mi_includes_output_no",
                                                                cls="radio"):
                                                dom_tags.input(type="radio", id="id_mi_includes_output_no",
                                                               name="mi_includes_output",
                                                               cls="inline",
                                                               checked=checked,
                                                               value=self.logical_file.metadata.has_model_output)
                                with dom_tags.div(id="mi_executed_by", cls="control-group"):
                                    with dom_tags.div(cls="controls"):
                                        dom_tags.legend('Model program used for execution')
                                        get_executed_by_form()

                with dom_tags.div(cls="row", style="margin-top:10px;"):
                    with dom_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        dom_tags.button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                                        style="display: none;", type="button")
        template = Template(root_div.render())
        rendered_html = template.render(context)
        return rendered_html


class ModelInstanceLogicalFile(AbstractModelLogicalFile):
    """ One file or more than one file in a specific folder can be part of this aggregation """

    # attribute to store type of model instance (SWAT, UEB etc)
    model_instance_type = models.CharField(max_length=255, default="Unknown Model Instance")
    metadata = models.OneToOneField(ModelInstanceFileMetaData, related_name="logical_file")
    data_type = "Model Instance"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mi_metadata = ModelInstanceFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mi_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Instance Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    # used in discovery faceting to aggregate native and composite content types
    def get_discovery_content_type(self):
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return self.model_instance_type

    def set_link_to_model_program(self, user, model_prog_aggr):
        """Creates a link to the specified model program aggregation *model_prog_aggr* using the
        executed_by metadata field.

        :param  user: user who is associating this (self) model instance aggregation to a model program aggregation
        :param  model_prog_aggr: an instance of ModelProgramLogicalFile to be associated with
        :raises PermissionDenied exception if the user does not have edit permission for the resource to which this
        model instance aggregation belongs or doesn't have view permission for the resource that contains the model
        program aggregation.
        """

        # check if user has edit permission for the resources
        mi_res = self.resource
        mp_res = model_prog_aggr.resource
        authorized = user.uaccess.can_change_resource(mi_res)
        if not authorized:
            raise PermissionDenied("You don't have permission to edit resource(ID:{})".format(mi_res.short_id))
        if mi_res.short_id != mp_res.short_id:
            authorized = user.uaccess.can_view_resource(mp_res)
            if not authorized:
                raise PermissionDenied("You don't have permission to view resource(ID:{})".format(mp_res.short_id))

        self.metadata.executed_by = model_prog_aggr
        self.metadata.save()
