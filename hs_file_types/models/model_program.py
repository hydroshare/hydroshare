import glob
import json
import os
from urllib.parse import urlparse

import jsonschema
from dateutil import parser
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.template import Context, Template
from dominate import tags as dom_tags
from rdflib import Literal, URIRef

from hs_core.hs_rdf import HSTERMS
from hs_core.hydroshare import current_site_url
from hs_core.models import ResourceFile

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
    def create(cls, **kwargs):
        """custom method to create an instance of this class"""
        mp_metadata = kwargs['mp_metadata']
        logical_file = mp_metadata.logical_file
        mp_file_type = kwargs['file_type']
        res_file = kwargs['res_file']
        # check that the resource file is part of this aggregation
        if res_file not in logical_file.files.all():
            raise ValidationError(f"Resource file {res_file} is not part of the aggregation")
        # check that the res_file is not already set to a model program file type
        if mp_metadata.mp_file_types.filter(res_file=res_file).exists():
            raise ValidationError(f"Resource file {res_file} is already set to model program file type")
        # validate mp_file_type
        mp_file_type = ModelProgramResourceFileType.type_from_string(mp_file_type)
        if mp_file_type is None:
            raise ValidationError("Not a valid model program file type")
        kwargs['file_type'] = mp_file_type
        return cls.objects.create(**kwargs)

    @classmethod
    def type_from_string(cls, type_string):
        """gets model program file type value as stored in DB for a given file type name
        :param type_string: name of the file type
        """
        type_map = {'release notes': cls.RELEASE_NOTES, 'documentation': cls.DOCUMENTATION,
                    'software': cls.SOFTWARE, 'computational engine': cls.ENGINE}

        type_string = type_string.lower()
        return type_map.get(type_string, None)

    @classmethod
    def type_name_from_type(cls, type_number):
        """gets model program file type name for the specified file type number
        :param  type_number: a number between 1 and 4
        """
        type_map = dict(cls.CHOICES)
        return type_map.get(type_number, None)

    def get_xml_name(self):
        xml_name_map = {self.RELEASE_NOTES: HSTERMS.modelReleaseNotes,
                        self.DOCUMENTATION: HSTERMS.modelDocumentation,
                        self.SOFTWARE: HSTERMS.modelSoftware,
                        self.ENGINE: HSTERMS.modelEngine
                        }
        return xml_name_map[self.file_type]


class ModelProgramFileMetaData(GenericFileMetaDataMixin):
    # version of model program
    version = models.CharField(verbose_name='Version', null=True, blank=True, max_length=255,
                               help_text='The software version or build number of the model')

    # program language used in developing the model program
    programming_languages = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=list,
                                       help_text="The programming language(s) that the model is written in")

    # operating system in which the model program can be executed
    operating_systems = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=list,
                                   help_text="Compatible operating systems to setup and run the model")

    # release date - date on which the model program was releases
    release_date = models.DateField(verbose_name='Release Date', null=True, blank=True,
                                    help_text='The date that this version of the model was released')

    # website where more information can be found for the model program
    website = models.URLField(verbose_name='Website', null=True, blank=True, max_length=255,
                              help_text='A URL to the website maintained by the model developers')

    # url for the code repository for the model program code
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
        try:
            # this query using reverse relation will raise ValueError if there are no related mi metadata objects
            # this seems to be a problem in django 4.2
            mi_metadata_objects = list(mp_aggr.mi_metadata_objects.all())
        except ValueError:
            mi_metadata_objects = []

        for mi_metadata in mi_metadata_objects:
            mi_metadata.is_dirty = True
            mi_metadata.save(update_fields=["is_dirty"])

        super(ModelProgramFileMetaData, self).delete()

    def get_rdf_graph(self):
        graph = super(ModelProgramFileMetaData, self).get_rdf_graph()
        subject = self.rdf_subject()
        site_url = current_site_url()
        for mp_file_type in self.mp_file_types.all():
            mp_file_type_xml_name = mp_file_type.get_xml_name()
            graph.add((subject, mp_file_type_xml_name, URIRef(site_url + mp_file_type.res_file.url)))

        if self.logical_file.metadata_schema_json:
            graph.add((subject, HSTERMS.modelProgramSchema, URIRef(self.logical_file.schema_file_url)))

        if self.version:
            graph.add((subject, HSTERMS.modelVersion, Literal(self.version)))
        if self.release_date:
            graph.add((subject, HSTERMS.modelReleaseDate, Literal(self.release_date.isoformat())))
        if self.website:
            graph.add((subject, HSTERMS.modelWebsite, URIRef(self.website)))
        if self.code_repository:
            graph.add((subject, HSTERMS.modelCodeRepository, URIRef(self.code_repository)))
        if self.programming_languages:
            for model_program_languages in self.programming_languages:
                graph.add((subject, HSTERMS.modelProgramLanguage, Literal(model_program_languages)))
        if self.operating_systems:
            for model_os in self.operating_systems:
                graph.add((subject, HSTERMS.modelOperatingSystem, Literal(model_os)))

        return graph

    def ingest_metadata(self, graph):

        def set_field(term, field_name, obj, is_date=False):
            val = graph.value(subject=subject, predicate=term)
            if val:
                if is_date:
                    date = parser.parse(str(val)).date()
                    setattr(obj, field_name, date)
                else:
                    setattr(obj, field_name, str(val.toPython()))

        def set_field_array(term, field_name, obj):
            vals = []
            for val in graph.objects(subject=subject, predicate=term):
                vals.append(val)
            setattr(obj, field_name, vals)

        super(ModelProgramFileMetaData, self).ingest_metadata(graph)

        subject = self.rdf_subject_from_graph(graph)

        set_field(HSTERMS.modelVersion, "version", self)
        set_field(HSTERMS.modelReleaseDate, "release_date", self, is_date=True)
        set_field(HSTERMS.modelWebsite, "website", self)
        set_field(HSTERMS.modelCodeRepository, "code_repository", self)
        set_field(HSTERMS.modelWebsite, "website", self)

        set_field_array(HSTERMS.modelProgramLanguage, "programming_languages", self)
        set_field_array(HSTERMS.modelOperatingSystem, "operating_systems", self)

        xml_name_map = {"release notes": HSTERMS.modelReleaseNotes,
                        "documentation": HSTERMS.modelDocumentation,
                        "software": HSTERMS.modelSoftware,
                        "computational engine": HSTERMS.modelEngine
                        }

        for mp_file_type, term in xml_name_map.items():
            for val in graph.objects(subject=subject, predicate=term):
                file_url = str(val.toPython())
                path = urlparse(file_url).path
                filename = os.path.basename(path)
                try:
                    file = self.logical_file.files.get(resource_file__endswith=filename)
                    if not ModelProgramResourceFileType.objects.filter(res_file=file).exists():
                        ModelProgramResourceFileType.create(file_type=mp_file_type, res_file=file, mp_metadata=self)
                except ObjectDoesNotExist:
                    pass

        schema_file = graph.value(subject=subject, predicate=HSTERMS.modelProgramSchema)
        if schema_file:
            istorage = self.logical_file.resource.get_s3_storage()
            if istorage.exists(self.logical_file.schema_file_path):
                with istorage.download(self.logical_file.schema_file_path) as f:
                    json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                metadata_schema_json = json.loads(json_str)
                self.logical_file.metadata_schema_json = metadata_schema_json
                self.logical_file.save()

    def get_html(self, include_extra_metadata=True, **kwargs):
        """generates html code to display aggregation metadata in view mode"""

        html_string = super(ModelProgramFileMetaData, self).get_html(skip_coverage=True)

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
                dom_tags.legend("Model Instance Metadata Schema")
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
        """generates html form code to edit metadata for this aggregation"""

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

                                    with dom_tags.fieldset(cls="fieldset-border"):
                                        with dom_tags.legend("Model Instance Metadata Schema", cls="legend-border",
                                                             style="font-size: 14px; font-weight:bold;"):
                                            dom_tags.span(cls="glyphicon glyphicon-info-sign text-muted",
                                                          data_toggle="tooltip",
                                                          data_placement="auto",
                                                          data_original_title="Upload/select a JSON file containing "
                                                                              "the schema. The content of the file "
                                                                              "will be shown below when you "
                                                                              "save metadata.")

                                        with dom_tags.div(cls="form-group"):
                                            link = "https://help.hydroshare.org/modeling/" \
                                                   "model-instance-metadata-schema/"
                                            link_title = "Refer to Model Instance Metadata schema help page " \
                                                         "for schema requirements."
                                            dom_tags.a(link_title, href=link, target="_blank")
                                        # give an option to upload/select a json file for the metadata schema
                                        with dom_tags.div(cls="form-group"):
                                            with dom_tags.select(cls="form-control", name='mi_json_schema_template',
                                                                 style="margin-top:10px;"):
                                                dom_tags.option("Select a schema", value="")
                                                template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
                                                template_path = os.path.join(template_path, "*.json")
                                                for schema_template in glob.glob(template_path):
                                                    template_file_name = os.path.basename(schema_template)
                                                    dom_tags.option(template_file_name, value=schema_template)
                                            dom_tags.p("OR")
                                            with dom_tags.div(cls="row file-row"):
                                                with dom_tags.div(cls="col-md-12"):
                                                    dom_tags.span("Upload a schema:")
                                                    dom_tags.input(type="file", accept=".json",
                                                                   name='mi_json_schema_file', id='mi-json-schema-file')

                                        if json_schema:
                                            dom_tags.button("Show/Hide Model Instance Metadata JSON Schema",
                                                            type="button",
                                                            cls="btn btn-success btn-block",
                                                            data_toggle="collapse",
                                                            data_target="#meta-schema")
                                            mi_schema_div = dom_tags.div(cls="content-block collapse", id="meta-schema",
                                                                         style="margin-top:10px; padding-bottom: 20px;")
                                            with mi_schema_div:
                                                dom_tags.textarea(json_schema,
                                                                  cls="form-control input-sm textinput textInput",
                                                                  id="mi-json-schema",
                                                                  name="metadata_json_schema", rows="30", readonly="")
                                        else:
                                            dom_tags.div(
                                                "Metadata schema is missing. You can either upload a schema "
                                                "JSON file or select one of the existing schema JSON files. "
                                                "Save changes using the button below to make the uploaded/selected "
                                                "schema JSON file part of the model program aggregation.",
                                                cls="alert alert-danger", id="div-missing-schema-message")

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

    metadata = models.OneToOneField(ModelProgramFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "Model Program"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mp_metadata = ModelProgramFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mp_metadata, resource=resource)

    def delete(self, using=None, keep_parents=False):
        """Overriding the base model delete() method to set any associated
        model instance aggregation metadata to dirty so that xml metadata file
        can be regenerated"""
        try:
            # this query using reverse relation will raise ValueError if there are no related mi metadata objects
            # this seems to be a problem in django 4.2
            mi_metadata_objects = list(self.mi_metadata_objects.all())
        except ValueError:
            mi_metadata_objects = []

        for mi_metadata in mi_metadata_objects:
            mi_metadata.is_dirty = True
            mi_metadata.save(update_fields=["is_dirty"])

        super(ModelProgramLogicalFile, self).delete()

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Program Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_term_label():
        return "Model Program Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "ModelProgramAggregation"

    def can_contain_aggregation(self, aggregation):
        # allow moving folder/file within the same aggregation
        return aggregation.is_model_program and self.id == aggregation.id

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return "Model Program"

    @staticmethod
    def validate_meta_schema(meta_schema):
        """A helper to validate metadata schema for model program aggregation
        :param  meta_schema: metadata schema as a string - which needs to be validated
        :returns a dict of metadata schema and a list of validation errors
        """
        validation_errors = []
        json_schema = dict()
        is_schema_valid = True
        try:
            json_schema = json.loads(meta_schema)
        except ValueError as err:
            validation_errors.append(f"Schema is not valid JSON. Error: {str(err)}")
            return json_schema, validation_errors

        if json_schema:
            schema_version = json_schema.get("$schema", "")
            if not schema_version:
                is_schema_valid = False
                err_message = "Not a valid JSON schema. {}"
                if "$schema" not in json_schema:
                    err_message = err_message.format("Key '$schema' is missing")
                else:
                    err_message = err_message.format("Key '$schema' is missing a value for schema version")
                validation_errors.append(err_message)
            else:
                if "/draft-04/" not in schema_version:
                    is_schema_valid = False
                    err_message = "Not a valid JSON schema. Schema version is invalid. Supported valid version(s): " \
                                  "draft-04"
                    validation_errors.append(err_message)

            if 'properties' not in json_schema:
                is_schema_valid = False
                validation_errors.append("Not a valid metadata schema. Attribute 'properties' is missing")

            if is_schema_valid:
                try:
                    jsonschema.Draft4Validator.check_schema(json_schema)
                except jsonschema.SchemaError as ex:
                    is_schema_valid = False
                    err_paths = " -> ".join(list(ex.path))
                    schema_errors = str(ex).split("\n")
                    schema_errors = " ".join(schema_errors)
                    schema_err_msg = f"{schema_errors}. Schema invalid field path:{err_paths}"
                    schema_err_msg = f"Not a valid JSON schema. Error:{schema_err_msg}"
                    validation_errors.append(schema_err_msg)

        if is_schema_valid:
            # custom validation - hydroshare requirements
            # this custom validation requiring additional attributes are needed for making the json-editor form
            # generation at the front-end to work
            if 'additionalProperties' not in json_schema:
                is_schema_valid = False
                validation_errors.append("Not a valid metadata schema. Attribute 'additionalProperties' is missing")

            elif json_schema['additionalProperties']:
                is_schema_valid = False
                validation_errors.append("Not a valid metadata schema. Attribute 'additionalProperties' "
                                         "should bet set to 'false'")

            def validate_schema(schema_dict):
                for k, v in schema_dict.items():
                    # key must not have whitespaces - required for xml encoding of metadata
                    if k != k.strip():
                        msg = f"Not a valid metadata schema. Attribute '{k}' has leading or trailing whitespaces"
                        validation_errors.append(msg)
                    # key must consists of alphanumeric characters only - required for xml encoding of metadata
                    if not k.isalnum():
                        msg = f"Not a valid metadata schema. Attribute '{k}' has non-alphanumeric characters"
                        validation_errors.append(msg)

                    # key must start with a alphabet character - required for xml encoding of metadata
                    if not k[0].isalpha():
                        msg = f"Not a valid metadata schema. Attribute '{k}' starts with a non-alphabet character"
                        validation_errors.append(msg)

                    if isinstance(v, dict):
                        if k not in ('properties', 'items'):
                            # we need a title to use as label for the form field
                            if 'title' not in v:
                                msg = f"Not a valid metadata schema. Attribute 'title' is missing for {k}"
                                validation_errors.append(msg)
                            elif len(v['title'].strip()) == 0:
                                msg = f"Not a valid metadata schema. Attribute 'title' has no value for {k}"
                                validation_errors.append(msg)

                            if v['type'] == 'array':
                                # we need format attribute set to 'table' in order for the jsoneditor to allow
                                # editing array type field
                                if 'format' not in v:
                                    msg = f"Not a valid metadata schema. Attribute 'format' is missing for {k}"
                                    validation_errors.append(msg)

                                elif v['format'] != 'table':
                                    msg = f"Not a valid metadata schema. Attribute 'format' should be set " \
                                          f"to table for {k}"
                                    validation_errors.append(msg)

                        if 'type' in v and v['type'] == 'object':
                            # we requiring "additionalProperties": false so that we don't allow user to add new
                            # form fields using the json-editor form
                            if 'additionalProperties' not in v:
                                msg = "Not a valid metadata schema. Attribute 'additionalProperties' is " \
                                      f"missing for {k}"
                                validation_errors.append(msg)
                            elif v['additionalProperties']:
                                msg = "Not a valid metadata schema. Attribute 'additionalProperties' must " \
                                      f"be set to false for {k}"
                                validation_errors.append(msg)

                        # check for nested objects - we are not allowing nested objects to keep the form
                        # generated from the schema by json-editor to not get complicated
                        nested_object_found = False
                        if 'type' in v and v['type'] == 'object':
                            # parent type is object - check child type is not object
                            for k_child, v_child in v.items():
                                if isinstance(v_child, dict):
                                    if 'type' in v_child and v_child['type'] == 'object':
                                        msg = "Not a valid metadata schema. Nested object types are not allowed. " \
                                              f"Attribute '{k_child}' contains nested object types"
                                        validation_errors.append(msg)
                                        nested_object_found = True
                        if not nested_object_found:
                            validate_schema(v)

            if is_schema_valid:
                validate_schema(json_schema['properties'])

        return json_schema, validation_errors

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

    def add_resource_files_in_folder(self, resource, folder):
        """
        A helper for creating aggregation. Makes all resource files in a given folder and its
        sub folders as part of the aggregation/logical file type
        :param  resource:  an instance of CompositeResource
        :param  folder: folder from which all files need to be made part of this aggregation
        """

        # get all resource files that in folder *folder* and all its sub folders
        res_files = ResourceFile.list_folder(resource=resource, folder=folder, sub_folders=True)

        for res_file in res_files:
            if not res_file.has_logical_file:
                self.add_resource_file(res_file, set_metadata_dirty=False)
            else:
                # if the file is already part of another aggregation, we need to remove it from that
                # as nested aggregation is not allowed in a model program aggregation
                res_file.logical_file_content_object = None
                self.add_resource_file(res_file, set_metadata_dirty=False)
        if res_files:
            self.set_metadata_dirty()
            resource.cleanup_aggregations()
        return res_files

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

        copy_of_logical_file.metadata_schema_json = self.metadata_schema_json
        copy_of_logical_file.folder = self.folder
        copy_of_logical_file.save()
        return copy_of_logical_file

    def set_model_instances_dirty(self):
        """set metadata to dirty for all the model instances related to this model program instance"""
        for mi_meta in self.mi_metadata_objects.all():
            mi_meta.is_dirty = True
            mi_meta.save(update_fields=["is_dirty"])

    def set_metadata_dirty(self):
        super(ModelProgramLogicalFile, self).set_metadata_dirty()
        for mi_meta in self.mi_metadata_objects.all():
            mi_meta.is_dirty = True
            mi_meta.save(update_fields=["is_dirty"])

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelProgramLogicalFile, self).create_aggregation_xml_documents(create_map_xml=create_map_xml)
        # set metadata to dirty for all model instance aggregations related to this model program aggregation
        self.set_model_instances_dirty()
