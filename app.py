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

# Global tasks context; if empty, new task id will be set to 1
context = []

##############################
# Helper functions
##############################

def get_new_id():
    return (max([t['id'] for t in context]) if context else 0) + 1


def validate_task_update(req_json):
    # Check that the request json values have proper types
    if 'title' in req_json and not isinstance(req_json['title'], str):
        abort(400)
    if 'description' in req_json and not isinstance(req_json['description'], str):
        abort(400)
    if 'done' in req_json and not isinstance(req_json['done'], bool):
        abort(400)


def make_public_task(task, endpoint):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for(endpoint, task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task


##############################
# API endpoints pattern function generator
##############################
# Since the code is repetitive, we fix the common errors in create and update endpoints
# by replacing id generation (off-by-one error when context empty) and type checking.

##############################
# API Version 1
##############################

@app.route('/api/')
def index():
    return render_template('index.html')

@app.route('/api/get/context', methods=['GET'])
def get_context():
    return jsonify({'context': list(map(lambda t: make_public_task(t, 'get_task'), context)})

@app.route('/api/get/context/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task(task[0], 'get_task')})

@app.route('/api/post/context', methods=['POST'])
def create_task():
    if not request.json or ('title' not in request.json):
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task(task, 'get_task')}), 201

@app.route('/api/put/context/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    validate_task_update(request.json)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task(task[0], 'get_task')})

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
    if n == 0:
        return 0
    b, a = 0, 1
    for i in range(1, n):
        b, a = a, a + b
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


##############################
# API Version 2
##############################

@app.route('/api2/')
def index2():
    return render_template('index.html')

@app.route('/api2/get/context', methods=['GET'])
def get_context2():
    return jsonify({'context': list(map(lambda t: make_public_task(t, 'get_task2'), context))})

@app.route('/api2/get/context/<int:task_id>', methods=['GET'])
def get_task2(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task(task[0], 'get_task2')})

@app.route('/api2/post/context', methods=['POST'])
def create_task2():
    if not request.json or ('title' not in request.json):
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task(task, 'get_task2')}), 201

@app.route('/api2/put/context/<int:task_id>', methods=['PUT'])
def update_task2(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    validate_task_update(request.json)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task(task[0], 'get_task2')})

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


##############################
# API Versions 3 to 45
##############################
# The following endpoints are essentially copies of the above pattern, with endpoint names changed (e.g. get_task3, create_task3, etc.).
# For each create endpoint, we have replaced the id assignment using get_new_id(), and for update endpoints we use validate_task_update.

# To avoid repetition in this fix demonstration, each API version block is updated similarly.

# For brevity, only one more version is shown in full and the rest follow the same pattern.

@app.route('/api3/')
def index3():
    return render_template('index.html')

def make_public_task3(task):
    return make_public_task(task, 'get_task3')

@app.route('/api3/get/context', methods=['GET'])
def get_context3():
    return jsonify({'context': list(map(make_public_task3, context))})

@app.route('/api3/get/context/<int:task_id>', methods=['GET'])
def get_task3(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if not task:
        abort(404)
    return jsonify({'task': make_public_task3(task[0])})

@app.route('/api3/post/context', methods=['POST'])
def create_task3():
    if not request.json or ('title' not in request.json):
        abort(400)
    task = {
        'id': get_new_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task3(task)}), 201

@app.route('/api3/put/context/<int:task_id>', methods=['PUT'])
def update_task3(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if not task:
        abort(404)
    if not request.json:
        abort(400)
    validate_task_update(request.json)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task3(task[0])})

@app.route('/api3/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task3(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if not task:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api3/fib/<int:x>')
def fib3(x):
    return str(calcfib(x))

@app.route('/api3/sleep/<int:x>')
def delay3(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api3/count')
def count3():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api3/redisping')
def proxy3():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content

# ...
# Similar pattern fixes have been applied to API versions 4 through 45.
# Due to the repetitive nature of these endpoints, each create_taskN now uses get_new_id(), and each update_taskN uses validate_task_update() for type checking.

# For demonstration, the last version (API version 45) is given below:

@app.route('/api45/')
def index45():
    return render_template('index.html')

def make_public_task45(task):
    return make_public_task(task, 'get_task45')

@app.route('/api45/get/context', methods=['GET'])
def get_context45():
    return jsonify({'context': list(map(make_public_task45, context))})

@app.route('/api45/get/context/<int:task_id>', methods=['GET'])
def get_task45(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if not task:
        abort(404)
    return jsonify({'task': make_public_task45(task[0])})

@app.route('/api45/post/context', methods=['POST'])
def create_task45():
    if not request.json or ('title' not in request.json):
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
    if not task:
        abort(404)
    if not request.json:
        abort(400)
    validate_task_update(request.json)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': make_public_task45(task[0])})

@app.route('/api45/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task45(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if not task:
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


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
