# Management GUI

FastWorker includes a built-in web dashboard for real-time monitoring of your task queue system. The GUI starts automatically with the control plane - no additional setup required.

## Overview

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

You can also configure the GUI using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTWORKER_GUI_ENABLED` | `true` | Enable/disable the GUI (`true`, `false`, `1`, `0`, `yes`, `no`) |
| `FASTWORKER_GUI_HOST` | `127.0.0.1` | GUI server host address |
| `FASTWORKER_GUI_PORT` | `8080` | GUI server port |

```bash
# Using environment variables
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

- **Critical** - Highest priority tasks (processed first)
- **High** - High priority tasks
- **Normal** - Default priority tasks
- **Low** - Lowest priority tasks (processed last)

Each queue shows:
- Task count with progress bar
- Preview of next tasks in queue

### Task Results Table

Displays cached task results with:

- **Task ID** - Unique task identifier (click to copy)
- **Status** - Success, failure, pending, or started
- **Result** - Task return value or error message
- **Completed At** - When the task finished
- **Cached At** - When the result was stored

Features:
- Pagination for large result sets
- Status color coding
- Click-to-copy task IDs

## REST API

The GUI server also exposes a REST API for programmatic access:

### Endpoints

#### GET /api/status

Returns overall control plane status.

```json
{
  "worker_id": "control-plane",
  "running": true,
  "base_address": "tcp://127.0.0.1:5555",
  "discovery_address": "tcp://127.0.0.1:5550",
  "subworkers": {
    "total": 2,
    "active": 2,
    "inactive": 0
  },
  "tasks": {
    "queued": 5,
    "active": 1,
    "cached_results": 150
  },
  "cache": {
    "max_size": 10000,
    "current_size": 150,
    "ttl_seconds": 3600
  },
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

#### GET /api/workers

Returns subworker information.

```json
{
  "workers": [
    {
      "id": "subworker1",
      "address": "tcp://127.0.0.1:5561",
      "status": "active",
      "load": 2,
      "last_seen": "2024-01-15T10:29:55.000000",
      "registered_at": "2024-01-15T09:00:00.000000"
    }
  ],
  "count": 1
}
```

#### GET /api/queues

Returns queue statistics.

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

#### GET /api/cache

Returns cache statistics.

```json
{
  "max_size": 10000,
  "current_size": 150,
  "utilization_percent": 1.5,
  "ttl_seconds": 3600,
  "by_status": {
    "success": 140,
    "failure": 10
  }
}
```

#### GET /api/tasks

Returns cached task results with pagination.

Query parameters:
- `limit` - Number of results (default: 50)
- `offset` - Starting offset (default: 0)
- `status` - Filter by status (optional)

```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "success",
      "result": "8",
      "error": null,
      "started_at": "2024-01-15T10:29:50.000000",
      "completed_at": "2024-01-15T10:29:51.000000",
      "cached_at": "2024-01-15T10:29:51.000000",
      "last_accessed": "2024-01-15T10:30:00.000000"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

## Security Considerations

### Network Binding

By default, the GUI binds to `127.0.0.1` (localhost only). This prevents remote access.

To allow remote access:

```bash
# Bind to all interfaces (use with caution)
fastworker control-plane --gui-host 0.0.0.0 --task-modules mytasks
```

**Warning:** When exposing the GUI to a network:
- Use a reverse proxy (nginx, Caddy) with authentication
- Consider firewall rules to restrict access
- The GUI has no built-in authentication

### Recommended Production Setup

```bash
# 1. Keep GUI on localhost
fastworker control-plane --gui-host 127.0.0.1 --gui-port 8080 --task-modules mytasks

# 2. Use nginx as reverse proxy with authentication
# nginx.conf example:
# location /fastworker/ {
#     auth_basic "FastWorker Admin";
#     auth_basic_user_file /etc/nginx/.htpasswd;
#     proxy_pass http://127.0.0.1:8080/;
# }
```

## Customizing the GUI

The GUI is built with Vue.js and TailwindCSS. To customize:

### Rebuilding the Frontend

```bash
cd fastworker/gui/frontend

# Install dependencies
npm install

# Development mode with hot reload
npm run dev

# Build for production
npm run build
# or use the build script
./build.sh
```

### Frontend Structure

```
fastworker/gui/frontend/
├── src/
│   ├── App.vue              # Main application
│   ├── main.js              # Entry point
│   ├── style.css            # TailwindCSS styles
│   └── components/
│       ├── StatsCard.vue    # Metric cards
│       ├── WorkersPanel.vue # Subworker list
│       ├── QueuesPanel.vue  # Queue visualization
│       └── TasksTable.vue   # Task results table
├── package.json             # Dependencies
├── vite.config.js           # Build configuration
└── tailwind.config.js       # TailwindCSS configuration
```

## Troubleshooting

### GUI Not Starting

1. **Port already in use**
   ```bash
   # Use a different port
   fastworker control-plane --gui-port 9000 --task-modules mytasks
   ```

2. **Check logs for errors**
   ```bash
   fastworker control-plane --log-level DEBUG --task-modules mytasks
   ```

### Cannot Access GUI Remotely

1. **Bind to all interfaces**
   ```bash
   fastworker control-plane --gui-host 0.0.0.0 --task-modules mytasks
   ```

2. **Check firewall rules**
   ```bash
   # Allow port 8080
   sudo ufw allow 8080/tcp
   ```

### GUI Shows Stale Data

The GUI auto-refreshes every 5 seconds. If data appears stale:

1. Click the refresh button in the header
2. Check browser console for errors
3. Verify control plane is running
