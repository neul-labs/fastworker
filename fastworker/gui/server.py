"""HTTP Management Server for FastWorker Control Plane GUI."""

import json
import logging
import os
import queue
import socketserver
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from fastworker.utils.event_bus import EventBus
    from fastworker.workers.control_plane import ControlPlaneWorker

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """HTTP server that handles each request in a new thread."""

    allow_reuse_address = True
    daemon_threads = True


class ManagementRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for management GUI."""

    directory = STATIC_DIR
    control_plane: Optional["ControlPlaneWorker"] = None
    event_bus: Optional["EventBus"] = None
    api_key: Optional[str] = None
    allowed_origins: str = "*"

    def log_message(self, format, *args):
        logger.debug(f"GUI HTTP: {args[0]}")

    def _check_auth(self) -> bool:
        """Check Bearer token auth for write endpoints. Returns True if allowed."""
        if not self.api_key:
            return True
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:] == self.api_key
        return False

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", self.allowed_origins)

    def _send_json_response(self, data: Dict[str, Any], status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors()
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_error_response(self, message: str, status: int = 400):
        self._send_json_response({"error": message}, status)

    def _send_static_file(self, filepath: str):
        mime_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }

        ext = os.path.splitext(filepath)[1].lower()
        content_type = mime_types.get(ext, "application/octet-stream")

        try:
            safe_path = os.path.normpath(os.path.join(STATIC_DIR, filepath.lstrip("/")))
            if not safe_path.startswith(STATIC_DIR):
                self.send_error(403, "Forbidden")
                return

            with open(safe_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            if not filepath.startswith("/api/"):
                try:
                    index_path = os.path.join(STATIC_DIR, "index.html")
                    with open(index_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", len(content))
                    self.end_headers()
                    self.wfile.write(content)
                except FileNotFoundError:
                    self.send_error(404, "File not found")
            else:
                self.send_error(404, "File not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def translate_path(self, path):
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        path = os.path.normpath(path)
        return os.path.join(STATIC_DIR, path.lstrip("/"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/events":
            self._handle_sse()
        elif path == "/api/status":
            self._handle_status()
        elif path == "/api/workers":
            self._handle_workers()
        elif path == "/api/tasks":
            self._handle_tasks(query)
        elif path == "/api/cache":
            self._handle_cache_stats()
        elif path == "/api/queues":
            self._handle_queue_stats()
        elif path == "/api/registered-tasks":
            self._handle_registered_tasks()
        elif path.startswith("/api/"):
            self.send_error(404, "API endpoint not found")
        else:
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Require auth for write endpoints
        if not self._check_auth():
            self._send_error_response("Unauthorized — invalid or missing API key", 401)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_error_response("Invalid JSON body", 400)
            return

        if path.startswith("/api/tasks/") and path.endswith("/cancel"):
            task_id = path.split("/")[3]
            self._handle_cancel(task_id)
        elif path.startswith("/api/tasks/") and path.endswith("/retry"):
            task_id = path.split("/")[3]
            self._handle_retry(task_id)
        else:
            self.send_error(404, "API endpoint not found")

    def _handle_sse(self):
        """Server-Sent Events endpoint for real-time updates."""
        cp = self.control_plane
        if not cp or not self.event_bus:
            self.send_error(503, "Event bus not available")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._set_cors()
        self.end_headers()

        # Create a thread-safe queue and register with the event bus
        t_queue: queue.Queue = queue.Queue()
        self.server.sse_queues.append(t_queue)

        try:
            while True:
                try:
                    event = t_queue.get(timeout=15)
                    event_name = event.get("name", "unknown")
                    event_data = json.dumps(event.get("data", {}), default=str)

                    self.wfile.write(f"event: {event_name}\n".encode())
                    self.wfile.write(f"data: {event_data}\n\n".encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Send keepalive comment
                    self.wfile.write(": heartbeat\n\n".encode())
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            logger.debug("SSE client disconnected")
        finally:
            if t_queue in self.server.sse_queues:
                self.server.sse_queues.remove(t_queue)

    def _handle_cancel(self, task_id: str):
        """Cancel a task by ID (POST endpoint)."""
        cp = self.control_plane
        if not cp:
            self._send_error_response("Control plane not available", 503)
            return

        cancelled = cp._handle_cancel(task_id) if hasattr(cp, "_handle_cancel") else False
        if cancelled:
            self._send_json_response({"task_id": task_id, "cancelled": True})
        else:
            self._send_error_response(f"Task {task_id} not found or already terminal", 404)

    def _handle_retry(self, task_id: str):
        """Retry a failed task by ID (POST endpoint)."""
        cp = self.control_plane
        if not cp:
            self._send_error_response("Control plane not available", 503)
            return

        entry = cp.result_cache.get(task_id)
        if not entry:
            self._send_error_response(f"Task {task_id} not found", 404)
            return

        result = entry.get("result")
        if not result or result.status.value != "failure":
            self._send_error_response("Task is not in a retryable state", 400)
            return

        # Re-queue the task by creating a new one and submitting it
        from fastworker.tasks.models import TaskPriority

        cp.active_tasks.pop(task_id, None)
        cp._cancel_events.pop(task_id, None)
        cp.task_queue[TaskPriority.NORMAL].append(result)

        self._send_json_response({"task_id": task_id, "retrying": True})

    def _handle_status(self):
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane
        active_workers = sum(1 for w in cp.subworkers.values() if w["status"] == "active")
        inactive_workers = len(cp.subworkers) - active_workers
        total_queued = sum(len(q) for q in cp.task_queue.values())

        status = {
            "worker_id": cp.worker_id,
            "running": cp.running,
            "base_address": cp.base_address,
            "discovery_address": cp.discovery_address,
            "uptime_seconds": None,
            "subworkers": {
                "total": len(cp.subworkers),
                "active": active_workers,
                "inactive": inactive_workers,
            },
            "tasks": {
                "queued": total_queued,
                "active": len(cp.active_tasks),
                "cached_results": len(cp.result_cache),
            },
            "cache": {
                "max_size": cp.result_cache_max_size,
                "current_size": len(cp.result_cache),
                "ttl_seconds": cp.result_cache_ttl_seconds,
            },
            "timestamp": datetime.now().isoformat(),
        }

        self._send_json_response(status)

    def _handle_workers(self):
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane
        workers = []

        workers.append(
            {
                "id": cp.worker_id,
                "address": cp.base_address,
                "status": "active" if cp.running else "inactive",
                "load": len(cp.active_tasks),
                "last_seen": datetime.now().isoformat(),
                "registered_at": None,
                "is_control_plane": True,
            }
        )

        for worker_id, info in cp.subworkers.items():
            workers.append(
                {
                    "id": worker_id,
                    "address": info["address"],
                    "status": info["status"],
                    "load": info["load"],
                    "last_seen": (
                        info["last_seen"].isoformat()
                        if isinstance(info["last_seen"], datetime)
                        else str(info["last_seen"])
                    ),
                    "registered_at": (
                        info.get("registered_at", "").isoformat()
                        if isinstance(info.get("registered_at"), datetime)
                        else str(info.get("registered_at", ""))
                    ),
                    "is_control_plane": False,
                }
            )

        self._send_json_response({"workers": workers, "count": len(workers)})

    def _handle_tasks(self, query: Dict):
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        limit = int(query.get("limit", [50])[0])
        offset = int(query.get("offset", [0])[0])
        status_filter = query.get("status", [None])[0]

        tasks = []
        cache_items = list(self.control_plane.result_cache.items())

        filtered_items = cache_items
        if status_filter:
            filtered_items = [
                (tid, entry)
                for tid, entry in cache_items
                if entry["result"].status.value == status_filter
            ]

        total = len(filtered_items)
        paginated = filtered_items[offset : offset + limit]

        for task_id, entry in paginated:
            result = entry["result"]
            tasks.append(
                {
                    "task_id": task_id,
                    "status": result.status.value,
                    "result": str(result.result)[:100] if result.result else None,
                    "error": result.error,
                    "started_at": (result.started_at.isoformat() if result.started_at else None),
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                    "cached_at": entry["stored_at"].isoformat(),
                    "last_accessed": entry["last_accessed"].isoformat(),
                }
            )

        self._send_json_response({"tasks": tasks, "total": total, "limit": limit, "offset": offset})

    def _handle_cache_stats(self):
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane
        status_counts = {}
        for entry in cp.result_cache.values():
            status = entry["result"].status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        stats = {
            "max_size": cp.result_cache_max_size,
            "current_size": len(cp.result_cache),
            "utilization_percent": (
                (len(cp.result_cache) / cp.result_cache_max_size * 100)
                if cp.result_cache_max_size > 0
                else 0
            ),
            "ttl_seconds": cp.result_cache_ttl_seconds,
            "by_status": status_counts,
        }

        self._send_json_response(stats)

    def _handle_queue_stats(self):
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane
        queues = {}
        for priority, task_q in cp.task_queue.items():
            queues[priority.value] = {
                "count": len(task_q),
                "tasks": [{"id": task.id, "name": task.name} for task in list(task_q)[:10]],
            }

        self._send_json_response(
            {
                "queues": queues,
                "total_queued": sum(len(q) for q in cp.task_queue.values()),
            }
        )

    def _handle_registered_tasks(self):
        from fastworker.tasks.registry import task_registry

        tasks = []
        for name in task_registry.list_tasks():
            task_func = task_registry.get_task(name)
            task_info = {
                "name": name,
                "module": task_func.__module__ if task_func else None,
                "doc": (task_func.__doc__.strip() if task_func and task_func.__doc__ else None),
            }
            tasks.append(task_info)

        self._send_json_response({"tasks": tasks, "count": len(tasks)})


class ManagementServer:
    """HTTP server for management GUI."""

    def __init__(
        self,
        control_plane: "ControlPlaneWorker",
        host: str = "127.0.0.1",
        port: int = 8080,
        event_bus: Optional["EventBus"] = None,
    ):
        self.control_plane = control_plane
        self.host = host
        self.port = port
        self.event_bus = event_bus
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False
        self.sse_queues: list[queue.Queue] = []

        self.api_key = os.getenv("FASTWORKER_GUI_API_KEY")
        self.allowed_origins = os.getenv("FASTWORKER_GUI_CORS_ORIGIN", "*")

    def start(self):
        if self._running:
            return

        handler_class = type(
            "CustomHandler",
            (ManagementRequestHandler,),
            {
                "control_plane": self.control_plane,
                "event_bus": self.event_bus,
                "api_key": self.api_key,
                "allowed_origins": self.allowed_origins,
                "directory": STATIC_DIR,
            },
        )

        try:
            self.server = ThreadingHTTPServer((self.host, self.port), handler_class)
            # Attach SSE queues to the server for thread-safe access
            self.server.sse_queues = self.sse_queues
            self._running = True

            # Start background task to bridge EventBus → SSE queues
            if self.event_bus:
                threading.Thread(target=self._bridge_events, daemon=True).start()

            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            logger.info(f"Management GUI started at http://{self.host}:{self.port}")

        except OSError as e:
            logger.error(f"Failed to start management server: {e}")
            raise

    def _bridge_events(self):
        """Bridge asyncio EventBus events to thread-safe queues for SSE clients."""
        import asyncio

        async def bridge():
            async for event in self.event_bus.subscribe():
                for q in list(self.sse_queues):
                    try:
                        q.put_nowait(event)
                    except queue.Full:
                        pass

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bridge())
        except Exception as e:
            logger.debug(f"Event bridge ended: {e}")

    def stop(self):
        self._running = False
        if self.server:
            self.server.shutdown()
            self.server = None
        logger.info("Management GUI stopped")
