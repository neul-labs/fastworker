# Framework Integration

FastWorker is framework-agnostic and works with any Python web framework that supports async operations.

## Framework Compatibility

| Framework | Async Support | Complexity | Recommended |
|-----------|--------------|------------|-------------|
| FastAPI | Native | Easy | Yes |
| Sanic | Native | Easy | Yes |
| Quart | Native | Easy | Yes |
| Tornado | Native | Easy | Yes |
| Flask 2.0+ | Native | Easy | Yes |
| Flask < 2.0 | Threading | Medium | With threading |
| Django 3.1+ | Native | Medium | Yes |
| Django < 3.1 | Threading | Hard | With threading |

## Flask Integration

### Flask with async/await (Flask 2.0+)

```python
from flask import Flask, request, jsonify
from fastworker import Client

app = Flask(__name__)
client = Client()

@app.before_serving
async def startup():
    await client.start()

@app.after_serving
async def shutdown():
    client.stop()

@app.route('/process/', methods=['POST'])
async def process_data():
    data = request.get_json()
    task_id = await client.delay("process_data", data)
    return jsonify({"task_id": task_id})

@app.route('/result/<task_id>', methods=['GET'])
async def get_result(task_id):
    result = await client.get_task_result(task_id)
    if result:
        return jsonify({"status": result.status, "result": result.result})
    return jsonify({"error": "Result not found"}), 404
```

### Flask with Threading (Traditional)

```python
from flask import Flask, request, jsonify
from fastworker import Client
import asyncio
import threading

app = Flask(__name__)
client = Client()
loop = None

def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop).result()

def start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

@app.before_first_request
def startup():
    global loop
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    run_async(client.start())

@app.route('/process/', methods=['POST'])
def process_data():
    data = request.get_json()
    task_id = run_async(client.delay("process_data", data))
    return jsonify({"task_id": task_id})
```

## Django Integration

### Django Async Views (Django 3.1+)

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from fastworker import Client
import json

client = Client()

@require_http_methods(["POST"])
async def process_data(request):
    data = json.loads(request.body)
    task_id = await client.delay("process_data", data)
    return JsonResponse({"task_id": task_id})

@require_http_methods(["GET"])
async def get_result(request, task_id):
    result = await client.get_task_result(task_id)
    if result:
        return JsonResponse({"status": result.status, "result": result.result})
    return JsonResponse({"error": "Result not found"}, status=404)
```

### Django App Configuration

```python
# apps.py
from django.apps import AppConfig
from fastworker import Client
import asyncio

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
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

```python
from sanic import Sanic, response
from fastworker import Client

app = Sanic("MyApp")
client = Client()

@app.before_server_start
async def setup_client(app, loop):
    await client.start()

@app.after_server_stop
async def cleanup_client(app, loop):
    client.stop()

@app.post("/process/")
async def process_data(request):
    data = request.json
    task_id = await client.delay("process_data", data)
    return response.json({"task_id": task_id})

@app.get("/result/<task_id>")
async def get_result(request, task_id):
    result = await client.get_task_result(task_id)
    if result:
        return response.json({"status": result.status, "result": result.result})
    return response.json({"error": "Result not found"}, status=404)
```

## Quart Integration

```python
from quart import Quart, request, jsonify
from fastworker import Client

app = Quart(__name__)
client = Client()

@app.before_serving
async def startup():
    await client.start()

@app.after_serving
async def shutdown():
    client.stop()

@app.route('/process/', methods=['POST'])
async def process_data():
    data = await request.get_json()
    task_id = await client.delay("process_data", data)
    return jsonify({"task_id": task_id})

@app.route('/result/<task_id>', methods=['GET'])
async def get_result(task_id):
    result = await client.get_task_result(task_id)
    if result:
        return jsonify({"status": result.status, "result": result.result})
    return jsonify({"error": "Result not found"}), 404
```

## Tornado Integration

```python
import tornado.ioloop
import tornado.web
from fastworker import Client
import json

client = Client()

class ProcessHandler(tornado.web.RequestHandler):
    async def post(self):
        data = json.loads(self.request.body)
        task_id = await client.delay("process_data", data)
        self.write({"task_id": task_id})

class ResultHandler(tornado.web.RequestHandler):
    async def get(self, task_id):
        result = await client.get_task_result(task_id)
        if result:
            self.write({"status": result.status, "result": result.result})
        else:
            self.set_status(404)
            self.write({"error": "Result not found"})

async def startup():
    await client.start()

def make_app():
    return tornado.web.Application([
        (r"/process/", ProcessHandler),
        (r"/result/([^/]+)", ResultHandler),
    ])

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(startup)
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()
```

## Standalone Python Script

```python
from fastworker import Client
import asyncio

async def main():
    client = Client()
    await client.start()

    try:
        # Submit multiple tasks
        tasks = []
        for i in range(10):
            task_id = await client.delay("process_number", i)
            tasks.append(task_id)
            print(f"Submitted task {i}: {task_id}")

        # Wait for processing
        await asyncio.sleep(2)

        # Get results
        for task_id in tasks:
            result = await client.get_task_result(task_id)
            if result:
                print(f"Task {task_id}: {result.result}")

    finally:
        client.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

## Best Practices

### 1. Client Lifecycle

Always start the client on application startup and stop on shutdown:

```python
# Startup
await client.start()

# Shutdown
client.stop()
```

### 2. Singleton Pattern

Create a single client instance:

```python
# Good - single instance
client = Client()

# Bad - multiple instances per request
```

### 3. Error Handling

```python
try:
    task_id = await client.delay("my_task", data)
    result = await client.get_task_result(task_id)
    if result and result.status == "success":
        return result.result
except Exception as e:
    print(f"Error: {e}")
```

### 4. Configuration

Use environment variables:

```python
import os

client = Client(
    discovery_address=os.getenv("FASTWORKER_DISCOVERY", "tcp://127.0.0.1:5550"),
    timeout=int(os.getenv("FASTWORKER_TIMEOUT", "30"))
)
```
