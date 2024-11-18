import json
import logging
import os
import random
import shutil
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from foresite import utils, Aggregation, URIRef, AggregatedResource, RdfLibSerializer
from rdflib import Namespace

from hs_core.models import ResourceFile
from hs_core.signals import post_remove_file_aggregation
from hs_file_types.models import AbstractLogicalFile
from hs_file_types.models.base import FileTypeContext
from hs_file_types.enums import AggregationMetaFilePath
from hydroshare import settings


class AbstractModelLogicalFile(AbstractLogicalFile):
    # folder path relative to {resource_id}/data/contents/ that represents this aggregation
    # folder becomes the name of the aggregation. Where folder is not set, the one file that is part
    # of this aggregation becomes the aggregation name
    folder = models.CharField(max_length=4096, null=True, blank=True)

    # metadata schema (in json format) for model instance aggregation
    # metadata for the model instance aggregation is validated based on this schema
    metadata_schema_json = models.JSONField(default=dict)

    class Meta:
        abstract = True

    @property
    def aggregation_name(self):
        """Returns aggregation name as per the aggregation naming rule defined in issue#2568"""

        if self.folder:
            # this model program/instance aggregation has been created from a folder
            # aggregation folder path is the aggregation name
            return self.folder
        else:
            # this model program/instance aggregation has been created from a single resource file
            # the path of the resource file is the aggregation name
            single_res_file = self.files.first()
            if single_res_file:
                return single_res_file.short_path
            return ""

    @property
    def schema_short_file_path(self):
        """File path of the aggregation metadata schema file relative to {resource_id}/data/contents/
        """

        json_file_name = self.aggregation_name
        if not json_file_name:
            return json_file_name

        if "/" in json_file_name:
            json_file_name = os.path.basename(json_file_name)

        json_file_name, _ = os.path.splitext(json_file_name)

        json_file_name += AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH

        if self.folder:
            file_folder = self.folder
        else:
            file_folder = ''
            aggr_file = self.files.first()
            if aggr_file is not None:
                file_folder = aggr_file.file_folder
        if file_folder:
            json_file_name = os.path.join(file_folder, json_file_name)

        return json_file_name

    @property
    def schema_file_path(self):
        """Full path of the aggregation metadata schema json file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.schema_short_file_path)

    @property
    def schema_file_url(self):
        """URL to the aggregation metadata schema json file
        """
        from hs_core.hydroshare.utils import current_site_url
        return "{}/resource/{}".format(current_site_url(), self.schema_file_path)

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation - no specific main file"""
        return ".*"

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
    def get_primary_resource_file(cls, resource_files):
        """Gets any one resource file from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    @classmethod
    def supports_folder_based_aggregation(cls):
        """A model program/model instance aggregation can be created from a folder"""
        return True

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """Makes all physical files that are in a folder (*folder_path*) part of a model program/instance
        aggregation type or a single file (*file_id*) part of this aggregation type.
        Note: parameter file_id is ignored here and a value for folder_path is required
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=None,
                             is_temp_file=False) as ft_ctx:

            if folder_path:
                res_files = []
                dataset_name = folder_path
                if '/' in folder_path:
                    dataset_name = os.path.basename(folder_path)
            else:
                res_file = ft_ctx.res_file
                res_files = [res_file]
                folder_path = res_file.file_folder
                dataset_name, _ = os.path.splitext(res_file.file_name)

            # remove any previously associated logical files from the files
            # before making them part of this new logical file
            for res_file in res_files:
                if res_file.has_logical_file:
                    res_file.logical_file_content_object = None
                    res_file.save()

            # create a model program/instance logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=res_files,
                                                  new_files_to_upload=[],
                                                  folder_path=folder_path)
            try:
                if folder_path and file_id is None:
                    logical_file.folder = folder_path
                    logical_file.save()
                    # make all the files in the selected folder as part of the aggregation
                    logical_file.add_resource_files_in_folder(resource, folder_path)
                    log.info("{0} aggregation was created for folder:{1}.".format(logical_file.data_type, folder_path))
                else:
                    log.info("{0} aggregation was created for file:{1}.".format(logical_file.data_type,
                                                                                res_file.storage_path))
                ft_ctx.logical_file = logical_file
            except Exception as ex:
                msg = "{} aggregation. Error when creating aggregation. Error:{}".format(logical_file.data_type,
                                                                                         str(ex))
                log.exception(msg)
                logical_file.remove_aggregation()
                raise ValidationError(msg)

        return logical_file

    def generate_map_xml(self):
        """Generates the xml needed to write to the aggregation map xml document"""
        from hs_core.hydroshare import encode_resource_url
        from hs_core.hydroshare.utils import current_site_url, get_file_mime_type

        current_site_url = current_site_url()
        # This is the qualified resource url.
        hs_res_url = os.path.join(current_site_url, 'resource', self.resource.file_path)
        # this is the path to the resource metadata file for download
        aggr_metadata_file_path = self.metadata_short_file_path
        metadata_url = os.path.join(hs_res_url, aggr_metadata_file_path)
        metadata_url = encode_resource_url(metadata_url)
        # this is the path to the aggregation resourcemap file for download
        aggr_map_file_path = self.map_short_file_path
        res_map_url = os.path.join(hs_res_url, aggr_map_file_path)
        res_map_url = encode_resource_url(res_map_url)

        # make the resource map:
        utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
        utils.namespaceSearchOrder.append('citoterms')

        ag_url = res_map_url + '#aggregation'
        a = Aggregation(ag_url)

        # Set properties of the aggregation
        a._dc.title = self.dataset_name
        agg_type_url = "{site}/terms/{aggr_type}"\
            .format(site=current_site_url, aggr_type=self.get_aggregation_type_name())
        a._dcterms.type = URIRef(agg_type_url)
        a._citoterms.isDocumentedBy = metadata_url
        a._ore.isDescribedBy = res_map_url

        res_type_aggregation = AggregatedResource(agg_type_url)
        res_type_aggregation._rdfs.label = self.get_aggregation_term_label()
        res_type_aggregation._rdfs.isDefinedBy = current_site_url + "/terms"

        a.add_resource(res_type_aggregation)

        # Create a description of the metadata document that describes the whole resource and add it
        # to the aggregation
        resMetaFile = AggregatedResource(metadata_url)
        resMetaFile._citoterms.documents = ag_url
        resMetaFile._ore.isAggregatedBy = ag_url
        resMetaFile._dc.format = "application/rdf+xml"

        # Create a description of the content file and add it to the aggregation
        files = self.files.all()
        resFiles = []
        for n, f in enumerate(files):
            res_uri = '{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=self.resource.short_id,
                file_name=f.short_path)
            res_uri = encode_resource_url(res_uri)
            resFiles.append(AggregatedResource(res_uri))
            resFiles[n]._ore.isAggregatedBy = ag_url
            resFiles[n]._dc.format = get_file_mime_type(os.path.basename(f.short_path))

        # Add the resource files to the aggregation
        a.add_resource(resMetaFile)
        for f in resFiles:
            a.add_resource(f)

        # Create a description of the contained aggregations and add it to the aggregation
        child_ore_aggregations = []
        for n, child_aggr in enumerate(self.get_children()):
            res_uri = '{hs_url}/resource/{res_id}/data/contents/{aggr_name}'.format(
                hs_url=current_site_url,
                res_id=self.resource.short_id,
                aggr_name=child_aggr.map_short_file_path + '#aggregation')
            res_uri = encode_resource_url(res_uri)
            child_ore_aggr = Aggregation(res_uri)
            child_ore_aggregations.append(child_ore_aggr)
            child_ore_aggregations[n]._ore.isAggregatedBy = ag_url
            child_agg_type_url = "{site}/terms/{aggr_type}"
            child_agg_type_url = child_agg_type_url.format(
                site=current_site_url, aggr_type=child_aggr.get_aggregation_type_name())
            child_ore_aggregations[n]._dcterms.type = URIRef(child_agg_type_url)

        # Add contained aggregations to the aggregation
        for aggr in child_ore_aggregations:
            a.add_resource(aggr)

        # Register a serializer with the aggregation, which creates a new ResourceMap that
        # needs a URI
        serializer = RdfLibSerializer('xml')
        # resMap = a.register_serialization(serializer, res_map_url)
        a.register_serialization(serializer, res_map_url)

        # Fetch the serialization
        remdoc = a.get_serialization()
        # remove this additional xml element - not sure why it gets added
        # <ore:aggregates rdf:resource="https://www.hydroshare.org/terms/[aggregation name]"/>
        xml_element_to_replace = '<ore:aggregates rdf:resource="{}"/>\n'.format(agg_type_url)
        xml_string = remdoc.data.replace(xml_element_to_replace, '')
        return xml_string

    def xml_file_short_path(self, resmap=True):
        """File path of the aggregation metadata or map xml file relative
        to {resource_id}/data/contents/
        :param  resmap  If true file path for aggregation resmap xml file, otherwise file path for
        aggregation metadata file is returned
        """

        xml_file_name = self.get_xml_file_name(resmap=resmap)
        if self.folder is not None:
            file_folder = self.folder
        else:
            file_folder = ''
            aggr_file = self.files.first()
            if aggr_file is not None:
                file_folder = aggr_file.file_folder

        if file_folder:
            xml_file_name = os.path.join(file_folder, xml_file_name)
        return xml_file_name

    def logical_delete(self, user, resource=None, delete_res_files=True, delete_meta_files=True):
        """
        Deletes the logical file as well as all resource files associated with this logical file.
        This function is primarily used by the system to delete logical file object and associated
        metadata as part of deleting a resource file object. Any time a request is made to
        delete a specific resource file object, if the requested file is part of a
        logical file then all files in the same logical file group will be deleted. if custom logic
        requires deleting logical file object (LFO) then instead of using LFO.delete(), you must
        use LFO.logical_delete()
        :param  user: user who is deleting file type/aggregation
        :param  resource: an instance of CompositeResource to which this logical file belongs to
        :param delete_res_files: If True all resource files that are part of this logical file will
        be deleted
        :param delete_meta_files: If True the resource map and metadata files that are part of this logical file
        will be deleted. The only time this should be set to False is when deleting a folder as the folder
        gets deleted from iRODS which deletes the associated metadata and resource map files.
        """

        from hs_core.hydroshare.resource import delete_resource_file

        parent_aggr = self.get_parent()
        if resource is None:
            resource = self.resource

        if delete_meta_files:
            # delete associated metadata and map xml documents
            istorage = resource.get_irods_storage()
            if istorage.exists(self.metadata_file_path):
                istorage.delete(self.metadata_file_path)
            if istorage.exists(self.map_file_path):
                istorage.delete(self.map_file_path)

            # delete schema json file if this a model aggregation
            if istorage.exists(self.schema_file_path):
                istorage.delete(self.schema_file_path)

        # delete all resource files associated with this instance of logical file
        if delete_res_files:
            for f in self.files.all():
                delete_resource_file(resource.short_id, f.id, user, delete_logical_file=False)
        else:
            # first need to set the aggregation for each of the associated resource files to None
            # so that deleting the aggregation (logical file) does not cascade to deleting of
            # resource files associated with the aggregation
            self.files.update(logical_file_object_id=None, logical_file_content_type=None)

        # delete logical file first then delete the associated metadata file object
        # deleting the logical file object will not automatically delete the associated
        # metadata file object
        metadata = self.metadata if self.has_metadata else None

        # if we are deleting a model program aggregation, then we need to set the
        # metadata of all the associated model instances to dirty
        if self.is_model_program:
            self.set_model_instances_dirty()
        self.delete()

        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

        # if this deleted aggregation has a parent aggregation - xml files for the parent
        # aggregation need to be regenerated at the time of download - so need to set metadata to dirty
        if parent_aggr is not None:
            parent_aggr.set_metadata_dirty()

        resource.cleanup_aggregations()

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. However, it doesn't delete any resource files that are part of the aggregation."""

        # delete associated metadata and map xml document
        istorage = self.resource.get_irods_storage()
        if istorage.exists(self.metadata_file_path):
            istorage.delete(self.metadata_file_path)
        if istorage.exists(self.map_file_path):
            istorage.delete(self.map_file_path)

        # delete schema json file if this a model aggregation
        if istorage.exists(self.schema_file_path):
            istorage.delete(self.schema_file_path)

        # find if there is a parent aggregation - files in this (self) aggregation
        # need to be added to parent if exists
        parent_aggr = self.get_parent()

        res_files = []
        res_files.extend(self.files.all())

        # first need to set the aggregation for each of the associated resource files to None
        # so that deleting the aggregation (logical file) does not cascade to deleting of
        # resource files associated with the aggregation
        self.files.update(logical_file_object_id=None, logical_file_content_type=None)

        # delete logical file (aggregation) first then delete the associated metadata file object
        # deleting the logical file object will not automatically delete the associated
        # metadata file object
        metadata = self.metadata if self.has_metadata else None

        # if we are removing a model program aggregation, then we need to set the
        # metadata of all the associated model instances to dirty
        if self.is_model_program:
            self.set_model_instances_dirty()
        self.delete()

        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

        # make all the resource files of this (self) aggregation part of the parent aggregation
        if parent_aggr is not None:
            for res_file in res_files:
                parent_aggr.add_resource_file(res_file)

            # need to regenerate the xml files for the parent at the time of download so that the references
            # to this deleted aggregation can be removed from the parent xml files - so need to set metadata to dirty
            parent_aggr.set_metadata_dirty()

        post_remove_file_aggregation.send(
            sender=self.__class__,
            resource=self.resource,
            res_files=self.files.all()
        )

        self.resource.setAVU("bag_modified", True)
        self.resource.setAVU('metadata_dirty', 'true')

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(AbstractModelLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()
        self.create_metadata_schema_json_file()

    def create_metadata_schema_json_file(self):
        """Creates aggregation metadata schema json file """

        if not self.metadata_schema_json:
            return

        # create a temp dir where the json file will be temporarily saved before copying to iRODS
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_irods_storage()

        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)

        # create json schema file for the aggregation
        json_from_file_name = os.path.join(tmpdir, 'schema.json')
        try:
            with open(json_from_file_name, 'w') as out:
                json_schema = json.dumps(self.metadata_schema_json, indent=4)
                out.write(json_schema)
            to_file_name = self.schema_file_path
            istorage.saveFile(json_from_file_name, to_file_name, True)
        finally:
            shutil.rmtree(tmpdir)

    def can_be_deleted_on_file_delete(self):
        """model aggregation based on folder is not deleted on delete of any or all of the resource files that
        are part of the model aggregation"""
        return self.folder is None

    @classmethod
    def can_set_folder_to_aggregation(cls, resource, dir_path, aggregations=None):
        """helper to check if the specified folder *dir_path* can be set to ModelProgram or ModelInstance aggregation
        """

        # checking target folder for any aggregation
        if resource.get_folder_aggregation_object(dir_path, aggregations=aggregations) is not None:
            # target folder is already an aggregation
            return False

        aggregation_path = dir_path
        if dir_path.startswith(resource.file_path):
            aggregation_path = dir_path[len(resource.file_path) + 1:]

        # checking sub-folders for fileset aggregation
        # check that we don't have any sub folder of dir_path representing a fileset aggregation
        # so that we can avoid nesting a fileset aggregation inside a model program or model instance aggregation
        if resource.filesetlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        if cls.__name__ == "ModelProgramLogicalFile":
            # checking sub-folders for model program aggregation
            # check that we don't have any sub folder of dir_path representing a model program aggregation
            # so that we can avoid nesting a model program aggregation inside a model
            # program aggregation
            if resource.modelprogramlogicalfile_set.filter(folder__startswith=aggregation_path).exists():
                return False

        # checking sub-folders for model instance aggregation
        # check that we don't have any sub folder of dir_path representing a model instance aggregation
        # so that we can avoid nesting a model instance aggregation inside a model program aggregation
        if resource.modelinstancelogicalfile_set.filter(folder__startswith=aggregation_path).exists():
            return False

        # check the first parent folder that represents an aggregation
        irods_path = dir_path

        # get the parent folder path
        path = os.path.dirname(dir_path)
        parent_aggregation = None
        while '/' in path:
            if path == resource.file_path:
                break
            parent_aggregation = resource.get_folder_aggregation_object(path, aggregations=aggregations)
            if parent_aggregation is not None:
                # this is the first parent folder that represents an aggregation
                break
            # get the next parent folder path
            path = os.path.dirname(path)

        if parent_aggregation is not None:
            if parent_aggregation.is_fileset:
                # check that all resource files under the target folder 'dir_path' are associated with fileset only
                files_in_path = ResourceFile.list_folder(resource, folder=irods_path, sub_folders=True)
                # if all the resource files are associated with fileset then we can set the folder to model program
                # or model instance aggregation
                if files_in_path:
                    return all(res_file.has_logical_file and res_file.logical_file.is_fileset for
                               res_file in files_in_path)
                return False
            else:
                return False
        else:
            # none of the parent folders represents an aggregation
            # check the files in the target path
            files_in_path = ResourceFile.list_folder(resource, folder=irods_path, sub_folders=True)

            if files_in_path:
                # if none of the resource files in the target path has logical file then we can set the folder
                # to model program or model instance aggregation
                if cls.__name__ == "ModelProgramLogicalFile":
                    # if none of the resource files in the target path has logical file then we can set the folder
                    # to model program aggregation
                    return not any(res_file.has_logical_file for res_file in files_in_path)
                else:
                    # if any of the files is part of a model instance aggr or fileset - folder can't be
                    # set to model instance
                    return not any(res_file.has_logical_file and (res_file.logical_file.is_model_instance
                                                                  or res_file.logical_file.is_fileset) for
                                   res_file in files_in_path)

            # path has no files - can't set the folder to aggregation
            return False
