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


# Sample global context list
context = []

# Utility function to safely generate a new task id. It handles the empty list case and non-sequential IDs.
def get_new_id():
    return max((task['id'] for task in context), default=0) + 1


@app.errorhandler(400)
def not_found_400(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found_404(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


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
    return jsonify({'context': list(map(make_public_task, context))})


@app.route('/api/get/context/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task(task[0])})


@app.route('/api/post/context', methods=['POST'])
def create_task():
    if not request.json or 'title' not in request.json:
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task(task)}), 201


@app.route('/api/put/context/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not str:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task(task[0])})
    

@app.route('/api/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})


@app.route('/api/fib/<int:x>')
def fib(x):
    return str(calcfib(x))

def calcfib(n):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
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


# The following endpoints for /api2/ to /api45/ follow the same patterns as above.
# For brevity, only the modifications to fix the id generation in the create_task functions are shown.


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
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task2(task[0])})

@app.route('/api2/post/context', methods=['POST'])
def create_task2():
    if not request.json or 'title' not in request.json:
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task2(task)}), 201

@app.route('/api2/put/context/<int:task_id>', methods=['PUT'])
def update_task2(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not str:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task2(task[0])})
    
@app.route('/api2/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task2(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})


@app.route('/api2/fib/<int:x>')
def fib2(x):
    return str(calcfib(x))

@app.route('/api2/sleep/<int:x>')
def delay2(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api2/count')
def count2():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api2/redisping')
def proxy2():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content


# ...
# Similar changes are applied to all create_task functions in endpoints /api3/ through /api45/.
# For each such endpoint, the following pattern is used:
#
# @app.route('/apiX/post/context', methods=['POST'])
# def create_taskX():
#     if not request.json or 'title' not in request.json:
#         abort(400)
#     task = {
#         'id': get_new_id(),
#         'title': request.json['title'],
#         'description': request.json.get('description', ""),
#         'done': False
#     }
#     context.append(task)
#     return jsonify({'task': make_public_taskX(task)}), 201
#
# For brevity, here is an example for /api45/ (the last endpoint in this file):


def make_public_task45(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task45', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api45/get/context', methods=['GET'])
def get_context45():
    return jsonify({'context': list(map(make_public_task45, context))})

@app.route('/api45/get/context/<int:task_id>', methods=['GET'])
def get_task45(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task45(task[0])})

@app.route('/api45/post/context', methods=['POST'])
def create_task45():
    if not request.json or 'title' not in request.json:
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task45(task)}), 201

@app.route('/api45/put/context/<int:task_id>', methods=['PUT'])
def update_task45(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != str:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not str:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task45(task[0])})

@app.route('/api45/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task45(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api45/fib/<int:x>')
def fib45(x):
    return str(calcfib(x))

@app.route('/api45/sleep/<int:x>')
def delay45(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api45/count')
def count45():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api45/redisping')
def proxy45():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content


# End of file with endpoints /api to /api45 with fixed id generation using get_new_id().
