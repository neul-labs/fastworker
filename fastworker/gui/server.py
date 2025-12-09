"""HTTP Management Server for FastWorker Control Plane GUI."""

import json
import logging
import os
import socketserver
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from typing import TYPE_CHECKING, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import threading

if TYPE_CHECKING:
    from fastworker.workers.control_plane import ControlPlaneWorker

logger = logging.getLogger(__name__)

# Get the directory where static files are stored
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """HTTP server that handles each request in a new thread."""

    allow_reuse_address = True
    daemon_threads = True


class ManagementRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for management GUI."""

    # Set the directory for static files
    directory = STATIC_DIR

    # Reference to control plane worker (set by server)
    control_plane: Optional["ControlPlaneWorker"] = None

    def log_message(self, format, *args):
        """Override to use Python logging."""
        logger.debug(f"GUI HTTP: {args[0]}")

    def _send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_static_file(self, filepath: str):
        """Serve a static file."""
        # Map file extensions to MIME types
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
            # Prevent directory traversal
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
            # For SPA routing, serve index.html for non-API routes
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
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def translate_path(self, path):
        """Translate URL path to filesystem path, using STATIC_DIR as root."""
        # Remove query string and fragment
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]

        # Normalize path
        path = os.path.normpath(path)

        # Join with static directory
        return os.path.join(STATIC_DIR, path.lstrip("/"))

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API endpoints
        if path == "/api/status":
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
            # Serve static files using SimpleHTTPRequestHandler
            # For root path, serve index.html
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

    def _handle_status(self):
        """Get overall control plane status."""
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane

        # Count active vs inactive subworkers
        active_workers = sum(
            1 for w in cp.subworkers.values() if w["status"] == "active"
        )
        inactive_workers = len(cp.subworkers) - active_workers

        # Calculate queue depths
        total_queued = sum(len(q) for q in cp.task_queue.values())

        status = {
            "worker_id": cp.worker_id,
            "running": cp.running,
            "base_address": cp.base_address,
            "discovery_address": cp.discovery_address,
            "uptime_seconds": None,  # Could be added later
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
        """Get worker information including control plane."""
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane
        workers = []

        # Add control plane as a worker (it processes tasks too)
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

        # Add subworkers
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
        """Get task information from cache."""
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        # Get pagination params
        limit = int(query.get("limit", [50])[0])
        offset = int(query.get("offset", [0])[0])
        status_filter = query.get("status", [None])[0]

        tasks = []
        cache_items = list(self.control_plane.result_cache.items())

        # Apply filters and pagination
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
                    "started_at": (
                        result.started_at.isoformat() if result.started_at else None
                    ),
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                    "cached_at": entry["stored_at"].isoformat(),
                    "last_accessed": entry["last_accessed"].isoformat(),
                }
            )

        self._send_json_response(
            {"tasks": tasks, "total": total, "limit": limit, "offset": offset}
        )

    def _handle_cache_stats(self):
        """Get cache statistics."""
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane

        # Count by status
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
        """Get queue statistics."""
        if not self.control_plane:
            self._send_json_response({"error": "Control plane not available"}, 503)
            return

        cp = self.control_plane

        queues = {}
        for priority, queue in cp.task_queue.items():
            queues[priority.value] = {
                "count": len(queue),
                "tasks": [
                    {"id": task.id, "name": task.name}
                    for task in list(queue)[:10]  # First 10 tasks
                ],
            }

        self._send_json_response(
            {
                "queues": queues,
                "total_queued": sum(len(q) for q in cp.task_queue.values()),
            }
        )

    def _handle_registered_tasks(self):
        """Get registered task definitions."""
        from fastworker.tasks.registry import task_registry

        tasks = []
        for name in task_registry.list_tasks():
            task_func = task_registry.get_task(name)
            task_info = {
                "name": name,
                "module": task_func.__module__ if task_func else None,
                "doc": (
                    task_func.__doc__.strip()
                    if task_func and task_func.__doc__
                    else None
                ),
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
    ):
        self.control_plane = control_plane
        self.host = host
        self.port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start the management server in a background thread."""
        if self._running:
            return

        # Create custom handler class with control plane reference and static directory
        handler_class = type(
            "CustomHandler",
            (ManagementRequestHandler,),
            {"control_plane": self.control_plane, "directory": STATIC_DIR},
        )

        try:
            self.server = ThreadingHTTPServer((self.host, self.port), handler_class)
            self._running = True

            # Run server in background thread using serve_forever
            self.thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.thread.start()

            logger.info(f"Management GUI started at http://{self.host}:{self.port}")

        except OSError as e:
            logger.error(f"Failed to start management server: {e}")
            raise

    def stop(self):
        """Stop the management server."""
        self._running = False
        if self.server:
            self.server.shutdown()
            self.server = None
        logger.info("Management GUI stopped")
