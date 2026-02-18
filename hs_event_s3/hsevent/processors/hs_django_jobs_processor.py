import redpanda_connect
import asyncio
import json
import logging
import django
import threading

django.setup()
from django.utils import timezone
from hs_core.jobs.producer import producer
from hs_core.models import JobStatus
from hs_core.task_utils import get_or_create_task_notification

logger = logging.getLogger("hs_django_jobs_processor")

try:
    import hs_core.jobs.handlers as handlers
except Exception as e:
    logger.exception("Error loading job handlers: %s", e)
    handlers = None


def publish_job_status(job_id, state, **extra_fields):
    message = {"v": 1, "job_id": job_id, "state": state}
    message.update(extra_fields)
    try:
        producer.publish("jobs.status", message)
    except Exception as e:
        logger.exception("Error publishing jobs.status for %s (%s): %s", job_id, state, e)


def notify_task(task_id, status, name, payload):
    try:
        get_or_create_task_notification(task_id=task_id, status=status, name=name, payload=payload)
    except Exception as e:
        logger.exception("Error creating task notification for %s (%s): %s", task_id, status, e)


def parse_job(payload):
    if isinstance(payload, memoryview):
        payload = payload.tobytes()
    try:
        job = json.loads(payload)
    except Exception:
        logger.debug("Skipping non-JSON jobs payload")
        return None
    if not isinstance(job, dict) or not job.get("job_id") or not job.get("job_type"):
        logger.debug("Skipping jobs payload without job_id/job_type")
        return None
    return job


def task_name_for_job(job_type):
    if job_type == "unpack_zip":
        return "file unzip"
    return job_type


def set_failed(job_id, job_type, error_msg):
    task_name = task_name_for_job(job_type)
    error_text = str(error_msg) if error_msg else "Unknown error"
    try:
        js = JobStatus.objects.filter(job_id=job_id).first()
        if not js:
            js = JobStatus(
                job_id=job_id,
                job_type=job_type,
                requested_at=timezone.now(),
                state="failed",
                error=error_text,
            )
        else:
            js.state = "failed"
            js.error = error_text
            js.updated_at = timezone.now()
        js.save()
    except Exception as e:
        logger.exception("Error setting JobStatus failed for %s: %s", job_id, e)

    publish_job_status(job_id, "failed", error=error_text)
    notify_task(task_id=job_id, status="failed", name=task_name, payload=error_text)


def process_job(job):
    job_id = job["job_id"]
    job_type = job["job_type"]
    task_name = task_name_for_job(job_type)
    resource_id = job.get("resource_id") or job.get("resource") or ""
    payload = f"/resource/{resource_id}" if resource_id else ""

    try:
        js = JobStatus.objects.filter(job_id=job_id).first()
        if js and js.state == "succeeded":
            return

        if not js:
            js = JobStatus(
                job_id=job_id,
                job_type=job_type,
                requested_by=job.get("requested_by", ""),
                requested_at=timezone.now(),
                state="requested",
            )
            js.save()

        js.state = "processing"
        js.updated_at = timezone.now()
        js.save()

        publish_job_status(
            job_id,
            "processing",
            message="starting",
            updated_at=js.updated_at.isoformat() + "Z",
        )
        notify_task(task_id=job_id, status="progress", name=task_name, payload=payload)

        handler_name = f"handle_{job_type}"
        if not handlers or not hasattr(handlers, handler_name):
            raise RuntimeError(f"No handler for job_type={job_type}")
        handler = getattr(handlers, handler_name)
        handler(job, producer=producer)

        js.refresh_from_db()
        if js.state in ("failed", "cancelled"):
            raise RuntimeError(js.error or f"job {job_id} ended in {js.state}")

        if js.state != "succeeded":
            js.state = "succeeded"
            js.updated_at = timezone.now()
            js.save()
            publish_job_status(job_id, "succeeded")
            notify_task(task_id=job_id, status="completed", name=task_name, payload=payload)
    except Exception as e:
        logger.exception("Error processing job %s: %s", job_id, e)
        set_failed(job_id=job_id, job_type=job_type, error_msg=str(e))


@redpanda_connect.processor
def handle_job_message(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    job = parse_job(msg.payload)
    if not job:
        return msg

    job_id = job["job_id"]
    job_type = job["job_type"]
    logger.info("jobs_processor: received job_id=%s job_type=%s", job_id, job_type)

    # Run the Django job in a separate thread, but don’t mark the message as done until the work finishes.
    sync_thread = threading.Thread(target=process_job, args=(job,), daemon=True)
    sync_thread.start()
    sync_thread.join()
    return msg


if __name__ == "__main__":
    asyncio.run(redpanda_connect.processor_main(handle_job_message))
