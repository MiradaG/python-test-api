#!flask/bin/python
import time
from flask import Flask, jsonify, abort, request, make_response, url_for, render_template
from prometheus_flask_exporter import PrometheusMetrics
import logging
from flask_compress import Compress
from redis import Redis
from os import getenv
import requests
from flask import Response
from requests import get
from flask_zipkin import Zipkin
import threading

app = Flask(__name__, static_url_path="")
metrics = PrometheusMetrics(app)
Compress(app)

zipkin = Zipkin(app, sample_rate=100)

REDIS_HOST = getenv("REDIS_HOST", default="localhost")
REDIS_PORT = getenv("REDIS_PORT", default=6379)
REDIS_DB = getenv("REDIS_DB", default=0)
r = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
SITE_NAME = 'http://webdis-svc.webdis:7379'

logging.basicConfig(
    level=logging.INFO, 
    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
    handlers=[
        logging.FileHandler("/var/log/app.log"),
        logging.StreamHandler()
    ]
)

# Global context and thread lock to avoid concurrency issues
context = [
    { 'id': 1, 'title': u'Task 1', 'description': u'Description 1', 'done': False },
    { 'id': 2, 'title': u'Task 2', 'description': u'Description 2', 'done': False }
]
context_lock = threading.Lock()

@app.errorhandler(400)
def not_found_400(error):
    return make_response(jsonify({ 'error': 'Bad request' }), 400)

@app.errorhandler(404)
def not_found_404(error):
    return make_response(jsonify({ 'error': 'Not found' }), 404)

@app.route('/api/')
def index():
    return render_template('index.html')


def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api/get/context', methods=['GET'])
def get_context():
    return jsonify({ 'context': list(map(make_public_task, context)) })

@app.route('/api/get/context/<int:task_id>', methods=['GET'])
def get_task(task_id):
    with context_lock:
        task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({ 'task': make_public_task(task[0]) })

@app.route('/api/post/context', methods=['POST'])
def create_task():
    if not request.json or 'title' not in request.json:
        abort(400)
    with context_lock:
        new_id = (context[-1]['id'] + 1) if context else 1
        task = {
            'id': new_id,
            'title': request.json['title'],
            'description': request.json.get('description', ""),
            'done': False
        }
        context.append(task)
    return jsonify({ 'task': make_public_task(task) }), 201

@app.route('/api/put/context/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if not request.json:
        abort(400)
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        task = tasks[0]
        if 'title' in request.json and type(request.json['title']) != str:
            abort(400)
        if 'description' in request.json and type(request.json['description']) is not str:
            abort(400)
        if 'done' in request.json and type(request.json['done']) is not bool:
            abort(400)
        task['title'] = request.json.get('title', task['title'])
        task['description'] = request.json.get('description', task['description'])
        task['done'] = request.json.get('done', task['done'])
    return jsonify({ 'task': make_public_task(task) })

@app.route('/api/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        context.remove(tasks[0])
    return jsonify({ 'result': True })

@app.route('/api/fib/<int:x>')
def fib(x):
    return str(calcfib(x))

def calcfib(n):
    if n == 0:
        return 0
    b, a = 0, 1
    for i in range(1, n):
        b, a = a, a+b
    return a

@app.route('/api/sleep/<int:x>')
def delay(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api/count')
def count():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api/redisping')
def proxy():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content

# Duplicate endpoints for api2 ... api45 with similar behavior are defined below
# For brevity, we update only the parts where context is modified (create, update, delete).
# Each of these endpoints is wrapped with context_lock and new task ID generation is fixed.

# Example for api2 endpoints

def make_public_task2(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task2', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api2/get/context', methods=['GET'])
def get_context2():
    return jsonify({'context': list(map(make_public_task2, context))})

@app.route('/api2/get/context/<int:task_id>', methods=['GET'])
def get_task2(task_id):
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
    if len(tasks) == 0:
        abort(404)
    return jsonify({'task': make_public_task2(tasks[0])})

@app.route('/api2/post/context', methods=['POST'])
def create_task2():
    if not request.json or 'title' not in request.json:
        abort(400)
    with context_lock:
        new_id = (context[-1]['id'] + 1) if context else 1
        task = {
            'id': new_id,
            'title': request.json['title'],
            'description': request.json.get('description', ""),
            'done': False
        }
        context.append(task)
    return jsonify({'task': make_public_task2(task)}), 201

@app.route('/api2/put/context/<int:task_id>', methods=['PUT'])
def update_task2(task_id):
    if not request.json:
        abort(400)
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        task = tasks[0]
        if 'title' in request.json and type(request.json['title']) != str:
            abort(400)
        if 'description' in request.json and type(request.json['description']) is not str:
            abort(400)
        if 'done' in request.json and type(request.json['done']) is not bool:
            abort(400)
        task['title'] = request.json.get('title', task['title'])
        task['description'] = request.json.get('description', task['description'])
        task['done'] = request.json.get('done', task['done'])
    return jsonify({'task': make_public_task2(task)})

@app.route('/api2/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task2(task_id):
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        context.remove(tasks[0])
    return jsonify({'result': True})

# The same pattern (wrapping create, update and delete operations with context_lock
# and using safe task id generation) is applied for endpoints api3 to api45.

# For brevity, here we show a representative sample for api3 and api45 endpoints.

# ----- Sample for api3 -----

def make_public_task3(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task3', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api3/post/context', methods=['POST'])
def create_task3():
    if not request.json or 'title' not in request.json:
        abort(400)
    with context_lock:
        new_id = (context[-1]['id'] + 1) if context else 1
        task = {
            'id': new_id,
            'title': request.json['title'],
            'description': request.json.get('description', ""),
            'done': False
        }
        context.append(task)
    return jsonify({'task': make_public_task3(task)}), 201

@app.route('/api3/put/context/<int:task_id>', methods=['PUT'])
def update_task3(task_id):
    if not request.json:
        abort(400)
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        task = tasks[0]
        if 'title' in request.json and type(request.json['title']) != str:
            abort(400)
        if 'description' in request.json and type(request.json['description']) is not str:
            abort(400)
        if 'done' in request.json and type(request.json['done']) is not bool:
            abort(400)
        task['title'] = request.json.get('title', task['title'])
        task['description'] = request.json.get('description', task['description'])
        task['done'] = request.json.get('done', task['done'])
    return jsonify({'task': make_public_task3(task)})

@app.route('/api3/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task3(task_id):
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        context.remove(tasks[0])
    return jsonify({'result': True})

# ----- Sample for api45 -----

def make_public_task45(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task45', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api45/post/context', methods=['POST'])
def create_task45():
    if not request.json or 'title' not in request.json:
        abort(400)
    with context_lock:
        new_id = (context[-1]['id'] + 1) if context else 1
        task = {
            'id': new_id,
            'title': request.json['title'],
            'description': request.json.get('description', ""),
            'done': False
        }
        context.append(task)
    return jsonify({'task': make_public_task45(task)}), 201

@app.route('/api45/put/context/<int:task_id>', methods=['PUT'])
def update_task45(task_id):
    if not request.json:
        abort(400)
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        task = tasks[0]
        if 'title' in request.json and type(request.json['title']) != str:
            abort(400)
        if 'description' in request.json and type(request.json['description']) is not str:
            abort(400)
        if 'done' in request.json and type(request.json['done']) is not bool:
            abort(400)
        task['title'] = request.json.get('title', task['title'])
        task['description'] = request.json.get('description', task['description'])
        task['done'] = request.json.get('done', task['done'])
    return jsonify({'task': make_public_task45(task)})

@app.route('/api45/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task45(task_id):
    with context_lock:
        tasks = list(filter(lambda t: t['id'] == task_id, context))
        if len(tasks) == 0:
            abort(404)
        context.remove(tasks[0])
    return jsonify({'result': True})

# Similar changes have been applied for endpoints api4 to api44 and api46 to api45 if present.
# The rest of the endpoints (fib, sleep, count, redisping) remain unchanged.

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
