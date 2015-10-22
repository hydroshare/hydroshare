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

        self.software_version = None  # Optional
        self.software_language = None  # Optional
        self.operating_sys = None  # Optional
        self.date_released = None  # Optional
        self.program_website = None  # Optional
        self.software_repo = None  # Optional
        self.release_notes = None  # Optional
        self.user_manual = None  # Optional
        self.theoretical_manual = None  # Optional
        self.source_code = None  # Optional

    def __str__(self):
        msg = "ModelProgramResourceMeta software_version: {software_version}, "
        msg += "software_language: {software_language}, "
        msg += "operating_sys: {operating_sys}, date_released: {date_released}, "
        msg += "program_website: {program_website}, software_repo: {software_repo}, "
        msg += "release_notes: {release_notes}, user_manual: {user_manual}, "
        msg += "theoretical_manual: {theoretical_manual}, source_code: {source_code}"
        msg = msg.format(software_version=self.software_version,
                         software_language=self.software_language,
                         operating_sys=self.operating_sys, date_released=self.date_released,
                         program_website=self.program_website, software_repo=self.software_repo,
                         release_notes=self.release_notes, user_manual=self.user_manual,
                         theoretical_manual=self.theoretical_manual,
                         source_code=self.source_code)
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
            # Get software_language
            software_language_lit = self._rmeta_graph.value(o, hsterms.software_language)
            if software_language_lit is not None:
                self.software_language = str(software_language_lit).strip()
                if self.software_language == '':
                    self.software_language = None
            # Get operating_sys
            operating_sys_lit = self._rmeta_graph.value(o, hsterms.operating_sys)
            if operating_sys_lit is not None:
                self.operating_sys = str(operating_sys_lit).strip()
                if self.operating_sys == '':
                    self.operating_sys = None
            # Get date_released
            date_released_lit = self._rmeta_graph.value(o, hsterms.date_released)
            if date_released_lit is not None:
                date_released_str = str(date_released_lit).strip()
                if date_released_str != '':
                    try:
                        self.date_released = hs_date_to_datetime(date_released_str)
                    except HsDateException:
                        try:
                            self.date_released = hs_date_to_datetime_iso(date_released_str)
                        except HsDateException as e:
                            msg = "Unable to parse date {0}, error: {1}".format(str(date_released_lit),
                                                                                str(e))
                            raise GenericResourceMeta.ResourceMetaException(msg)
            # Get program_website
            program_website_lit = self._rmeta_graph.value(o, hsterms.program_website)
            if program_website_lit is not None:
                self.program_website = str(program_website_lit).strip()
                if self.program_website == '':
                    self.program_website = None
            # Get release_notes
            release_notes_lit = self._rmeta_graph.value(o, hsterms.release_notes)
            if release_notes_lit is not None:
                self.release_notes = str(release_notes_lit).strip()
                if self.release_notes == '':
                    self.release_notes = None
            # Get user_manual
            user_manual_lit = self._rmeta_graph.value(o, hsterms.user_manual)
            if user_manual_lit is not None:
                self.user_manual = str(user_manual_lit).strip()
                if self.user_manual == '':
                    self.user_manual = None
            # Get theoretical_manual
            theoretical_manual_lit = self._rmeta_graph.value(o, hsterms.theoretical_manual)
            if theoretical_manual_lit is not None:
                self.theoretical_manual = str(theoretical_manual_lit).strip()
                if self.theoretical_manual == '':
                    self.theoretical_manual = None
            # Get source_code
            source_code_lit = self._rmeta_graph.value(o, hsterms.source_code)
            if source_code_lit is not None:
                self.source_code = str(source_code_lit).strip()
                if self.source_code == '':
                    self.source_code = None
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
        if self.software_language:
            resource.metadata._mpmetadata.update(software_language=self.software_language)
        if self.operating_sys:
            resource.metadata._mpmetadata.update(operating_sys=self.operating_sys)
        if self.date_released:
            resource.metadata._mpmetadata.update(date_released=self.date_released)
        if self.program_website:
            resource.metadata._mpmetadata.update(program_website=self.program_website)
        if self.software_repo:
            resource.metadata._mpmetadata.update(software_repo=self.software_repo)
        if self.release_notes:
            resource.metadata._mpmetadata.update(release_notes=self.release_notes)
        if self.user_manual:
            resource.metadata._mpmetadata.update(user_manual=self.user_manual)
        if self.theoretical_manual:
            resource.metadata._mpmetadata.update(theoretical_manual=self.theoretical_manual)
        if self.source_code:
            resource.metadata._mpmetadata.update(source_code=self.source_code)
