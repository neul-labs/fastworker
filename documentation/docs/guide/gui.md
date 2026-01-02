# Management GUI

FastWorker includes a built-in web dashboard for real-time monitoring. The GUI starts automatically with the control plane.

## Overview

Access the GUI at: **http://127.0.0.1:8080** (default)

The management GUI provides:

- **Real-time Status** - Monitor control plane health and uptime
- **Worker Monitoring** - Track active/inactive subworkers with load metrics
- **Queue Visualization** - View task counts by priority level
- **Task History** - Browse cached task results with status and timing
- **Cache Statistics** - Monitor result cache utilization

## Quick Start

```bash
# Start control plane with GUI (enabled by default)
fastworker control-plane --task-modules mytasks

# GUI available at http://127.0.0.1:8080
```

## Configuration

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--no-gui` | `false` | Disable the management GUI |
| `--gui-host` | `127.0.0.1` | Host address for the GUI server |
| `--gui-port` | `8080` | Port for the GUI server |

### Examples

```bash
# Default: GUI on localhost:8080
fastworker control-plane --task-modules mytasks

# Custom port
fastworker control-plane --gui-port 9000 --task-modules mytasks

# Allow remote access (bind to all interfaces)
fastworker control-plane --gui-host 0.0.0.0 --gui-port 8080 --task-modules mytasks

# Disable GUI entirely
fastworker control-plane --no-gui --task-modules mytasks
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTWORKER_GUI_ENABLED` | `true` | Enable/disable the GUI |
| `FASTWORKER_GUI_HOST` | `127.0.0.1` | GUI server host address |
| `FASTWORKER_GUI_PORT` | `8080` | GUI server port |

```bash
export FASTWORKER_GUI_HOST=0.0.0.0
export FASTWORKER_GUI_PORT=9000
fastworker control-plane --task-modules mytasks
```

## Dashboard Sections

### Status Overview

The top section displays key metrics:

- **Active Workers** - Number of connected and healthy subworkers
- **Queued Tasks** - Total tasks waiting in all priority queues
- **Cached Results** - Number of task results in the cache
- **Cache Utilization** - Percentage of cache capacity used

### Subworkers Panel

Shows all registered subworkers with:

- **Status** - Active (green) or inactive (red) indicator
- **Worker ID** - Unique identifier for the subworker
- **Address** - Network address of the subworker
- **Load** - Current number of tasks being processed
- **Last Seen** - Time since last heartbeat

### Task Queues Panel

Visualizes task distribution across priority levels:

- **Critical** - Highest priority tasks
- **High** - High priority tasks
- **Normal** - Default priority tasks
- **Low** - Lowest priority tasks

### Task Results Table

Displays cached task results with:

- **Task ID** - Unique task identifier (click to copy)
- **Status** - Success, failure, pending, or started
- **Result** - Task return value or error message
- **Completed At** - When the task finished

## REST API

The GUI server also exposes a REST API for programmatic access.

### GET /api/status

Returns overall control plane status.

```bash
curl http://127.0.0.1:8080/api/status
```

```json
{
  "worker_id": "control-plane",
  "running": true,
  "base_address": "tcp://127.0.0.1:5555",
  "subworkers": {
    "total": 2,
    "active": 2,
    "inactive": 0
  },
  "tasks": {
    "queued": 5,
    "cached_results": 150
  },
  "cache": {
    "max_size": 10000,
    "current_size": 150,
    "ttl_seconds": 3600
  }
}
```

### GET /api/workers

Returns subworker information.

```bash
curl http://127.0.0.1:8080/api/workers
```

```json
{
  "workers": [
    {
      "id": "subworker1",
      "address": "tcp://127.0.0.1:5561",
      "status": "active",
      "load": 2,
      "last_seen": "2024-01-15T10:29:55.000000"
    }
  ],
  "count": 1
}
```

### GET /api/queues

Returns queue statistics.

```bash
curl http://127.0.0.1:8080/api/queues
```

```json
{
  "queues": {
    "critical": {"count": 0, "tasks": []},
    "high": {"count": 1, "tasks": [{"id": "abc123", "name": "urgent_task"}]},
    "normal": {"count": 3, "tasks": [...]},
    "low": {"count": 1, "tasks": [...]}
  },
  "total_queued": 5
}
```

### GET /api/tasks

Returns cached task results with pagination.

```bash
curl "http://127.0.0.1:8080/api/tasks?limit=50&offset=0"
```

Query parameters:

- `limit` - Number of results (default: 50)
- `offset` - Starting offset (default: 0)
- `status` - Filter by status (optional)

## Security

### Default (Localhost Only)

By default, the GUI binds to `127.0.0.1` (localhost only), preventing remote access.

### Enabling Remote Access

```bash
# Bind to all interfaces (use with caution)
fastworker control-plane --gui-host 0.0.0.0 --task-modules mytasks
```

!!! warning
    When exposing the GUI to a network:

    - Use a reverse proxy (nginx, Caddy) with authentication
    - Consider firewall rules to restrict access
    - The GUI has no built-in authentication

### Recommended Production Setup

```bash
# 1. Keep GUI on localhost
fastworker control-plane --gui-host 127.0.0.1 --gui-port 8080 --task-modules mytasks

# 2. Use nginx as reverse proxy with authentication
```

Example nginx config:

```nginx
location /fastworker/ {
    auth_basic "FastWorker Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8080/;
}
```

## Troubleshooting

### GUI Not Starting

**Port already in use:**

```bash
fastworker control-plane --gui-port 9000 --task-modules mytasks
```

### Cannot Access GUI Remotely

**Bind to all interfaces:**

```bash
fastworker control-plane --gui-host 0.0.0.0 --task-modules mytasks
```

**Check firewall:**

```bash
sudo ufw allow 8080/tcp
```

### GUI Shows Stale Data

The GUI auto-refreshes every 5 seconds. If data appears stale:

1. Click the refresh button in the header
2. Check browser console for errors
3. Verify control plane is running
