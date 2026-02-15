import json
import uuid
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from django.conf import settings

try:
    from confluent_kafka import Producer
except Exception:
    Producer = None

logger = logging.getLogger(__name__)

DEFAULT_BOOTSTRAP = getattr(settings, "REDPANDA_BOOTSTRAP", "redpanda:9092")
DEFAULT_TOPIC = getattr(settings, "JOBS_REQUESTS_TOPIC", "jobs.requests")
PUBLISH_TIMEOUT = float(getattr(settings, "KAFKA_PUBLISH_TIMEOUT", 5.0))
PUBLISH_RETRIES = int(getattr(settings, "KAFKA_PUBLISH_RETRIES", 3))
PUBLISH_BACKOFF = float(getattr(settings, "KAFKA_PUBLISH_BACKOFF", 1.0))


class ProducerWrapper:
    """Kafka producer with retries and logging."""

    def __init__(self, bootstrap: str = DEFAULT_BOOTSTRAP):
        self._producer = None
        if Producer is None:
            logger.warning("confluent_kafka.Producer not available in this environment")
            return
        try:
            self._producer = Producer({"bootstrap.servers": bootstrap})
            logger.debug("Initialized Kafka Producer with bootstrap %s", bootstrap)
        except Exception as exc:
            logger.error("Failed to initialize Kafka Producer: %s", exc)
            self._producer = None

    def is_available(self) -> bool:
        return self._producer is not None

    def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """Publish message to topic with retries."""
        if not self.is_available():
            raise RuntimeError("Kafka Producer not available")
        payload = json.dumps(message).encode("utf-8")
        last_exc: Optional[Exception] = None
        for attempt in range(1, PUBLISH_RETRIES + 1):
            try:
                self._producer.produce(topic, payload)
                self._producer.flush(timeout=PUBLISH_TIMEOUT)
                logger.debug("Published message to %s (job_id=%s)", topic, message.get("job_id"))
                return
            except Exception as exc:
                last_exc = exc
                logger.warning("Publish attempt %d to %s failed: %s", attempt, topic, exc)
                time.sleep(PUBLISH_BACKOFF * attempt)
        logger.error("Failed to publish message to %s after %d attempts", topic, PUBLISH_RETRIES)
        raise RuntimeError(f"Failed to publish message: {last_exc}")


def build_job_request(
    job_type: str,
    resource_id: Optional[str] = None,
    requested_by: str = "system",
    input_data: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a job request dict for jobs.requests."""
    if job_id is None:
        job_id = str(uuid.uuid4())
    msg: Dict[str, Any] = {
        "v": 1,
        "job_id": job_id,
        "job_type": job_type,
        "requested_by": requested_by,
        "input": input_data or {},
        "requested_at": datetime.utcnow().isoformat() + "Z",
    }
    if resource_id:
        msg["resource_id"] = resource_id
    if correlation_id:
        msg["correlation_id"] = correlation_id
    return msg


producer = ProducerWrapper()

