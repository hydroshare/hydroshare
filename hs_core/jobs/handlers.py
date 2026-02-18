import logging
import threading
import zipfile
import os
import time

from django.utils import timezone
from django.contrib.auth.models import User

from hs_core.models import JobStatus, ResourceFile
from hs_core.views.utils import unzip_file
from hs_core.hydroshare import utils as hs_utils
from hs_core.task_utils import get_or_create_task_notification

logger = logging.getLogger("job_handlers")


def handle_unpack_zip(job, producer):
    job_id = job.get("job_id")
    inp = job.get("input", {}) or {}
    zip_with_rel_path = inp.get("zip_with_rel_path")
    remove_original = inp.get("remove_original", True)
    overwrite = inp.get("overwrite", False)
    auto_aggregate = inp.get("auto_aggregate", False)
    ingest_metadata = inp.get("ingest_metadata", False)
    unzip_to_folder = inp.get("unzip_to_folder", False)

    js = JobStatus.objects.filter(job_id=job_id).first()
    if not js:
        js = JobStatus(
            job_id=job_id,
            job_type="unpack_zip",
            requested_by=job.get("requested_by", ""),
            requested_at=timezone.now(),
            state="requested",
        )
        js.save()

    js.state = "processing"
    js.updated_at = timezone.now()
    js.save()
    try:
        producer.publish(
            "jobs.status",
            {
                "v": 1,
                "job_id": job_id,
                "state": "processing",
                "message": "starting",
                "updated_at": js.updated_at.isoformat() + "Z",
            },
        )
    except Exception:
        logger.exception("Failed to publish processing status for %s", job_id)

    resource_id = job.get("resource_id") or job.get("resource")
    payload = f"/resource/{resource_id}"
    try:
        get_or_create_task_notification(
            task_id=job_id, status="progress", name="file unzip", payload=payload
        )
    except Exception:
        logger.exception("Failed to create/update TaskNotification for processing")

    # Run unzip and poll ResourceFile count for progress
    try:
        res = hs_utils.get_resource_by_shortkey(resource_id)
        istorage = res.get_s3_storage()
        zip_full_path = os.path.join(res.root_path, zip_with_rel_path)
    except Exception:
        err = f"resource resolution failed for {resource_id}"
        logger.exception(err)
        js.state = "failed"
        js.error = err
        js.updated_at = timezone.now()
        js.save()
        try:
            producer.publish(
                "jobs.status", {"v": 1, "job_id": job_id, "state": "failed", "error": err}
            )
        except Exception:
            logger.exception("Failed to publish failed status for %s", job_id)
        try:
            get_or_create_task_notification(
                task_id=job_id, status="failed", name="file unzip", payload=payload
            )
        except Exception:
            logger.exception("Failed to update TaskNotification for failed job")
        return payload

    total = None
    try:
        with zipfile.ZipFile(istorage.download(zip_full_path)) as zf:
            total = len([i for i in zf.infolist() if not i.is_dir()])
    except Exception:
        total = None

    initial_count = ResourceFile.objects.filter(object_id=res.id).count()

    exc_holder = {}

    def _run_unzip():
        try:
            unzip_file(
                User.objects.first(),
                resource_id,
                zip_with_rel_path,
                remove_original,
                overwrite,
                auto_aggregate,
                ingest_metadata,
                unzip_to_folder,
            )
        except Exception as e:
            exc_holder["exc"] = e

    t = threading.Thread(target=_run_unzip, daemon=True)
    t.start()

    last_published = 0
    publish_every = 5
    last_percent = None
    while t.is_alive():
        time.sleep(2)
        try:
            current = ResourceFile.objects.filter(object_id=res.id).count()
            processed = max(0, current - initial_count)
            if total:
                percent = int(processed / total * 100) if total else None
            else:
                percent = None
            if (
                processed - last_published >= publish_every
                or (percent is not None and percent != last_percent and percent % 5 == 0)
            ):
                last_published = processed
                last_percent = percent
                js.progress = percent if percent is not None else processed
                js.updated_at = timezone.now()
                js.save(update_fields=["progress", "updated_at"])
                msg = {
                    "v": 1,
                    "job_id": job_id,
                    "state": "processing",
                    "progress": percent,
                    "message": f"Imported {processed}",
                }
                try:
                    producer.publish("jobs.status", msg)
                except Exception:
                    logger.exception("Failed to publish progress for %s", job_id)
        except Exception:
            logger.exception("Error while computing progress for %s", job_id)

    if "exc" in exc_holder:
        exc = exc_holder["exc"]
        logger.exception("unpack failed for job %s: %s", job_id, exc)
        js.state = "failed"
        js.error = str(exc)
        js.updated_at = timezone.now()
        js.save()
        try:
            producer.publish(
                "jobs.status", {"v": 1, "job_id": job_id, "state": "failed", "error": str(exc)}
            )
        except Exception:
            logger.exception("Failed to publish failed status for %s", job_id)
        try:
            get_or_create_task_notification(
                task_id=job_id, status="failed", name="file unzip", payload=payload
            )
        except Exception:
            logger.exception("Failed to update TaskNotification for failed job")
        return str(exc)

    js.state = "succeeded"
    js.result_ref = ""
    js.updated_at = timezone.now()
    js.progress = 100
    js.save()
    try:
        producer.publish(
            "jobs.status",
            {"v": 1, "job_id": job_id, "state": "succeeded", "result_ref": js.result_ref},
        )
    except Exception:
        logger.exception("Failed to publish succeeded status for %s", job_id)
    try:
        get_or_create_task_notification(
            task_id=job_id, status="completed", name="file unzip", payload=payload
        )
    except Exception:
        logger.exception("Failed to update TaskNotification for completed job")
    return payload
