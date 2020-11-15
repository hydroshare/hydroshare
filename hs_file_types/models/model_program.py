import json

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Template, Context
from dominate import tags as dom_tags
from lxml import etree

from hs_core.models import ResourceFile, CoreMetaData
from .base_model_program_instance import AbstractModelLogicalFile
from .generic import GenericFileMetaDataMixin


class ModelProgramResourceFileType(models.Model):
    RELEASE_NOTES = 1
    DOCUMENTATION = 2
    SOFTWARE = 3
    ENGINE = 4
    CHOICES = (
        (RELEASE_NOTES, 'Release Notes'),
        (DOCUMENTATION, 'Documentation'),
        (SOFTWARE, 'Software'),
        (ENGINE, "Computational Engine")
    )
    file_type = models.PositiveSmallIntegerField(choices=CHOICES)
    res_file = models.ForeignKey(ResourceFile, on_delete=models.CASCADE)
    mp_metadata = models.ForeignKey('ModelProgramFileMetaData', on_delete=models.CASCADE, related_name='mp_file_types')

    @classmethod
    def type_from_string(cls, type_string):
        type_map = {'release notes': cls.RELEASE_NOTES, 'documentation': cls.DOCUMENTATION,
                    'software': cls.SOFTWARE, 'computational engine': cls.ENGINE}

        type_string = type_string.lower()
        return type_map.get(type_string, None)

    @classmethod
    def type_name_from_type(cls, type_number):
        """Gets model program file type name for the specified file type number
        :param  type_number: a number between 1 and 4
        """
        type_map = dict(cls.CHOICES)
        return type_map.get(type_number, None)

    def add_to_xml_container(self, xml_container):
        xml_name_map = {self.RELEASE_NOTES: 'modelReleaseNotes',
                        self.DOCUMENTATION: "modelDocumentation",
                        self.SOFTWARE: "modelSoftware",
                        self.ENGINE: "modelEngine"
                        }
        element_xml_name = xml_name_map[self.file_type]
        element = etree.SubElement(xml_container, '{%s}%s' % (CoreMetaData.NAMESPACES['hsterms'], element_xml_name))
        element.text = self.res_file.short_path


class ModelProgramFileMetaData(GenericFileMetaDataMixin):
    # version
    version = models.CharField(verbose_name='Version', null=True, blank=True, max_length=255,
                               help_text='The software version or build number of the model')

    # program language
    programming_languages = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=list,
                                       help_text="The programming language(s) that the model is written in")

    # operating system
    operating_systems = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=list,
                                   help_text="Compatible operating systems to setup and run the model")

    # release date
    release_date = models.DateField(verbose_name='Release Date', null=True, blank=True,
                                    help_text='The date that this version of the model was released')

    # web page
    website = models.URLField(verbose_name='Website', null=True, blank=True, max_length=255,
                              help_text='A URL to the website maintained by the model developers')

    # repository
    code_repository = models.URLField(verbose_name='Software Repository', null=True,
                                      blank=True, max_length=255,
                                      help_text='A URL to the source code repository (e.g. git, mercurial, svn)')

    @property
    def operating_systems_as_string(self):
        return ", ".join(self.operating_systems)

    @property
    def programming_languages_as_string(self):
        return ", ".join(self.programming_languages)

    def delete(self, using=None, keep_parents=False):
        """Overriding the base model delete() method to set any associated
        model instance aggregation metadata to dirty so that xml metadata file
        can be regenerated for those linked model instance aggregations"""

        mp_aggr = self.logical_file
        for mi_metadata in mp_aggr.mi_metadata_objects.all():
            mi_metadata.is_dirty = True
            mi_metadata.save()

        super(ModelProgramFileMetaData, self).delete()

    def get_xml(self, pretty_print=True, additional_namespaces=None):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(ModelProgramFileMetaData, self)._get_xml_containers(
            additional_namespaces=additional_namespaces)
        for mp_file_type in self.mp_file_types.all():
            mp_file_type.add_to_xml_container(xml_container=container_to_add_to)

        if self.logical_file.model_program_type:
            model_type_name = etree.SubElement(container_to_add_to,
                                               '{%s}modelProgramType' % CoreMetaData.NAMESPACES['hsterms'])
            model_type_name.text = self.logical_file.model_program_type
        if self.version:
            model_version = etree.SubElement(container_to_add_to,
                                             '{%s}modelVersion' % CoreMetaData.NAMESPACES['hsterms'])
            model_version.text = self.version
        if self.release_date:
            model_release_date = etree.SubElement(container_to_add_to,
                                                  '{%s}modelReleaseDate' % CoreMetaData.NAMESPACES['hsterms'])
            model_release_date.text = self.release_date.isoformat()
        if self.website:
            model_website = etree.SubElement(container_to_add_to,
                                             '{%s}modelWebsite' % CoreMetaData.NAMESPACES['hsterms'])
            model_website.text = self.website
        if self.code_repository:
            model_code_repo = etree.SubElement(container_to_add_to,
                                               '{%s}modelCodeRepository' % CoreMetaData.NAMESPACES['hsterms'])
            model_code_repo.text = self.code_repository
        if self.programming_languages:
            model_program_language = etree.SubElement(container_to_add_to,
                                                      '{%s}modelProgramLanguage' % CoreMetaData.NAMESPACES['hsterms'])
            model_program_language.text = ", ".join(self.programming_languages)
        if self.operating_systems:
            model_os = etree.SubElement(container_to_add_to,
                                        '{%s}modelOperatingSystem' % CoreMetaData.NAMESPACES['hsterms'])
            model_os.text = ", ".join(self.operating_systems)

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, encoding='UTF-8',
                                                               pretty_print=pretty_print).decode()

    def get_html(self, include_extra_metadata=True, **kwargs):
        html_string = super(ModelProgramFileMetaData, self).get_html(skip_coverage=True)
        mp_program_type_div = dom_tags.div()
        with mp_program_type_div:
            dom_tags.legend("Model Program Type")
            dom_tags.p(self.logical_file.model_program_type)
        html_string += mp_program_type_div.render()

        if self.version:
            version_div = dom_tags.div(cls="content-block")
            with version_div:
                dom_tags.legend("Version")
                dom_tags.p(self.version)
            html_string += version_div.render()

        if self.release_date:
            release_date_div = dom_tags.div(cls="content-block")
            with release_date_div:
                dom_tags.legend("Release Date")
                dom_tags.p(self.release_date.strftime('%m/%d/%Y'))
            html_string += release_date_div.render()

        if self.website:
            website_div = dom_tags.div(cls="content-block")
            with website_div:
                dom_tags.legend("Website")
                dom_tags.a(self.website, href=self.website, target="_blank")
            html_string += website_div.render()

        if self.code_repository:
            code_repo_div = dom_tags.div(cls="content-block")
            with code_repo_div:
                dom_tags.legend("Code Repository")
                dom_tags.a(self.code_repository, href=self.code_repository, target="_blank")
            html_string += code_repo_div.render()

        if self.operating_systems:
            os_div = dom_tags.div(cls="content-block")
            with os_div:
                dom_tags.legend("Operating Systems")
                dom_tags.p(self.operating_systems_as_string)
            html_string += os_div.render()

        if self.programming_languages:
            pl_div = dom_tags.div(cls="content-block")
            with pl_div:
                dom_tags.legend("Programming Languages")
                dom_tags.p(self.programming_languages_as_string)
            html_string += pl_div.render()

        json_schema = self.logical_file.metadata_schema_json
        if json_schema:
            mi_schema_div = dom_tags.div(cls="content-block")
            with mi_schema_div:
                dom_tags.legend("Model Instance Metadata JSON Schema")
                json_schema = json.dumps(json_schema, indent=4)
                dom_tags.textarea(json_schema, readonly=True, rows='30', style="min-width: 100%;", cls="form-control")
            html_string += mi_schema_div.render()

        if self.mp_file_types.all():
            mp_files_div = dom_tags.div(cls="content-block")
            with mp_files_div:
                dom_tags.legend("Content Files")
                for mp_file in self.mp_file_types.all():
                    with dom_tags.div(cls="row"):
                        with dom_tags.div(cls="col-md-6"):
                            dom_tags.p(mp_file.res_file.file_name)
                        with dom_tags.div(cls="col-md-6"):
                            mp_file_type_name = ModelProgramResourceFileType.type_name_from_type(mp_file.file_type)
                            dom_tags.p(mp_file_type_name)

            html_string += mp_files_div.render()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """This generates html form code to add/update the following metadata attributes
        version
        release_date

        """
        form_action = "/hsapi/_internal/{}/update-modelprogram-metadata/"
        form_action = form_action.format(self.logical_file.id)
        root_div = dom_tags.div("{% load crispy_forms_tags %}")
        base_div, context = super(ModelProgramFileMetaData, self).get_html_forms(render=False, skip_coverage=True)

        def get_html_form_mp_file_types():
            aggregation = self.logical_file
            res_file_options_div = dom_tags.div(cls="col-12")
            with res_file_options_div:
                dom_tags.input(type="text", name="mp_file_types", value="", style="display: None;")
            for res_file in aggregation.files.all():
                with dom_tags.div(cls="row file-row"):
                    with dom_tags.div(cls="col-md-6"):
                        dom_tags.p(res_file.short_path)
                    with dom_tags.div(cls="col-md-6"):
                        mp_file_type_obj = self.mp_file_types.filter(res_file=res_file).first()
                        with dom_tags.select(cls="form-control"):
                            dom_tags.option("Select file type", value="")
                            for mp_file_type in ModelProgramResourceFileType.CHOICES:
                                mp_file_type_name = mp_file_type[1]
                                if mp_file_type_obj is not None:
                                    if mp_file_type_obj.file_type == mp_file_type[0]:
                                        dom_tags.option(mp_file_type_name, selected="selected", value=mp_file_type_name)
                                    else:
                                        dom_tags.option(mp_file_type_name, value=mp_file_type_name)
                                else:
                                    dom_tags.option(mp_file_type_name, value=mp_file_type_name)

            return res_file_options_div

        with root_div:
            dom_tags.div().add(base_div)
            with dom_tags.div():
                with dom_tags.form(action=form_action, id="filetype-modelprogram",
                                   method="post", enctype="multipart/form-data"):
                    dom_tags.div("{% csrf_token %}")
                    with dom_tags.fieldset(cls="fieldset-border"):
                        dom_tags.legend("General Information", cls="legend-border")
                        with dom_tags.div(cls="form-group"):
                            with dom_tags.div(cls="control-group"):
                                with dom_tags.div(id="mp-program-type"):
                                    dom_tags.label('Model Program Type*', fr="id_mp_program_type", cls="control-label")
                                    dom_tags.input(type="text", id="id_mp_program_type", name="mp_program_type",
                                                   cls="form-control input-sm textinput",
                                                   value=self.logical_file.model_program_type)
                                dom_tags.label('Version', cls="control-label", fr="file_version")
                                with dom_tags.div(cls="controls"):
                                    if self.version:
                                        version = self.version
                                    else:
                                        version = ""
                                    dom_tags.input(value=version,
                                                   cls="form-control input-sm textinput textInput",
                                                   id="file_version", maxlength="250",
                                                   name="version", type="text")
                                dom_tags.label('Release Date', fr="file_release_date", cls="control-label")
                                with dom_tags.div(cls="controls"):
                                    if self.release_date:
                                        release_date = self.release_date.strftime('%m/%d/%Y')
                                    else:
                                        release_date = ""
                                    dom_tags.input(value=release_date,
                                                   cls="form-control input-sm dateinput",
                                                   id="file_release_date",
                                                   name="release_date", type="text")

                                dom_tags.label('Website', fr="file_website", cls="control-label")
                                with dom_tags.div(cls="controls"):
                                    if self.website:
                                        website = self.website
                                    else:
                                        website = ""
                                    dom_tags.input(value=website,
                                                   cls="form-control input-sm textinput textInput",
                                                   id="file_website", maxlength="250",
                                                   name="website", type="text")
                                dom_tags.label('Code Repository', fr="file_code_repository", cls="control-label")
                                with dom_tags.div(cls="controls"):
                                    if self.code_repository:
                                        code_repo = self.code_repository
                                    else:
                                        code_repo = ""
                                    dom_tags.input(value=code_repo,
                                                   cls="form-control input-sm textinput textInput",
                                                   id="file_code_repository", maxlength="250",
                                                   name="code_repository", type="text")
                                dom_tags.label('Operating Systems', fr="file_operating_systems", cls="control-label")
                                with dom_tags.div(cls="controls"):
                                    operating_systems = self.operating_systems_as_string
                                    dom_tags.input(value=operating_systems,
                                                   cls="form-control input-sm textinput textInput",
                                                   id="file_operating_systems", maxlength="250",
                                                   name="operating_systems", type="text")
                                dom_tags.label('Programming Languages', fr="file_programming_languages",
                                               cls="control-label")
                                with dom_tags.div(cls="controls"):
                                    programming_languages = self.programming_languages_as_string
                                    dom_tags.input(value=programming_languages,
                                                   cls="form-control input-sm textinput textInput",
                                                   id="file_programming_languages", maxlength="250",
                                                   name="programming_languages", type="text")
                                with dom_tags.div(cls="controls"):
                                    json_schema = self.logical_file.metadata_schema_json
                                    if json_schema:
                                        json_schema = json.dumps(json_schema, indent=4)
                                    else:
                                        json_schema = ''
                                    dom_tags.label("Model Instance Metadata JSON Schema", fr="mi-json-schema",
                                                   cls="control-label")
                                    dom_tags.span(cls="glyphicon glyphicon-info-sign text-muted", data_toggle="tooltip",
                                                  data_placement="auto",
                                                  data_original_title="Upload a JSON file containing the schema. "
                                                                      "Uploaded file will not be saved as part of "
                                                                      "the resource. Schema data from the uploaded "
                                                                      "file will be used to populate the field below.")

                                    # give an option to upload a json file for the metadata schema
                                    with dom_tags.div(cls="form-group"):
                                        dom_tags.input(type="file", accept=".json",
                                                       name='mi_json_schema_file', id='mi-json-schema-file')

                                    dom_tags.textarea(json_schema,
                                                      cls="form-control input-sm textinput textInput",
                                                      id="mi-json-schema",
                                                      name="metadata_json_schema", rows="30", readonly="")

                            with dom_tags.div(id="mp_content_files", cls="control-group"):
                                with dom_tags.div(cls="controls"):
                                    dom_tags.legend('Content Files')
                                    get_html_form_mp_file_types()

                        with dom_tags.div(cls="row", style="margin-top:10px;"):
                            with dom_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                                dom_tags.button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                                                style="display: none;", type="button")

        template = Template(root_div.render())
        rendered_html = template.render(context)
        return rendered_html


class ModelProgramLogicalFile(AbstractModelLogicalFile):
    """ One file or more than one file in a specific folder can be part of this aggregation """

    # attribute to store type of model program (SWAT, UEB etc)
    model_program_type = models.CharField(max_length=255, default="Unknown Model Program")

    metadata = models.OneToOneField(ModelProgramFileMetaData, related_name="logical_file")
    data_type = "Model Program"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mp_metadata = ModelProgramFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mp_metadata, resource=resource)

    def delete(self, using=None, keep_parents=False):
        """Overriding the base model delete() method to set any associated
        model instance aggregation metadata to dirty so that xml metadata file
        can be regenerated"""

        for mi_metadata in self.mi_metadata_objects.all():
            mi_metadata.is_dirty = True
            mi_metadata.save()

        super(ModelProgramLogicalFile, self).delete()

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Program Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelProgramAggregation"

    # used in discovery faceting to aggregate native and composite content types
    def get_discovery_content_type(self):
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return self.model_program_type

    def set_res_file_as_mp_file_type(self, res_file, mp_file_type):
        """Creates an instance of ModelProgramResourceFileType using the specified resource file *res_file*
        :param  res_file: An instance of ResourceFile that is already part of this aggregation
        :param  mp_file_type: Model program file type to set. Valid values are: software, engine, release notes,
        documentation
        """

        # check that the resource file is part of this aggregation
        if res_file not in self.files.all():
            raise ValidationError("Res file is not part of the aggregation")
        # check that the res_file is not already set to a model program file type
        if self.metadata.mp_file_types.filter(res_file=res_file).exists():
            raise ValidationError("Res file is already set to model program file type")
        # validate mp_file_type
        mp_file_type = ModelProgramResourceFileType.type_from_string(mp_file_type)
        if mp_file_type is None:
            raise ValidationError("Not a valid model program file type")
        # create an instance of ModelProgramResourceFileType
        ModelProgramResourceFileType.objects.create(file_type=mp_file_type, res_file=res_file,
                                                    mp_metadata=self.metadata)

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelProgramLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()

    def copy_mp_file_types(self, tgt_logical_file):
        """helper function to support creating copy or new version of a resource
        :param tgt_logical_file: an instance of ModelProgramLogicalFile which has been
        created as part of creating a copy/new version of a resource
        """
        for mp_file_type in self.metadata.mp_file_types.all():
            mp_res_file = ''
            for res_file in tgt_logical_file.files.all():
                if res_file.short_path == mp_file_type.res_file.short_path:
                    mp_res_file = res_file
                    break
            if mp_res_file:
                ModelProgramResourceFileType.objects.create(file_type=mp_file_type.file_type, res_file=mp_res_file,
                                                            mp_metadata=tgt_logical_file.metadata)

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(ModelProgramLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.metadata.version = self.metadata.version
        copy_of_logical_file.metadata.programming_languages = self.metadata.programming_languages
        copy_of_logical_file.metadata.operating_systems = self.metadata.operating_systems
        copy_of_logical_file.metadata.release_date = self.metadata.release_date
        copy_of_logical_file.metadata.website = self.metadata.website
        copy_of_logical_file.metadata.code_repository = self.metadata.code_repository
        copy_of_logical_file.metadata.save()

        copy_of_logical_file.model_program_type = self.model_program_type
        copy_of_logical_file.metadata_schema_json = self.metadata_schema_json
        copy_of_logical_file.folder = self.folder
        copy_of_logical_file.save()
        return copy_of_logical_file

    def set_model_instances_dirty(self):
        """set metadata to dirty for all the model instances related to this model program instance"""
        for mi_meta in self.mi_metadata_objects.all():
            mi_meta.is_dirty = True
            mi_meta.save()
