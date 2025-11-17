# Framework Integration Guide

FastWorker is a **framework-agnostic** task queue that works with any Python web framework or application. The Client is simply an async Python class, making it compatible with FastAPI, Flask, Django, Sanic, and any other framework that supports async operations.

**See Also:**
- [FastAPI Integration](fastapi.md) - Detailed FastAPI integration guide
- [Client Guide](clients.md) - Client API and usage
- [Configuration](configuration.md) - Environment variables
- [Troubleshooting](troubleshooting.md) - Framework-specific issues

## Framework-Agnostic Client

The core Client can be used in any Python application:

```python
from fastworker import Client
import asyncio

async def main():
    # Create and start client
    client = Client()
    await client.start()

    # Submit tasks
    task_id = await client.delay("process_data", {"key": "value"})
    print(f"Task submitted: {task_id}")

    # Get results
    result = await client.get_task_result(task_id)
    if result:
        print(f"Result: {result.result}")

    # Clean up
    client.stop()

asyncio.run(main())
```

## FastAPI Integration

See the dedicated [FastAPI Integration](fastapi.md) guide for comprehensive examples.

### Quick Example

```python
from fastapi import FastAPI
from fastworker import Client

app = FastAPI()
client = Client()

@app.on_event("startup")
async def startup_event():
    await client.start()

@app.on_event("shutdown")
async def shutdown_event():
    client.stop()

@app.post("/process/")
async def process_data(data: dict):
    task_id = await client.delay("process_data", data)
    return {"task_id": task_id}
```

## Flask Integration

Flask can integrate with FastWorker using async support (Flask 2.0+).

### Flask with async/await

```python
from flask import Flask, request, jsonify
from fastworker import Client
import asyncio

app = Flask(__name__)
client = Client()

@app.before_serving
async def startup():
    """Initialize FastWorker client before serving."""
    await client.start()

@app.after_serving
async def shutdown():
    """Clean up FastWorker client after serving."""
    client.stop()

@app.route('/process/', methods=['POST'])
async def process_data():
    """Async endpoint for task submission."""
    data = request.get_json()
    task_id = await client.delay("process_data", data)
    return jsonify({"task_id": task_id})

@app.route('/result/<task_id>', methods=['GET'])
async def get_result(task_id):
    """Async endpoint for result retrieval."""
    result = await client.get_task_result(task_id)
    if result:
        return jsonify({
            "status": result.status,
            "result": result.result
        })
    return jsonify({"error": "Result not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

### Flask with Threading (Traditional Flask)

For traditional Flask without async support:

```python
from flask import Flask, request, jsonify
from fastworker import Client
import asyncio
import threading

app = Flask(__name__)
client = Client()
loop = None

def run_async(coro):
    """Helper to run async code in Flask."""
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

def start_background_loop(loop):
    """Start event loop in background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

@app.before_first_request
def startup():
    """Initialize FastWorker client and event loop."""
    global loop
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    run_async(client.start())

@app.route('/process/', methods=['POST'])
def process_data():
    """Sync endpoint that runs async task submission."""
    data = request.get_json()
    task_id = run_async(client.delay("process_data", data))
    return jsonify({"task_id": task_id})

@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    """Sync endpoint that runs async result retrieval."""
    result = run_async(client.get_task_result(task_id))
    if result:
        return jsonify({
            "status": result.status,
            "result": result.result
        })
    return jsonify({"error": "Result not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

## Django Integration

Django can integrate with FastWorker using async views (Django 3.1+).

### Django Async Views

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from fastworker import Client
import json

client = Client()

# Initialize client when Django starts
async def init_client():
    await client.start()

@require_http_methods(["POST"])
async def process_data(request):
    """Async view for task submission."""
    data = json.loads(request.body)
    task_id = await client.delay("process_data", data)
    return JsonResponse({"task_id": task_id})

@require_http_methods(["GET"])
async def get_result(request, task_id):
    """Async view for result retrieval."""
    result = await client.get_task_result(task_id)
    if result:
        return JsonResponse({
            "status": result.status,
            "result": result.result
        })
    return JsonResponse({"error": "Result not found"}, status=404)
```

### Django App Configuration

```python
# apps.py
from django.apps import AppConfig
from fastworker import Client
import asyncio

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        """Initialize FastWorker client when Django app is ready."""
        client = Client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.start())
```

### Django URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_data, name='process_data'),
    path('result/<str:task_id>/', views.get_result, name='get_result'),
]
```

## Sanic Integration

Sanic has native async support, making it ideal for FastWorker.

```python
from sanic import Sanic, response
from fastworker import Client

app = Sanic("MyApp")
client = Client()

@app.before_server_start
async def setup_client(app, loop):
    """Initialize FastWorker client before server starts."""
    await client.start()

@app.after_server_stop
async def cleanup_client(app, loop):
    """Clean up FastWorker client after server stops."""
    client.stop()

@app.post("/process/")
async def process_data(request):
    """Async endpoint for task submission."""
    data = request.json
    task_id = await client.delay("process_data", data)
    return response.json({"task_id": task_id})

@app.get("/result/<task_id>")
async def get_result(request, task_id):
    """Async endpoint for result retrieval."""
    result = await client.get_task_result(task_id)
    if result:
        return response.json({
            "status": result.status,
            "result": result.result
        })
    return response.json({"error": "Result not found"}, status=404)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
```

## Tornado Integration

Tornado's native async support works seamlessly with FastWorker.

```python
import tornado.ioloop
import tornado.web
from fastworker import Client
import json

client = Client()

class ProcessHandler(tornado.web.RequestHandler):
    async def post(self):
        """Async handler for task submission."""
        data = json.loads(self.request.body)
        task_id = await client.delay("process_data", data)
        self.write({"task_id": task_id})

class ResultHandler(tornado.web.RequestHandler):
    async def get(self, task_id):
        """Async handler for result retrieval."""
        result = await client.get_task_result(task_id)
        if result:
            self.write({
                "status": result.status,
                "result": result.result
            })
        else:
            self.set_status(404)
            self.write({"error": "Result not found"})

async def startup():
    """Initialize FastWorker client."""
    await client.start()

def make_app():
    return tornado.web.Application([
        (r"/process/", ProcessHandler),
        (r"/result/([^/]+)", ResultHandler),
    ])

if __name__ == "__main__":
    # Start client
    tornado.ioloop.IOLoop.current().run_sync(startup)

    # Start server
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
```

## Quart Integration

Quart is an async version of Flask with native async/await support.

```python
from quart import Quart, request, jsonify
from fastworker import Client

app = Quart(__name__)
client = Client()

@app.before_serving
async def startup():
    """Initialize FastWorker client before serving."""
    await client.start()

@app.after_serving
async def shutdown():
    """Clean up FastWorker client after serving."""
    client.stop()

@app.route('/process/', methods=['POST'])
async def process_data():
    """Async endpoint for task submission."""
    data = await request.get_json()
    task_id = await client.delay("process_data", data)
    return jsonify({"task_id": task_id})

@app.route('/result/<task_id>', methods=['GET'])
async def get_result(task_id):
    """Async endpoint for result retrieval."""
    result = await client.get_task_result(task_id)
    if result:
        return jsonify({
            "status": result.status,
            "result": result.result
        })
    return jsonify({"error": "Result not found"}), 404

if __name__ == '__main__':
    app.run()
```

## Standalone Python Script

FastWorker can be used in any Python script:

```python
from fastworker import Client
import asyncio

async def main():
    # Initialize client
    client = Client()
    await client.start()

    try:
        # Submit multiple tasks
        tasks = []
        for i in range(10):
            task_id = await client.delay("process_number", i)
            tasks.append(task_id)
            print(f"Submitted task {i}: {task_id}")

        # Wait a bit for processing
        await asyncio.sleep(2)

        # Get results
        for task_id in tasks:
            result = await client.get_task_result(task_id)
            if result:
                print(f"Task {task_id}: {result.result}")

    finally:
        # Clean up
        client.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

## Best Practices

### 1. Client Lifecycle Management

Always start the client when your application starts and stop it when it shuts down:

```python
# Good
await client.start()  # On startup
# ... use client ...
client.stop()  # On shutdown

# Bad - creating new clients for each request
# Don't do this!
```

### 2. Singleton Pattern

Create a single client instance and reuse it:

```python
# Good - single instance
client = Client()

# Bad - multiple instances
# Don't create new Client() for each request
```

### 3. Error Handling

Always handle potential errors:

```python
try:
    task_id = await client.delay("my_task", data)
    result = await client.get_task_result(task_id)
    if result and result.status == "success":
        return result.result
    else:
        # Handle failure
        return None
except Exception as e:
    # Handle exception
    print(f"Error: {e}")
```

### 4. Configuration

Use environment variables for configuration:

```python
import os

client = Client(
    discovery_address=os.getenv("FASTWORKER_DISCOVERY", "tcp://127.0.0.1:5550"),
    timeout=int(os.getenv("FASTWORKER_TIMEOUT", "30")),
    retries=int(os.getenv("FASTWORKER_RETRIES", "3"))
)
```

## Comparison: Framework Compatibility

| Framework | Async Support | Integration Complexity | Recommended |
|-----------|--------------|----------------------|-------------|
| FastAPI | Native | Easy | ✅ Yes |
| Sanic | Native | Easy | ✅ Yes |
| Quart | Native | Easy | ✅ Yes |
| Tornado | Native | Easy | ✅ Yes |
| Flask 2.0+ | Native | Easy | ✅ Yes |
| Flask < 2.0 | Threading | Medium | ⚠️ With threading |
| Django 3.1+ | Native | Medium | ✅ Yes |
| Django < 3.1 | Threading | Hard | ⚠️ With threading |

## Summary

FastWorker's framework-agnostic design means you can:

1. Use it with any Python web framework
2. Integrate it into existing applications with minimal changes
3. Switch frameworks without changing your task queue logic
4. Use the same client in different parts of your application

The key requirement is async/await support, which is available in all modern Python web frameworks.
