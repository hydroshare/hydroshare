from django.core.management.base import BaseCommand

from hs_core.hydroshare import current_site_url, set_dirty_bag_flag
from hs_core.models import CoreMetaData
from hs_script_resource.models import ScriptResource
from ..utils import migrate_core_meta_elements


class Command(BaseCommand):
    help = "Convert all script resources to composite resource"

    def handle(self, *args, **options):
        resource_counter = 0
        to_resource_type = 'CompositeResource'
        msg = "THERE ARE CURRENTLY {} SCRIPT RESOURCES TO MIGRATE TO COMPOSITE RESOURCE.".format(
            ScriptResource.objects.count())
        print(msg, flush=True)
        for script_res in ScriptResource.objects.all():
            msg = "Migrating script resource:{}".format(script_res.short_id)
            print(msg, flush=True)
            # check resource exists on irods
            istorage = script_res.get_irods_storage()
            if not istorage.exists(script_res.root_path):
                err_msg = "Script resource was not found in iRODS (ID: {})".format(script_res.short_id)
                print("ERROR: {}".format(err_msg), flush=True)
                # skip this script resource for migration
                continue

            # change the resource_type
            script_metadata_obj = script_res.metadata
            script_res.resource_type = to_resource_type
            script_res.content_model = to_resource_type.lower()
            script_res.save()

            # get the converted resource object - CompositeResource
            comp_res = script_res.get_content_model()

            # set CoreMetaData object for the composite resource
            core_meta_obj = CoreMetaData.objects.create()
            comp_res.content_object = core_meta_obj
            # migrate script resource core metadata elements to composite resource
            migrate_core_meta_elements(script_metadata_obj, comp_res)
            # dtarb suggested to add this extended metadata
            comp_res.extra_metadata['Type'] = 'Script'

            # migrate script resource specific metadata as key/value metadata (as suggested by dtarb)
            # to composite resource
            if script_metadata_obj.program:
                script_meta = script_metadata_obj.program
                if script_meta.scriptLanguage:
                    comp_res.extra_metadata['Programming Language'] = script_meta.scriptLanguage
                if script_meta.languageVersion:
                    comp_res.extra_metadata['Programming Language Version'] = script_meta.languageVersion
                if script_meta.scriptVersion:
                    comp_res.extra_metadata['Script Version'] = script_meta.scriptVersion
                if script_meta.scriptDependencies:
                    comp_res.extra_metadata['Script Dependencies'] = script_meta.scriptDependencies
                if script_meta.scriptReleaseDate:
                    release_date = script_meta.scriptReleaseDate.strftime('%m-%d-%Y')
                    comp_res.extra_metadata['Release Date'] = release_date
                if script_meta.scriptCodeRepository:
                    comp_res.extra_metadata['Script Repository'] = script_meta.scriptCodeRepository
            comp_res.save()
            # update url attribute of the metadata 'type' element
            type_element = comp_res.metadata.type
            type_element.url = '{0}/terms/{1}'.format(current_site_url(), to_resource_type)
            type_element.save()

            # set resource to dirty so that resource level xml files (resource map and
            # metadata xml files) will be generated as part of next bag download
            set_dirty_bag_flag(comp_res)
            resource_counter += 1
            msg = "Migrated script resource:{}".format(script_res.short_id)
            print(msg, flush=True)
            # delete the instance of ScriptMetaData that was part of the original script resource
            script_metadata_obj.delete()

        msg = "{} SCRIPT RESOURCES WERE MIGRATED TO COMPOSITE RESOURCE.".format(resource_counter)
        print(msg)
        msg = "THERE ARE CURRENTLY {} SCRIPT RESOURCES AFTER MIGRATION.".format(ScriptResource.objects.count())
        print(msg)

