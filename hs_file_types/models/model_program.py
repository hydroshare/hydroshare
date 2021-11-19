import glob
import json
import os

from urllib.parse import urlparse
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Template, Context
from dominate import tags as dom_tags
from rdflib import Literal, URIRef
from dateutil import parser

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
        for mi_metadata in mp_aggr.mi_metadata_objects.all():
            mi_metadata.is_dirty = True
            mi_metadata.save()

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

        if self.logical_file.model_program_type:
            graph.add((subject, HSTERMS.modelProgramName, Literal(self.logical_file.model_program_type)))
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
                    date = parser.parse(str(val))
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

        set_field(HSTERMS.modelProgramName, "model_program_type", self.logical_file)
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
                except ResourceFile.DoesNotExist:
                    pass

        schema_file = graph.value(subject=subject, predicate=HSTERMS.modelProgramSchema)
        if schema_file:
            istorage = self.logical_file.resource.get_irods_storage()
            if istorage.exists(self.logical_file.schema_file_path):
                with istorage.download(self.logical_file.schema_file_path) as f:
                    json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                metadata_schema_json = json.loads(json_str)
                self.logical_file.metadata_schema_json = metadata_schema_json
                self.logical_file.save()


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
