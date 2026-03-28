import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable

DEFAULT_DEBOUNCE_DELAY_SECONDS = 30.0
DEFAULT_MAX_WAIT_SECONDS = 300.0


@dataclass(frozen=True)
class ManifestRebuildRequest:
    """Describe a single resource-level file manifest rebuild request."""

    resource_id: str
    resource_contents_path: str
    manifest_path: str
    status_path: str
    metadata_path: str


@dataclass
class _PendingManifestRebuild:
    """Track worker-owned timing state for a pending manifest rebuild."""

    request: ManifestRebuildRequest
    first_event_time: float
    last_event_time: float


class ManifestRebuildCoordinator:
    """Coalesce manifest rebuild requests on a single worker thread."""

    def __init__(
        self,
        rebuild_callback: Callable[[ManifestRebuildRequest], None],
        debounce_delay_seconds: float | None = None,
        max_wait_seconds: float | None = None,
    ):
        """Initialize the coordinator with a rebuild callback and timing settings."""
        self._rebuild_callback = rebuild_callback
        self._debounce_delay_seconds = (
            debounce_delay_seconds
            if debounce_delay_seconds is not None
            else float(os.environ.get("HS_EXTRACT_MANIFEST_DEBOUNCE_DELAY_SECONDS", DEFAULT_DEBOUNCE_DELAY_SECONDS))
        )
        self._max_wait_seconds = (
            max_wait_seconds
            if max_wait_seconds is not None
            else float(os.environ.get("HS_EXTRACT_MANIFEST_MAX_WAIT_SECONDS", DEFAULT_MAX_WAIT_SECONDS))
        )
        self._event_queue: queue.Queue[ManifestRebuildRequest] = queue.Queue()
        self._pending_by_resource: dict[str, _PendingManifestRebuild] = {}
        self._startup_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the worker thread if it has not already been started."""
        with self._startup_lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="manifest-rebuild-coordinator",
                daemon=True,
            )
            self._worker_thread.start()

    def stop(self) -> None:
        """Stop the worker thread and wait briefly for it to exit."""
        self._stop_event.set()
        self._event_queue.put(
            ManifestRebuildRequest(
                resource_id="__stop__",
                resource_contents_path="",
                manifest_path="",
                status_path="",
                metadata_path="",
            )
        )
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=1)

    def enqueue(self, request: ManifestRebuildRequest) -> None:
        """Queue a resource for rebuild and ensure the worker is running."""
        self.start()
        self._event_queue.put(request)

    def pending_count(self) -> int:
        """Return the number of distinct pending resource rebuilds."""
        return len(self._pending_by_resource)

    def _merge_request(self, request: ManifestRebuildRequest, now: float) -> None:
        pending = self._pending_by_resource.get(request.resource_id)
        if pending is None:
            self._pending_by_resource[request.resource_id] = _PendingManifestRebuild(
                request=request,
                first_event_time=now,
                last_event_time=now,
            )
            return
        pending.request = request
        pending.last_event_time = now

    def _next_timeout_seconds(self, now: float) -> float:
        if not self._pending_by_resource:
            return 1.0
        wait_times = []
        for pending in self._pending_by_resource.values():
            debounce_due = pending.last_event_time + self._debounce_delay_seconds
            max_wait_due = pending.first_event_time + self._max_wait_seconds
            wait_times.append(max(0.0, min(debounce_due, max_wait_due) - now))
        return min(wait_times) if wait_times else 1.0

    def _pop_ready_requests(self, now: float) -> list[ManifestRebuildRequest]:
        ready_resource_ids = []
        for resource_id, pending in self._pending_by_resource.items():
            debounce_elapsed = now - pending.last_event_time >= self._debounce_delay_seconds
            max_wait_elapsed = now - pending.first_event_time >= self._max_wait_seconds
            if debounce_elapsed or max_wait_elapsed:
                ready_resource_ids.append(resource_id)
        ready_requests = []
        for resource_id in ready_resource_ids:
            ready_requests.append(self._pending_by_resource.pop(resource_id).request)
        return ready_requests

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            timeout = self._next_timeout_seconds(now)
            try:
                request = self._event_queue.get(timeout=timeout)
                if request.resource_id == "__stop__":
                    continue
                self._merge_request(request, time.time())
            except queue.Empty:
                pass

            ready_requests = self._pop_ready_requests(time.time())
            for request in ready_requests:
                self._rebuild_callback(request)