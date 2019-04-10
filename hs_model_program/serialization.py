import rdflib

from django.db import transaction

from hs_core.serialization import GenericResourceMeta
from hs_core.hydroshare.date_util import hs_date_to_datetime, hs_date_to_datetime_iso, HsDateException

class ModelProgramResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of ModelProgramResource instances.
    """
    def __init__(self):
        super(ModelProgramResourceMeta, self).__init__()

        self.modelVersion = None  # Optional
        self.modelProgramLanguage = None  # Optional
        self.modelOperatingSystem = None  # Optional
        self.modelReleaseDate = None  # Optional
        self.modelWebsite = None  # Optional
        self.modelCodeRepository = None  # Optional
        self.modelReleaseNotes = None  # Optional
        self.modelDocumentation = None  # Optional
        self.modelSoftware = None  # Optional

    def __str__(self):
        msg = "ModelProgramResourceMeta software_version: {software_version}, "
        msg += "modelVersion: {modelProgramLanguage}, "
        msg += "modelOperatingSystem: {modelOperatingSystem}, modelReleaseDate: {modelReleaseDate}, "
        msg += "modelWebsite: {modelWebsite}, modelCodeRepository: {modelCodeRepository}, "
        msg += "modelReleaseNotes: {modelReleaseNotes}, modelDocumentation: {modelDocumentation}, "
        msg = msg.format(modelVersion=self.modelVersion,
                         modelProgramLanguage=self.modelProgramLanguage,
                         modelOperatingSystem=self.modelOperatingSystem, modelReleaseDate=self.modelReleaseDate,
                         modelWebsite=self.modelWebsite, modelCodeRepository=self.modelCodeRepository,
                         modelReleaseNotes=self.modelReleaseNotes, modelDocumentation=self.modelDocumentation,
                         modelSoftware=self.modelSoftware)
        return msg

    def __unicode__(self):
        return unicode(str(self))

    def _read_resource_metadata(self):
        super(ModelProgramResourceMeta, self)._read_resource_metadata()

        print("--- ModelProgramResource ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get Model program metadata (MpMetadata)
        for s, p, o in self._rmeta_graph.triples((None, hsterms.MpMetadata, None)):
            # Get software_version
            software_version_lit = self._rmeta_graph.value(o, hsterms.software_version)
            if software_version_lit is not None:
                self.software_version = str(software_version_lit).strip()
                if self.software_version == '':
                    self.software_version = None
            # Get modelProgramLanguage
            modelProgramLanguage_lit = self._rmeta_graph.value(o, hsterms.modelProgramLanguage)
            if modelProgramLanguage_lit is not None:
                self.modelProgramLanguage = str(modelProgramLanguage_lit).strip()
                if self.modelProgramLanguage == '':
                    self.modelProgramLanguage = None
            # Get modelOperatingSystem
            modelOperatingSystem_lit = self._rmeta_graph.value(o, hsterms.modelOperatingSystem)
            if modelOperatingSystem_lit is not None:
                self.modelOperatingSystem = str(modelOperatingSystem_lit).strip()
                if self.modelOperatingSystem == '':
                    self.modelOperatingSystem = None
            # Get modelReleaseDate
            modelReleaseDate_lit = self._rmeta_graph.value(o, hsterms.modelReleaseDate)
            if modelReleaseDate_lit is not None:
                modelReleaseDate_str = str(modelReleaseDate_lit).strip()
                if modelReleaseDate_str != '':
                    try:
                        self.modelReleaseDate = hs_date_to_datetime(modelReleaseDate_str)
                    except HsDateException:
                        try:
                            self.modelReleaseDate = hs_date_to_datetime_iso(modelReleaseDate_str)
                        except HsDateException as e:
                            msg = "Unable to parse date {0}, error: {1}".format(str(modelReleaseDate_lit),
                                                                                str(e))
                            raise GenericResourceMeta.ResourceMetaException(msg)
            # Get modelWebsite
            modelWebsite_lit = self._rmeta_graph.value(o, hsterms.modelWebsite)
            if modelWebsite_lit is not None:
                self.modelWebsite = str(modelWebsite_lit).strip()
                if self.modelWebsite == '':
                    self.modelWebsite = None
            # Get modelReleaseNotes
            modelReleaseNotes_lit = self._rmeta_graph.value(o, hsterms.modelReleaseNotes)
            if modelReleaseNotes_lit is not None:
                self.modelReleaseNotes = str(modelReleaseNotes_lit).strip()
                if self.modelReleaseNotes == '':
                    self.modelReleaseNotes = None
            # Get modelDocumentation
            modelDocumentation_lit = self._rmeta_graph.value(o, hsterms.modelDocumentation)
            if modelDocumentation_lit is not None:
                self.modelDocumentation = str(modelDocumentation_lit).strip()
                if self.modelDocumentation == '':
                    self.modelDocumentation = None
            # Get modelSoftware
            modelSoftware_lit = self._rmeta_graph.value(o, hsterms.modelSoftware)
            if modelSoftware_lit is not None:
                self.modelSoftware = str(modelSoftware_lit).strip()
                if self.modelSoftware == '':
                    self.modelSoftware = None
            print("\t\t{0}".format(str(self)))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: ModelProgramResource instance
        """
        super(ModelProgramResourceMeta, self).write_metadata_to_resource(resource)

        if self.software_version:
            resource.metadata._mpmetadata.update(software_version=self.software_version)
        if self.modelProgramLanguage:
            resource.metadata._mpmetadata.update(modelProgramLanguage=self.modelProgramLanguage)
        if self.modelOperatingSystem:
            resource.metadata._mpmetadata.update(modelOperatingSystem=self.modelOperatingSystem)
        if self.modelReleaseDate:
            resource.metadata._mpmetadata.update(modelReleaseDate=self.modelReleaseDate)
        if self.modelWebsite:
            resource.metadata._mpmetadata.update(modelWebsite=self.modelWebsite)
        if self.modelCodeRepository:
            resource.metadata._mpmetadata.update(modelCodeRepository=self.modelCodeRepository)
        if self.modelReleaseNotes:
            resource.metadata._mpmetadata.update(modelReleaseNotes=self.modelReleaseNotes)
        if self.modelDocumentation:
            resource.metadata._mpmetadata.update(modelDocumentation=self.modelDocumentation)
        if self.modelSoftware:
            resource.metadata._mpmetadata.update(modelSoftware=self.modelSoftware)
