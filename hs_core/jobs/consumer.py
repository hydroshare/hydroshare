#!/usr/bin/env python3
"""Consume jobs.requests and dispatch to handlers."""
import json
import logging
import os
import signal
import time
from typing import Any, Dict, Optional

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")
import django  # noqa: E402

django.setup()  # noqa: E402

from django.utils import timezone
from confluent_kafka import Consumer, KafkaError  # type: ignore

from hs_core.jobs.producer import producer
from hs_core.models import JobStatus
from hs_core.hydroshare import utils as hs_utils
from hs_core.task_utils import get_or_create_task_notification

logger = logging.getLogger("job_consumer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class JobConsumer:
    """Subscribe to jobs.requests and dispatch to handlers."""

    def __init__(self, bootstrap: str = "redpanda:9092", group_id: str = "job-consumer"):
        self._running = True
        self.consumer = Consumer(
            {
                "bootstrap.servers": bootstrap,
                "group.id": group_id,
                "enable.auto.commit": False,
                "auto.offset.reset": "earliest",
            }
        )
        self.topic = "jobs.requests"
        try:
            import hs_core.jobs.handlers as handlers  # type: ignore

            self.handlers = handlers
        except Exception:
            self.handlers = None
            logger.debug("No handlers module found.")

    def start(self) -> None:
        logger.info("Subscribing to %s", self.topic)
        self.consumer.subscribe([self.topic])
        while self._running:
            try:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Kafka error: %s", msg.error())
                    continue

                payload = self._parse_message(msg.value())
                if not payload:
                    self.consumer.commit(message=msg)
                    continue

                self._process(payload)
                self.consumer.commit(message=msg)
            except Exception:
                logger.exception("Consumer loop error; retrying shortly")
                time.sleep(1.0)

        self.consumer.close()

    def stop(self) -> None:
        self._running = False

    def _parse_message(self, raw: bytes) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            logger.warning("Failed to parse message")
            return None

    def _process(self, job: Dict[str, Any]) -> None:
        job_id = job.get("job_id")
        job_type = job.get("job_type")
        logger.info("Received job_id=%s job_type=%s", job_id, job_type)

        js = JobStatus.objects.filter(job_id=job_id).first()
        if js and js.state == "succeeded":
            logger.info("Job %s already succeeded; skipping", job_id)
            return

        if not js:
            try:
                js = JobStatus(job_id=job_id, job_type=job_type, requested_by=job.get("requested_by", ""), requested_at=timezone.now(), state="requested")
                js.save()
            except Exception:
                logger.exception("Failed to create JobStatus for %s", job_id)

        try:
            js.state = "processing"
            js.updated_at = timezone.now()
            js.save()
            producer.publish("jobs.status", {"v": 1, "job_id": job_id, "state": "processing", "message": "starting", "updated_at": js.updated_at.isoformat() + "Z"})
        except Exception:
            logger.exception("Failed to set processing for %s", job_id)

        resource_id = job.get("resource_id") or job.get("resource")
        payload = f"/resource/{resource_id}" if resource_id else ""
        try:
            get_or_create_task_notification(task_id=job_id, status="progress", name=job_type, payload=payload)
        except Exception:
            logger.exception("Failed to create/update TaskNotification for %s", job_id)

        # Dispatch to handler
        handler_name = f"handle_{job_type}"
        if self.handlers and hasattr(self.handlers, handler_name):
            try:
                handler = getattr(self.handlers, handler_name)
                handler(job, producer=producer)
            except Exception as exc:
                logger.exception("Handler %s failed for job %s: %s", handler_name, job_id, exc)
                js.state = "failed"
                js.error = str(exc)
                js.updated_at = timezone.now()
                js.save()
                try:
                    producer.publish("jobs.status", {"v": 1, "job_id": job_id, "state": "failed", "error": str(exc)})
                except Exception:
                    logger.exception("Failed to publish failed status for %s", job_id)
                try:
                    get_or_create_task_notification(task_id=job_id, status="failed", name=job_type, payload=payload)
                except Exception:
                    logger.exception("Failed to update TaskNotification for failed job %s", job_id)
        else:
            msg = f"No handler for job_type={job_type}"
            logger.warning(msg)
            js.state = "failed"
            js.error = msg
            js.updated_at = timezone.now()
            js.save()
            try:
                producer.publish("jobs.status", {"v": 1, "job_id": job_id, "state": "failed", "error": msg})
            except Exception:
                logger.exception("Failed to publish failed status for %s", job_id)
            try:
                get_or_create_task_notification(task_id=job_id, status="failed", name=job_type, payload=payload)
            except Exception:
                logger.exception("Failed to update TaskNotification for failed (no handler) %s", job_id)


def _install_signal_handlers(consumer: JobConsumer) -> None:
    def _handle(sig, frame):
        logger.info("Signal %s received, stopping consumer", sig)
        consumer.stop()

    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)


def main() -> None:
    bootstrap = os.environ.get("REDPANDA_BOOTSTRAP", "redpanda:9092")
    group = os.environ.get("JOB_CONSUMER_GROUP", "job-consumer")
    consumer = JobConsumer(bootstrap=bootstrap, group_id=group)
    _install_signal_handlers(consumer)
    consumer.start()


if __name__ == "__main__":
    main()
