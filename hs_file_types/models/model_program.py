import os
import logging
import json
import jsonschema

from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Template, Context
from lxml import etree
from dominate import tags as dom_tags

from hs_core.models import ResourceFile, CoreMetaData
from base import AbstractLogicalFile, FileTypeContext
from generic import GenericFileMetaDataMixin


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
                    'software': cls.SOFTWARE, 'engine': cls.ENGINE}

        type_string = type_string.lower()
        return type_map.get(type_string, None)

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
    programming_languages = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[],
                                       help_text="The programming language(s) that the model is written in")

    # operating system
    operating_systems = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[],
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

    # TODO: needs to test this function once there is UI for populating metadata for this aggregation
    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(ModelProgramFileMetaData, self)._get_xml_containers()
        for mp_file_type in self.mp_file_types.all():
            mp_file_type.add_to_xml_container(xml_container=container_to_add_to)
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
                                                               pretty_print=pretty_print)

    def get_html(self, include_extra_metadata=True, **kwargs):
        html_string = super(ModelProgramFileMetaData, self).get_html()
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
                dom_tags.p(self.website)
            html_string += website_div.render()
        if self.code_repository:
            code_repo_div = dom_tags.div(cls="content-block")
            with code_repo_div:
                dom_tags.legend("Code Repository")
                dom_tags.p(self.code_repository)
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
        json_schema = self.logical_file.mi_schema_json
        if json_schema:
            mi_schema_div = dom_tags.div(cls="content-block")
            with mi_schema_div:
                dom_tags.legend("Model Instance Metadata JSON Schema")
                json_schema = json.dumps(json_schema)
                dom_tags.p(json_schema)
            html_string += mi_schema_div.render()
        # TODO: need to add the code for displaying mp file types here
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
        base_div, context = super(ModelProgramFileMetaData, self).get_html_forms(render=False)

        with root_div:
            dom_tags.div().add(base_div)
            with dom_tags.div():
                dom_tags.legend("General Information")
                with dom_tags.form(action=form_action, id="filetype-generic",
                                   method="post", enctype="multipart/form-data"):
                    dom_tags.div("{% csrf_token %}")
                    with dom_tags.div(cls="form-group"):
                        with dom_tags.div(cls="control-group"):
                            dom_tags.legend('Version')
                            with dom_tags.div(cls="controls"):
                                if self.version:
                                    version = self.version
                                else:
                                    version = ""
                                dom_tags.input(value=version,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_version", maxlength="250",
                                               name="version", type="text")
                            dom_tags.legend('Release Date')
                            with dom_tags.div(cls="controls"):
                                if self.release_date:
                                    release_date = self.release_date.strftime('%m/%d/%Y')
                                else:
                                    release_date = ""
                                dom_tags.input(value=release_date,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_release_date", maxlength="250",
                                               name="release_date", type="text")

                            dom_tags.legend('Website')
                            with dom_tags.div(cls="controls"):
                                if self.website:
                                    website = self.website
                                else:
                                    website = ""
                                dom_tags.input(value=website,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_website", maxlength="250",
                                               name="website", type="text")
                            dom_tags.legend('Code Repository')
                            with dom_tags.div(cls="controls"):
                                if self.code_repository:
                                    code_repo = self.code_repository
                                else:
                                    code_repo = ""
                                dom_tags.input(value=code_repo,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_code_repository", maxlength="250",
                                               name="code_repository", type="text")
                            dom_tags.legend('Operating Systems')
                            with dom_tags.div(cls="controls"):
                                operating_systems = self.operating_systems_as_string
                                dom_tags.input(value=operating_systems,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_operating_systems", maxlength="250",
                                               name="operating_systems", type="text")
                            dom_tags.legend('Programming Languages')
                            with dom_tags.div(cls="controls"):
                                programming_languages = self.programming_languages_as_string
                                dom_tags.input(value=programming_languages,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_programming_languages", maxlength="250",
                                               name="programming_languages", type="text")
                            with dom_tags.div(cls="controls"):
                                json_schema = self.logical_file.mi_schema_json
                                if json_schema:
                                    json_schema = json.dumps(json_schema)
                                else:
                                    json_schema = ''
                                dom_tags.label("Model Instance Metadata JSON Schema", fr="file_mi_json_schema")
                                dom_tags.textarea(json_schema,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_mi_json_schema",
                                               name="mi_json_schema", rows="15")

                            # TODO: need to add the code for editing mp file types here

                    with dom_tags.div(cls="row", style="margin-top:10px;"):
                        with dom_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                            dom_tags.button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                                            style="display: none;", type="button")

        template = Template(root_div.render())
        rendered_html = template.render(context)
        return rendered_html


class ModelProgramLogicalFile(AbstractLogicalFile):
    """ One file or more than one files in a specific folder can be part of this aggregation """

    metadata = models.OneToOneField(ModelProgramFileMetaData, related_name="logical_file")

    # metadata schema (in json format) for model instance aggregation to which this aggregation
    # can be related. metadata for the related model instance aggregation is validated based on this schema
    mi_schema_json = JSONField(default=dict)

    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation. Where folder is not set, the one file that is part
    # of this aggregation becomes the aggregation name
    folder = models.CharField(max_length=4096, null=True, blank=True)
    data_type = "Model Program"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mp_metadata = ModelProgramFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mp_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Program Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelProgramLogicalFile"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return "Model Program"

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) == 0:
            # no files
            return ""

        return cls.__name__

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
        """Gets any one resource file from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """Makes all physical files that are in a folder (*folder_path*) part of a model program
        aggregation type or a single file (*file_id*) part of this aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=None,
                             is_temp_file=False) as ft_ctx:

            if folder_path is not None:
                res_files = []
                dataset_name = folder_path
                if '/' in folder_path:
                    dataset_name = os.path.basename(folder_path)
            else:
                res_file = ft_ctx.res_file
                res_files = [res_file]
                folder_path = res_file.file_folder
                dataset_name, _ = os.path.splitext(res_file.file_name)

            # create a model program logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=res_files,
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)

            if folder_path is not None and file_id is None:
                logical_file.folder = folder_path
                logical_file.save()
                # make all the files in the selected folder as part of the aggregation
                logical_file.add_resource_files_in_folder(resource, folder_path)
                log.info("Model Program aggregation was created for folder:{}.".format(folder_path))
            else:
                log.info("Model Program aggregation was created for file:{}.".format(res_file.storage_path))
            ft_ctx.logical_file = logical_file

    def set_mi_schema(self, json_schema_string):
        """Sets the mi_schema_json fields of the aggregation with valid json schema
        :param  json_schema_string: a string containing json schema
        """
        json_schema = json.loads(json_schema_string)
        # validate schema
        try:
            jsonschema.Draft4Validator.check_schema(json_schema)
        except jsonschema.SchemaError as ex:
            raise ValidationError("Not a valid json schema.{}".format(ex.message))
        self.mi_schema_json = json_schema
        self.save()

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
