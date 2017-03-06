from django.db import models
from django.template import Template, Context

from dominate.tags import div, form, button, h4

from hs_core.models import Coverage
from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm

from base import AbstractFileMetaData, AbstractLogicalFile


class GenericFileMetaData(AbstractFileMetaData):
    def get_html(self):
        """overrides the base class function"""

        html_string = super(GenericFileMetaData, self).get_html()
        if not self.has_metadata:
            root_div = div(cls="alert alert-warning alert-dismissible", role="alert")
            with root_div:
                h4("No file level metadata exists for the selected file.")
            html_string = root_div.render()
        else:
            if self.temporal_coverage:
                html_string += self.temporal_coverage.get_html()

            if self.spatial_coverage:
                html_string += self.spatial_coverage.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, datatset_name_form=True):
        """overrides the base class function"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(GenericFileMetaData, self).get_html_forms()
            with div(cls="col-lg-6 col-xs-12"):
                with form(id="id-coverage_temporal-file-type", action="{{ temp_form.action }}",
                          method="post", enctype="multipart/form-data"):
                    div("{% crispy temp_form %}")
                    with div(cls="row", style="margin-top:10px;"):
                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                     "col-md-2 col-xs-6"):
                            button("Save changes", type="button",
                                   cls="btn btn-primary pull-right btn-form-submit",
                                   style="display: none;")  # TODO: TESTING

            with div(cls="col-lg-6 col-xs-12"):
                with form(id="id-coverage-spatial-filetype", action="{{ spatial_form.action }}",
                          method="post", enctype="multipart/form-data"):
                    div("{% crispy spatial_form %}")
                    with div(cls="row", style="margin-top:10px;"):
                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                     "col-md-2 col-xs-6"):
                            button("Save changes", type="button",
                                   cls="btn btn-primary pull-right btn-form-submit",
                                   style="display: none;")  # TODO: TESTING

        template = Template(root_div.render())
        context_dict = dict()
        temp_cov_form = self.get_temporal_coverage_form()
        spatial_cov_form = self.get_spatial_coverage_form()
        update_action = "/hsapi/_internal/GenericLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/GenericLogicalFile/{0}/{1}/add-file-metadata/"

        element_name = "coverage"
        if self.temporal_coverage or self.spatial_coverage:
            if self.temporal_coverage:
                temp_action = update_action.format(self.logical_file.id, element_name,
                                                   self.temporal_coverage.id)
                temp_cov_form.action = temp_action
            else:
                temp_action = create_action.format(self.logical_file.id, element_name)
                temp_cov_form.action = temp_action

            if self.spatial_coverage:
                spatial_action = update_action.format(self.logical_file.id, element_name,
                                                      self.spatial_coverage.id)
                spatial_cov_form.action = spatial_action
            else:
                spatial_action = create_action.format(self.logical_file.id, element_name)
                spatial_cov_form.action = spatial_action
        else:
            action = create_action.format(self.logical_file.id, element_name)
            temp_cov_form.action = action
            spatial_cov_form.action = action

        context_dict["temp_form"] = temp_cov_form
        context_dict["spatial_form"] = spatial_cov_form
        context = Context(context_dict)
        rendered_html = template.render(context)
        # file level form field ids need to changed so that they are different from
        # the ids used at the resource level for the same type of metadata elements
        # Note: These string replacement operations need to be done in this particular
        # order otherwise same element id will be replaced multiple times
        rendered_html = rendered_html.replace("div_id_start", "div_id_start_filetype")
        rendered_html = rendered_html.replace("div_id_end", "div_id_end_filetype")
        rendered_html = rendered_html.replace("id_start", "id_start_filetype")
        rendered_html = rendered_html.replace("id_end", "id_end_filetype")

        for spatial_element_id in ('div_id_northlimit', 'div_id_southlimit', 'div_id_westlimit',
                                   'div_id_eastlimit'):
            rendered_html = rendered_html.replace(spatial_element_id,
                                                  spatial_element_id + "_filetype", 1)
        for spatial_element_id in ('div_id_type', 'div_id_north', 'div_id_east'):
            rendered_html = rendered_html.replace(spatial_element_id,
                                                  spatial_element_id + "_filetype", 1)

        return rendered_html

    def get_spatial_coverage_form(self):
        return Coverage.get_spatial_html_form(resource=None, element=self.spatial_coverage)

    def get_temporal_coverage_form(self):
        return Coverage.get_temporal_html_form(resource=None, element=self.temporal_coverage)

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Generic file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == "coverage":
            if 'type' in request.POST:
                if request.POST['type'].lower() == 'point' or request.POST['type'].lower() == 'box':
                    element_form = CoverageSpatialForm(data=request.POST)
                else:
                    element_form = CoverageTemporalForm(data=request.POST)
            else:
                element_form = CoverageTemporalForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


class GenericLogicalFile(AbstractLogicalFile):
    """ Each resource file is assigned an instance of this logical file type on upload to
    Composite Resource """
    metadata = models.OneToOneField(GenericFileMetaData, related_name="logical_file")
    data_type = "Generic data"

    @classmethod
    def create(cls):
        # this custom method MUST be used to create an instance of this class
        generic_metadata = GenericFileMetaData.objects.create()
        return cls.objects.create(metadata=generic_metadata)
