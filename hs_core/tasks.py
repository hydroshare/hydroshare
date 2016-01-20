import tempfile
import zipfile

from celery import shared_task

from hs_core.hydroshare import utils


@shared_task
def add_zip_file_contents_to_resource(pk, zip_file):
    try:
        resource = utils.get_resource_by_shortkey(pk, or_404=False)
        tmp_dir = tempfile.mkdtemp()
        zfile = zipfile.ZipFile(zip_file)
        zcontents = utils.ZipContents(zfile)
        files = zcontents.get_files()

        for f in files:
            utils.add_file_to_resource(resource, f)

        # TODO: Call success callback
    except Exception as e:
        zfile.close()
        # TODO: Call error callback
        raise e
