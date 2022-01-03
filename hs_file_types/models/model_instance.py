import json
import os
import random
import shutil
from uuid import uuid4

from django.contrib.postgres.fields import JSONField
from django.db import models
from rdflib import Literal, URIRef

from hs_core.hs_rdf import HSTERMS
from hs_core.hydroshare.utils import current_site_url
from hs_core.models import ResourceFile
from .base import NestedLogicalFileMixin
from .base_model_program_instance import AbstractModelLogicalFile
from .generic import GenericFileMetaDataMixin
from .model_program import ModelProgramLogicalFile
from hydroshare import settings


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="mi_metadata_objects")

    # additional metadata in json format based on metadata schema of the related (executed_by)
    # model program aggregation
    metadata_json = JSONField(default=dict)

    def get_rdf_graph(self):
        graph = super(ModelInstanceFileMetaData, self).get_rdf_graph()
        subject = self.rdf_subject()

        graph.add((subject, HSTERMS.includesModelOutput, Literal(self.has_model_output)))

        if self.executed_by:
            resource = self.logical_file.resource
            hs_res_url = os.path.join(current_site_url(), 'resource', resource.file_path)
            aggr_url = os.path.join(hs_res_url, self.executed_by.map_short_file_path) + '#aggregation'
            graph.add((subject, HSTERMS.executedByModelProgram, URIRef(aggr_url)))

        if self.logical_file.metadata_schema_json:
            graph.add((subject, HSTERMS.modelProgramSchema, URIRef(self.logical_file.schema_file_url)))

        if self.metadata_json:
            graph.add((subject, HSTERMS.modelProgramSchemaValues, URIRef(self.logical_file.schema_values_file_url)))

        return graph

    def ingest_metadata(self, graph):
        from ..utils import get_logical_file_by_map_file_path

        super(ModelInstanceFileMetaData, self).ingest_metadata(graph)
        subject = self.rdf_subject_from_graph(graph)

        has_model_output = graph.value(subject=subject, predicate=HSTERMS.includesModelOutput)
        if has_model_output:
            self.has_model_output = str(has_model_output).lower() == 'true'
            self.save()

        executed_by = graph.value(subject=subject, predicate=HSTERMS.executedByModelProgram)
        if executed_by:
            aggr_map_path = executed_by.split('/resource/', 1)[1].split("#")[0]
            mp_aggr = get_logical_file_by_map_file_path(self.logical_file.resource, ModelProgramLogicalFile,
                                                        aggr_map_path)
            self.executed_by = mp_aggr
            self.save()

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

        schema_values_file = graph.value(subject=subject, predicate=HSTERMS.modelProgramSchemaValues)
        if schema_values_file:
            istorage = self.logical_file.resource.get_irods_storage()
            if istorage.exists(self.logical_file.schema_values_file_path):
                with istorage.download(self.logical_file.schema_values_file_path) as f:
                    json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                metadata_schema_json = json.loads(json_str)
                self.metadata_json = metadata_schema_json
                self.save()


class ModelInstanceLogicalFile(NestedLogicalFileMixin, AbstractModelLogicalFile):
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
    def get_aggregation_term_label():
        return "Model Instance Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    @property
    def schema_values_short_file_path(self):
        """File path of the aggregation schema values file relative to {resource_id}/data/contents/
        """

        json_file_name = self.aggregation_name
        if "/" in json_file_name:
            json_file_name = os.path.basename(json_file_name)

        json_file_name, _ = os.path.splitext(json_file_name)

        json_file_name += "_schema_values.json"

        if self.folder:
            file_folder = self.folder
        else:
            file_folder = self.files.first().file_folder
        if file_folder:
            json_file_name = os.path.join(file_folder, json_file_name)

        return json_file_name

    @property
    def schema_values_file_path(self):
        """Full path of the aggregation schema values json file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.schema_values_short_file_path)

    @property
    def schema_values_file_url(self):
        """URL to the aggregation metadata schema values json file
        """
        from hs_core.hydroshare.utils import current_site_url
        return "{}/resource/{}".format(current_site_url(), self.schema_values_file_path)

    def set_metadata_dirty(self):
        super(ModelInstanceLogicalFile, self).set_metadata_dirty()
        for child_aggr in self.get_children():
            child_aggr.set_metadata_dirty()

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelInstanceLogicalFile, self).create_aggregation_xml_documents(create_map_xml=create_map_xml)
        for child_aggr in self.get_children():
            child_aggr.create_aggregation_xml_documents(create_map_xml=create_map_xml)
        self.create_schema_values_json_file()

    def create_schema_values_json_file(self):
        """Creates aggregation schema values json file """

        if not self.metadata.metadata_json:
            return

        # create a temp dir where the json file will be temporarily saved before copying to iRODS
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_irods_storage()

        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)

        # create json schema file for the aggregation
        json_from_file_name = os.path.join(tmpdir, 'schema_values.json')
        try:
            with open(json_from_file_name, 'w') as out:
                json_schema = json.dumps(self.metadata.metadata_json, indent=4)
                out.write(json_schema)
            to_file_name = self.schema_values_file_path
            istorage.saveFile(json_from_file_name, to_file_name, True)
        finally:
            shutil.rmtree(tmpdir)

    def can_contain_aggregation(self, aggregation):
        if aggregation.is_model_instance and self.id == aggregation.id:
            # allow moving file/folder within the same aggregation
            return True

        if aggregation.is_model_instance or aggregation.is_model_program or aggregation.is_fileset:
            return False
        return True

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return "Model Instance"

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
                self.add_resource_file(res_file)
            else:
                logical_file = res_file.logical_file
                if logical_file.is_fileset:
                    res_file.logical_file_content_object = None
                    self.add_resource_file(res_file)
        if res_files:
            resource.cleanup_aggregations()
        return res_files

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(ModelInstanceLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.metadata.has_model_output = self.metadata.has_model_output
        # Note: though copying executed_by here, it will be reset by the copy_executed_by() function
        # if the executed_by model program aggregation exists in the source resource
        copy_of_logical_file.metadata.executed_by = self.metadata.executed_by
        copy_of_logical_file.metadata.metadata_json = self.metadata.metadata_json
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.folder = self.folder
        copy_of_logical_file.metadata_schema_json = self.metadata_schema_json
        copy_of_logical_file.save()
        return copy_of_logical_file

    def copy_executed_by(self, tgt_logical_file):
        """helper function to support creating copy or new version of a resource
        :param tgt_logical_file: an instance of ModelInstanceLogicalFile which has been
        created as part of creating a copy/new version of a resource
        """

        # if the linked model program exists in the same source resource
        # then we have to reset the executed_by for the tgt logical file to the copy of the
        # same model program aggregation that is now part of the copied resource
        if self.metadata.executed_by:
            src_executed_by = self.metadata.executed_by
            src_resource = self.resource
            src_mp_logical_files = src_resource.modelprogramlogicalfile_set.all()
            if src_executed_by in src_mp_logical_files:
                tgt_resource = tgt_logical_file.resource
                tgt_mp_logical_files = tgt_resource.modelprogramlogicalfile_set.all()
                for tgt_mp_logical_file in tgt_mp_logical_files:
                    if src_executed_by.aggregation_name == tgt_mp_logical_file.aggregation_name:
                        tgt_logical_file.metadata.executed_by = tgt_mp_logical_file
                        tgt_logical_file.metadata.save()
                        break

    def logical_delete(self, user, delete_res_files=True):
        # super deletes files needed to delete the values file path
        istorage = self.resource.get_irods_storage()
        if istorage.exists(self.schema_values_file_path):
            istorage.delete(self.schema_values_file_path)
        super(ModelInstanceLogicalFile, self).logical_delete(user, delete_res_files=delete_res_files)

    def remove_aggregation(self):
        # super deletes files needed to delete the values file path
        istorage = self.resource.get_irods_storage()

        if istorage.exists(self.schema_values_file_path):
            istorage.delete(self.schema_values_file_path)
        super(ModelInstanceLogicalFile, self).remove_aggregation()


def _dict_has_value(dct):
    """helper to check if the dict contains at least one valid value"""
    for val in dct.values():
        if isinstance(val, str):
            if val.strip() != '':
                return True
        elif isinstance(val, list):
            if val:
                return True
        elif type(val) in (int, float, bool):
            return True
        elif isinstance(val, dict):
            return _dict_has_value(val)
    return False
