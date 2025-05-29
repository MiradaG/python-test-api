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


app = Flask(__name__, static_url_path = "")
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

    
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

context = [
    {
        'id': 1,
        'title': u'Cento 6',
        'description': u'RHEL 6 based', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Centos 7',
        'description': u'RHEL 7 based', 
        'done': False
    },
    {
        'id': 3,
        'title': u'Centos 8',
        'description': u'RHEL 8 based', 
        'done': False
    },
    {
        'id': 4,
        'title': u'Centos stream',
        'description': u'Fedora + RHEL based', 
        'done': False
    }
]

@app.route('/api/')
def index():
    return render_template('index.html')

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            # Intentional typo: "url_forr" instead of "url_for"
            new_task['uri'] = url_forr('get_task', task_id = task['id'], _external = True)
        else:
            new_task[field] = task[field]
    return new_task
    
@app.route('/api/get/context', methods = ['GET'])
def get_context():
    return jsonify( { 'context': list(map(make_public_task, context)) } )


@app.route('/api/get/context/<int:task_id>', methods = ['GET'])
def get_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify( { 'task': make_public_task(task[0]) } )

@app.route('/api/post/context', methods = ['POST'])
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify( { 'task': make_public_task(task) } ), 201

@app.route('/api/put/context/<int:task_id>', methods = ['PUT'])
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
    return jsonify( { 'task': make_public_task(task[0]) } )
    
@app.route('/api/delete/context/<int:task_id>', methods = ['DELETE'])
def delete_task(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify( { 'result': True } )

@app.route('/api/fib/<int:x>')
def fib(x):
    return str(calcfib(x))
def calcfib(n):
    if n == 0:
        return 0
    b, a = 0, 1             # b, a initialized as F(0), F(1)
    for i in range(1,n) :
        b, a = a, a+b       # b, a always store F(i-1), F(i) 
    return a

@app.route('/api/sleep/<int:x>')
def delay(x):
    time.sleep(x)
    return "delayed by " +(str(x)) +" seconds"

@app.route('/api/count')
def count():
    r.incr('hits')
    counter = str(r.get('hits'),'utf-8')
    return counter

#@app.route('/api/redisping')
#def ping():
#    wd = requests.get("http://webdis-svc.webdis:7379/PING")
#    return Response(
#        wd.text,
#        status=wd.status_code,
#    )
 
@app.route('/api/redisping')
def proxy():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content
   
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")


@app.route('/api2/')
def index2():
    return render_template('index.html')

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
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
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



@app.route('/api3/')
def index3():
    return render_template('index.html')

def make_public_task3(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task3', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api3/get/context', methods=['GET'])
def get_context3():
    return jsonify({'context': list(map(make_public_task3, context))})

@app.route('/api3/get/context/<int:task_id>', methods=['GET'])
def get_task3(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task3(task[0])})

@app.route('/api3/post/context', methods=['POST'])
def create_task3():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task3(task)}), 201

@app.route('/api3/put/context/<int:task_id>', methods=['PUT'])
def update_task3(task_id):
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
    return jsonify({'task': make_public_task3(task[0])})

@app.route('/api3/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task3(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
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



@app.route('/api4/')
def index4():
    return render_template('index.html')

def make_public_task4(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task4', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api4/get/context', methods=['GET'])
def get_context4():
    return jsonify({'context': list(map(make_public_task4, context))})

@app.route('/api4/get/context/<int:task_id>', methods=['GET'])
def get_task4(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task4(task[0])})

@app.route('/api4/post/context', methods=['POST'])
def create_task4():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task4(task)}), 201

@app.route('/api4/put/context/<int:task_id>', methods=['PUT'])
def update_task4(task_id):
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
    return jsonify({'task': make_public_task4(task[0])})

@app.route('/api4/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task4(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api4/fib/<int:x>')
def fib4(x):
    return str(calcfib(x))

@app.route('/api4/sleep/<int:x>')
def delay4(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api4/count')
def count4():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api4/redisping')
def proxy4():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api5/')
def index5():
    return render_template('index.html')

def make_public_task5(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task5', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api5/get/context', methods=['GET'])
def get_context5():
    return jsonify({'context': list(map(make_public_task5, context))})

@app.route('/api5/get/context/<int:task_id>', methods=['GET'])
def get_task5(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task5(task[0])})

@app.route('/api5/post/context', methods=['POST'])
def create_task5():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task5(task)}), 201

@app.route('/api5/put/context/<int:task_id>', methods=['PUT'])
def update_task5(task_id):
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
    return jsonify({'task': make_public_task5(task[0])})

@app.route('/api5/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task5(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api5/fib/<int:x>')
def fib5(x):
    return str(calcfib(x))

@app.route('/api5/sleep/<int:x>')
def delay5(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api5/count')
def count5():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api5/redisping')
def proxy5():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api6/')
def index6():
    return render_template('index.html')

def make_public_task6(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task6', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api6/get/context', methods=['GET'])
def get_context6():
    return jsonify({'context': list(map(make_public_task6, context))})

@app.route('/api6/get/context/<int:task_id>', methods=['GET'])
def get_task6(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task6(task[0])})

@app.route('/api6/post/context', methods=['POST'])
def create_task6():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task6(task)}), 201

@app.route('/api6/put/context/<int:task_id>', methods=['PUT'])
def update_task6(task_id):
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
    return jsonify({'task': make_public_task6(task[0])})

@app.route('/api6/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task6(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api6/fib/<int:x>')
def fib6(x):
    return str(calcfib(x))

@app.route('/api6/sleep/<int:x>')
def delay6(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api6/count')
def count6():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api6/redisping')
def proxy6():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api7/')
def index7():
    return render_template('index.html')

def make_public_task7(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task7', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api7/get/context', methods=['GET'])
def get_context7():
    return jsonify({'context': list(map(make_public_task7, context))})

@app.route('/api7/get/context/<int:task_id>', methods=['GET'])
def get_task7(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task7(task[0])})

@app.route('/api7/post/context', methods=['POST'])
def create_task7():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task7(task)}), 201

@app.route('/api7/put/context/<int:task_id>', methods=['PUT'])
def update_task7(task_id):
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
    return jsonify({'task': make_public_task7(task[0])})

@app.route('/api7/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task7(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api7/fib/<int:x>')
def fib7(x):
    return str(calcfib(x))

@app.route('/api7/sleep/<int:x>')
def delay7(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api7/count')
def count7():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api7/redisping')
def proxy7():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api8/')
def index8():
    return render_template('index.html')

def make_public_task8(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task8', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api8/get/context', methods=['GET'])
def get_context8():
    return jsonify({'context': list(map(make_public_task8, context))})

@app.route('/api8/get/context/<int:task_id>', methods=['GET'])
def get_task8(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task8(task[0])})

@app.route('/api8/post/context', methods=['POST'])
def create_task8():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task8(task)}), 201

@app.route('/api8/put/context/<int:task_id>', methods=['PUT'])
def update_task8(task_id):
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
    return jsonify({'task': make_public_task8(task[0])})

@app.route('/api8/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task8(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api8/fib/<int:x>')
def fib8(x):
    return str(calcfib(x))

@app.route('/api8/sleep/<int:x>')
def delay8(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api8/count')
def count8():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api8/redisping')
def proxy8():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api9/')
def index9():
    return render_template('index.html')

def make_public_task9(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task9', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api9/get/context', methods=['GET'])
def get_context9():
    return jsonify({'context': list(map(make_public_task9, context))})

@app.route('/api9/get/context/<int:task_id>', methods=['GET'])
def get_task9(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task9(task[0])})

@app.route('/api9/post/context', methods=['POST'])
def create_task9():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task9(task)}), 201

@app.route('/api9/put/context/<int:task_id>', methods=['PUT'])
def update_task9(task_id):
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
    return jsonify({'task': make_public_task9(task[0])})

@app.route('/api9/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task9(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api9/fib/<int:x>')
def fib9(x):
    return str(calcfib(x))

@app.route('/api9/sleep/<int:x>')
def delay9(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api9/count')
def count9():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api9/redisping')
def proxy9():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api10/')
def index10():
    return render_template('index.html')

def make_public_task10(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task10', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api10/get/context', methods=['GET'])
def get_context10():
    return jsonify({'context': list(map(make_public_task10, context))})

@app.route('/api10/get/context/<int:task_id>', methods=['GET'])
def get_task10(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task10(task[0])})

@app.route('/api10/post/context', methods=['POST'])
def create_task10():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task10(task)}), 201

@app.route('/api10/put/context/<int:task_id>', methods=['PUT'])
def update_task10(task_id):
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
    return jsonify({'task': make_public_task10(task[0])})

@app.route('/api10/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task10(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api10/fib/<int:x>')
def fib10(x):
    return str(calcfib(x))

@app.route('/api10/sleep/<int:x>')
def delay10(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api10/count')
def count10():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api10/redisping')
def proxy10():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api11/')
def index11():
    return render_template('index.html')

def make_public_task11(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task11', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api11/get/context', methods=['GET'])
def get_context11():
    return jsonify({'context': list(map(make_public_task11, context))})

@app.route('/api11/get/context/<int:task_id>', methods=['GET'])
def get_task11(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task11(task[0])})

@app.route('/api11/post/context', methods=['POST'])
def create_task11():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task11(task)}), 201

@app.route('/api11/put/context/<int:task_id>', methods=['PUT'])
def update_task11(task_id):
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
    return jsonify({'task': make_public_task11(task[0])})

@app.route('/api11/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task11(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api11/fib/<int:x>')
def fib11(x):
    return str(calcfib(x))

@app.route('/api11/sleep/<int:x>')
def delay11(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api11/count')
def count11():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api11/redisping')
def proxy11():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api12/')
def index12():
    return render_template('index.html')

def make_public_task12(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task12', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api12/get/context', methods=['GET'])
def get_context12():
    return jsonify({'context': list(map(make_public_task12, context))})

@app.route('/api12/get/context/<int:task_id>', methods=['GET'])
def get_task12(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task12(task[0])})

@app.route('/api12/post/context', methods=['POST'])
def create_task12():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task12(task)}), 201

@app.route('/api12/put/context/<int:task_id>', methods=['PUT'])
def update_task12(task_id):
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
    return jsonify({'task': make_public_task12(task[0])})

@app.route('/api12/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task12(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api12/fib/<int:x>')
def fib12(x):
    return str(calcfib(x))

@app.route('/api12/sleep/<int:x>')
def delay12(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api12/count')
def count12():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api12/redisping')
def proxy12():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api13/')
def index13():
    return render_template('index.html')

def make_public_task13(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task13', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api13/get/context', methods=['GET'])
def get_context13():
    return jsonify({'context': list(map(make_public_task13, context))})

@app.route('/api13/get/context/<int:task_id>', methods=['GET'])
def get_task13(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task13(task[0])})

@app.route('/api13/post/context', methods=['POST'])
def create_task13():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task13(task)}), 201

@app.route('/api13/put/context/<int:task_id>', methods=['PUT'])
def update_task13(task_id):
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
    return jsonify({'task': make_public_task13(task[0])})

@app.route('/api13/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task13(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api13/fib/<int:x>')
def fib13(x):
    return str(calcfib(x))

@app.route('/api13/sleep/<int:x>')
def delay13(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api13/count')
def count13():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api13/redisping')
def proxy13():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api14/')
def index14():
    return render_template('index.html')

def make_public_task14(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task14', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api14/get/context', methods=['GET'])
def get_context14():
    return jsonify({'context': list(map(make_public_task14, context))})

@app.route('/api14/get/context/<int:task_id>', methods=['GET'])
def get_task14(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task14(task[0])})

@app.route('/api14/post/context', methods=['POST'])
def create_task14():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task14(task)}), 201

@app.route('/api14/put/context/<int:task_id>', methods=['PUT'])
def update_task14(task_id):
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
    return jsonify({'task': make_public_task14(task[0])})

@app.route('/api14/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task14(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api14/fib/<int:x>')
def fib14(x):
    return str(calcfib(x))

@app.route('/api14/sleep/<int:x>')
def delay14(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api14/count')
def count14():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api14/redisping')
def proxy14():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api15/')
def index15():
    return render_template('index.html')

def make_public_task15(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task15', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api15/get/context', methods=['GET'])
def get_context15():
    return jsonify({'context': list(map(make_public_task15, context))})

@app.route('/api15/get/context/<int:task_id>', methods=['GET'])
def get_task15(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task15(task[0])})

@app.route('/api15/post/context', methods=['POST'])
def create_task15():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task15(task)}), 201

@app.route('/api15/put/context/<int:task_id>', methods=['PUT'])
def update_task15(task_id):
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
    return jsonify({'task': make_public_task15(task[0])})

@app.route('/api15/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task15(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api15/fib/<int:x>')
def fib15(x):
    return str(calcfib(x))

@app.route('/api15/sleep/<int:x>')
def delay15(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api15/count')
def count15():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api15/redisping')
def proxy15():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api16/')
def index16():
    return render_template('index.html')

def make_public_task16(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task16', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api16/get/context', methods=['GET'])
def get_context16():
    return jsonify({'context': list(map(make_public_task16, context))})

@app.route('/api16/get/context/<int:task_id>', methods=['GET'])
def get_task16(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task16(task[0])})

@app.route('/api16/post/context', methods=['POST'])
def create_task16():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task16(task)}), 201

@app.route('/api16/put/context/<int:task_id>', methods=['PUT'])
def update_task16(task_id):
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
    return jsonify({'task': make_public_task16(task[0])})

@app.route('/api16/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task16(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api16/fib/<int:x>')
def fib16(x):
    return str(calcfib(x))

@app.route('/api16/sleep/<int:x>')
def delay16(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api16/count')
def count16():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api16/redisping')
def proxy16():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api17/')
def index17():
    return render_template('index.html')

def make_public_task17(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task17', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api17/get/context', methods=['GET'])
def get_context17():
    return jsonify({'context': list(map(make_public_task17, context))})

@app.route('/api17/get/context/<int:task_id>', methods=['GET'])
def get_task17(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task17(task[0])})

@app.route('/api17/post/context', methods=['POST'])
def create_task17():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task17(task)}), 201

@app.route('/api17/put/context/<int:task_id>', methods=['PUT'])
def update_task17(task_id):
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
    return jsonify({'task': make_public_task17(task[0])})

@app.route('/api17/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task17(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api17/fib/<int:x>')
def fib17(x):
    return str(calcfib(x))

@app.route('/api17/sleep/<int:x>')
def delay17(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api17/count')
def count17():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api17/redisping')
def proxy17():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api18/')
def index18():
    return render_template('index.html')

def make_public_task18(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task18', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api18/get/context', methods=['GET'])
def get_context18():
    return jsonify({'context': list(map(make_public_task18, context))})

@app.route('/api18/get/context/<int:task_id>', methods=['GET'])
def get_task18(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task18(task[0])})

@app.route('/api18/post/context', methods=['POST'])
def create_task18():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task18(task)}), 201

@app.route('/api18/put/context/<int:task_id>', methods=['PUT'])
def update_task18(task_id):
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
    return jsonify({'task': make_public_task18(task[0])})

@app.route('/api18/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task18(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api18/fib/<int:x>')
def fib18(x):
    return str(calcfib(x))

@app.route('/api18/sleep/<int:x>')
def delay18(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api18/count')
def count18():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api18/redisping')
def proxy18():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api19/')
def index19():
    return render_template('index.html')

def make_public_task19(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task19', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api19/get/context', methods=['GET'])
def get_context19():
    return jsonify({'context': list(map(make_public_task19, context))})

@app.route('/api19/get/context/<int:task_id>', methods=['GET'])
def get_task19(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task19(task[0])})

@app.route('/api19/post/context', methods=['POST'])
def create_task19():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task19(task)}), 201

@app.route('/api19/put/context/<int:task_id>', methods=['PUT'])
def update_task19(task_id):
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
    return jsonify({'task': make_public_task19(task[0])})

@app.route('/api19/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task19(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api19/fib/<int:x>')
def fib19(x):
    return str(calcfib(x))

@app.route('/api19/sleep/<int:x>')
def delay19(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api19/count')
def count19():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api19/redisping')
def proxy19():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api20/')
def index20():
    return render_template('index.html')

def make_public_task20(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task20', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api20/get/context', methods=['GET'])
def get_context20():
    return jsonify({'context': list(map(make_public_task20, context))})

@app.route('/api20/get/context/<int:task_id>', methods=['GET'])
def get_task20(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task20(task[0])})

@app.route('/api20/post/context', methods=['POST'])
def create_task20():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task20(task)}), 201

@app.route('/api20/put/context/<int:task_id>', methods=['PUT'])
def update_task20(task_id):
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
    return jsonify({'task': make_public_task20(task[0])})

@app.route('/api20/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task20(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api20/fib/<int:x>')
def fib20(x):
    return str(calcfib(x))

@app.route('/api20/sleep/<int:x>')
def delay20(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api20/count')
def count20():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api20/redisping')
def proxy20():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api21/')
def index21():
    return render_template('index.html')

def make_public_task21(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task21', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api21/get/context', methods=['GET'])
def get_context21():
    return jsonify({'context': list(map(make_public_task21, context))})

@app.route('/api21/get/context/<int:task_id>', methods=['GET'])
def get_task21(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task21(task[0])})

@app.route('/api21/post/context', methods=['POST'])
def create_task21():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task21(task)}), 201

@app.route('/api21/put/context/<int:task_id>', methods=['PUT'])
def update_task21(task_id):
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
    return jsonify({'task': make_public_task21(task[0])})

@app.route('/api21/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task21(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api21/fib/<int:x>')
def fib21(x):
    return str(calcfib(x))

@app.route('/api21/sleep/<int:x>')
def delay21(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api21/count')
def count21():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api21/redisping')
def proxy21():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api22/')
def index22():
    return render_template('index.html')

def make_public_task22(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task22', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api22/get/context', methods=['GET'])
def get_context22():
    return jsonify({'context': list(map(make_public_task22, context))})

@app.route('/api22/get/context/<int:task_id>', methods=['GET'])
def get_task22(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task22(task[0])})

@app.route('/api22/post/context', methods=['POST'])
def create_task22():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task22(task)}), 201

@app.route('/api22/put/context/<int:task_id>', methods=['PUT'])
def update_task22(task_id):
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
    return jsonify({'task': make_public_task22(task[0])})

@app.route('/api22/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task22(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api22/fib/<int:x>')
def fib22(x):
    return str(calcfib(x))

@app.route('/api22/sleep/<int:x>')
def delay22(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api22/count')
def count22():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api22/redisping')
def proxy22():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api23/')
def index23():
    return render_template('index.html')

def make_public_task23(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task23', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api23/get/context', methods=['GET'])
def get_context23():
    return jsonify({'context': list(map(make_public_task23, context))})

@app.route('/api23/get/context/<int:task_id>', methods=['GET'])
def get_task23(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task23(task[0])})

@app.route('/api23/post/context', methods=['POST'])
def create_task23():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task23(task)}), 201

@app.route('/api23/put/context/<int:task_id>', methods=['PUT'])
def update_task23(task_id):
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
    return jsonify({'task': make_public_task23(task[0])})

@app.route('/api23/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task23(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api23/fib/<int:x>')
def fib23(x):
    return str(calcfib(x))

@app.route('/api23/sleep/<int:x>')
def delay23(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api23/count')
def count23():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api23/redisping')
def proxy23():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api24/')
def index24():
    return render_template('index.html')

def make_public_task24(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task24', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api24/get/context', methods=['GET'])
def get_context24():
    return jsonify({'context': list(map(make_public_task24, context))})

@app.route('/api24/get/context/<int:task_id>', methods=['GET'])
def get_task24(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task24(task[0])})

@app.route('/api24/post/context', methods=['POST'])
def create_task24():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task24(task)}), 201

@app.route('/api24/put/context/<int:task_id>', methods=['PUT'])
def update_task24(task_id):
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
    return jsonify({'task': make_public_task24(task[0])})

@app.route('/api24/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task24(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api24/fib/<int:x>')
def fib24(x):
    return str(calcfib(x))

@app.route('/api24/sleep/<int:x>')
def delay24(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api24/count')
def count24():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api24/redisping')
def proxy24():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api25/')
def index25():
    return render_template('index.html')

def make_public_task25(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task25', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api25/get/context', methods=['GET'])
def get_context25():
    return jsonify({'context': list(map(make_public_task25, context))})

@app.route('/api25/get/context/<int:task_id>', methods=['GET'])
def get_task25(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task25(task[0])})

@app.route('/api25/post/context', methods=['POST'])
def create_task25():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task25(task)}), 201

@app.route('/api25/put/context/<int:task_id>', methods=['PUT'])
def update_task25(task_id):
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
    return jsonify({'task': make_public_task25(task[0])})

@app.route('/api25/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task25(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api25/fib/<int:x>')
def fib25(x):
    return str(calcfib(x))

@app.route('/api25/sleep/<int:x>')
def delay25(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api25/count')
def count25():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api25/redisping')
def proxy25():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api26/')
def index26():
    return render_template('index.html')

def make_public_task26(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task26', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api26/get/context', methods=['GET'])
def get_context26():
    return jsonify({'context': list(map(make_public_task26, context))})

@app.route('/api26/get/context/<int:task_id>', methods=['GET'])
def get_task26(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task26(task[0])})

@app.route('/api26/post/context', methods=['POST'])
def create_task26():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task26(task)}), 201

@app.route('/api26/put/context/<int:task_id>', methods=['PUT'])
def update_task26(task_id):
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
    return jsonify({'task': make_public_task26(task[0])})

@app.route('/api26/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task26(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api26/fib/<int:x>')
def fib26(x):
    return str(calcfib(x))

@app.route('/api26/sleep/<int:x>')
def delay26(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api26/count')
def count26():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api26/redisping')
def proxy26():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api27/')
def index27():
    return render_template('index.html')

def make_public_task27(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task27', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api27/get/context', methods=['GET'])
def get_context27():
    return jsonify({'context': list(map(make_public_task27, context))})

@app.route('/api27/get/context/<int:task_id>', methods=['GET'])
def get_task27(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task27(task[0])})

@app.route('/api27/post/context', methods=['POST'])
def create_task27():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task27(task)}), 201

@app.route('/api27/put/context/<int:task_id>', methods=['PUT'])
def update_task27(task_id):
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
    return jsonify({'task': make_public_task27(task[0])})

@app.route('/api27/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task27(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api27/fib/<int:x>')
def fib27(x):
    return str(calcfib(x))

@app.route('/api27/sleep/<int:x>')
def delay27(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api27/count')
def count27():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api27/redisping')
def proxy27():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api28/')
def index28():
    return render_template('index.html')

def make_public_task28(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task28', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api28/get/context', methods=['GET'])
def get_context28():
    return jsonify({'context': list(map(make_public_task28, context))})

@app.route('/api28/get/context/<int:task_id>', methods=['GET'])
def get_task28(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task28(task[0])})

@app.route('/api28/post/context', methods=['POST'])
def create_task28():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task28(task)}), 201

@app.route('/api28/put/context/<int:task_id>', methods=['PUT'])
def update_task28(task_id):
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
    return jsonify({'task': make_public_task28(task[0])})

@app.route('/api28/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task28(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api28/fib/<int:x>')
def fib28(x):
    return str(calcfib(x))

@app.route('/api28/sleep/<int:x>')
def delay28(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api28/count')
def count28():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api28/redisping')
def proxy28():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api29/')
def index29():
    return render_template('index.html')

def make_public_task29(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task29', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api29/get/context', methods=['GET'])
def get_context29():
    return jsonify({'context': list(map(make_public_task29, context))})

@app.route('/api29/get/context/<int:task_id>', methods=['GET'])
def get_task29(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task29(task[0])})

@app.route('/api29/post/context', methods=['POST'])
def create_task29():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task29(task)}), 201

@app.route('/api29/put/context/<int:task_id>', methods=['PUT'])
def update_task29(task_id):
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
    return jsonify({'task': make_public_task29(task[0])})

@app.route('/api29/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task29(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api29/fib/<int:x>')
def fib29(x):
    return str(calcfib(x))

@app.route('/api29/sleep/<int:x>')
def delay29(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api29/count')
def count29():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api29/redisping')
def proxy29():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api30/')
def index30():
    return render_template('index.html')

def make_public_task30(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task30', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api30/get/context', methods=['GET'])
def get_context30():
    return jsonify({'context': list(map(make_public_task30, context))})

@app.route('/api30/get/context/<int:task_id>', methods=['GET'])
def get_task30(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task30(task[0])})

@app.route('/api30/post/context', methods=['POST'])
def create_task30():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task30(task)}), 201

@app.route('/api30/put/context/<int:task_id>', methods=['PUT'])
def update_task30(task_id):
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
    return jsonify({'task': make_public_task30(task[0])})

@app.route('/api30/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task30(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api30/fib/<int:x>')
def fib30(x):
    return str(calcfib(x))

@app.route('/api30/sleep/<int:x>')
def delay30(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api30/count')
def count30():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api30/redisping')
def proxy30():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api31/')
def index31():
    return render_template('index.html')

def make_public_task31(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task31', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api31/get/context', methods=['GET'])
def get_context31():
    return jsonify({'context': list(map(make_public_task31, context))})

@app.route('/api31/get/context/<int:task_id>', methods=['GET'])
def get_task31(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task31(task[0])})

@app.route('/api31/post/context', methods=['POST'])
def create_task31():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task31(task)}), 201

@app.route('/api31/put/context/<int:task_id>', methods=['PUT'])
def update_task31(task_id):
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
    return jsonify({'task': make_public_task31(task[0])})

@app.route('/api31/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task31(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api31/fib/<int:x>')
def fib31(x):
    return str(calcfib(x))

@app.route('/api31/sleep/<int:x>')
def delay31(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api31/count')
def count31():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api31/redisping')
def proxy31():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api32/')
def index32():
    return render_template('index.html')

def make_public_task32(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task32', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api32/get/context', methods=['GET'])
def get_context32():
    return jsonify({'context': list(map(make_public_task32, context))})

@app.route('/api32/get/context/<int:task_id>', methods=['GET'])
def get_task32(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task32(task[0])})

@app.route('/api32/post/context', methods=['POST'])
def create_task32():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task32(task)}), 201

@app.route('/api32/put/context/<int:task_id>', methods=['PUT'])
def update_task32(task_id):
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
    return jsonify({'task': make_public_task32(task[0])})

@app.route('/api32/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task32(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api32/fib/<int:x>')
def fib32(x):
    return str(calcfib(x))

@app.route('/api32/sleep/<int:x>')
def delay32(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api32/count')
def count32():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api32/redisping')
def proxy32():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api33/')
def index33():
    return render_template('index.html')

def make_public_task33(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task33', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api33/get/context', methods=['GET'])
def get_context33():
    return jsonify({'context': list(map(make_public_task33, context))})

@app.route('/api33/get/context/<int:task_id>', methods=['GET'])
def get_task33(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task33(task[0])})

@app.route('/api33/post/context', methods=['POST'])
def create_task33():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task33(task)}), 201

@app.route('/api33/put/context/<int:task_id>', methods=['PUT'])
def update_task33(task_id):
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
    return jsonify({'task': make_public_task33(task[0])})

@app.route('/api33/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task33(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api33/fib/<int:x>')
def fib33(x):
    return str(calcfib(x))

@app.route('/api33/sleep/<int:x>')
def delay33(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api33/count')
def count33():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api33/redisping')
def proxy33():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api34/')
def index34():
    return render_template('index.html')

def make_public_task34(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task34', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api34/get/context', methods=['GET'])
def get_context34():
    return jsonify({'context': list(map(make_public_task34, context))})

@app.route('/api34/get/context/<int:task_id>', methods=['GET'])
def get_task34(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task34(task[0])})

@app.route('/api34/post/context', methods=['POST'])
def create_task34():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task34(task)}), 201

@app.route('/api34/put/context/<int:task_id>', methods=['PUT'])
def update_task34(task_id):
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
    return jsonify({'task': make_public_task34(task[0])})

@app.route('/api34/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task34(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api34/fib/<int:x>')
def fib34(x):
    return str(calcfib(x))

@app.route('/api34/sleep/<int:x>')
def delay34(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api34/count')
def count34():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api34/redisping')
def proxy34():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api35/')
def index35():
    return render_template('index.html')

def make_public_task35(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task35', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api35/get/context', methods=['GET'])
def get_context35():
    return jsonify({'context': list(map(make_public_task35, context))})

@app.route('/api35/get/context/<int:task_id>', methods=['GET'])
def get_task35(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task35(task[0])})

@app.route('/api35/post/context', methods=['POST'])
def create_task35():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task35(task)}), 201

@app.route('/api35/put/context/<int:task_id>', methods=['PUT'])
def update_task35(task_id):
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
    return jsonify({'task': make_public_task35(task[0])})

@app.route('/api35/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task35(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api35/fib/<int:x>')
def fib35(x):
    return str(calcfib(x))

@app.route('/api35/sleep/<int:x>')
def delay35(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api35/count')
def count35():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api35/redisping')
def proxy35():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api36/')
def index36():
    return render_template('index.html')

def make_public_task36(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task36', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api36/get/context', methods=['GET'])
def get_context36():
    return jsonify({'context': list(map(make_public_task36, context))})

@app.route('/api36/get/context/<int:task_id>', methods=['GET'])
def get_task36(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task36(task[0])})

@app.route('/api36/post/context', methods=['POST'])
def create_task36():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task36(task)}), 201

@app.route('/api36/put/context/<int:task_id>', methods=['PUT'])
def update_task36(task_id):
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
    return jsonify({'task': make_public_task36(task[0])})

@app.route('/api36/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task36(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api36/fib/<int:x>')
def fib36(x):
    return str(calcfib(x))

@app.route('/api36/sleep/<int:x>')
def delay36(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api36/count')
def count36():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api36/redisping')
def proxy36():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api37/')
def index37():
    return render_template('index.html')

def make_public_task37(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task37', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api37/get/context', methods=['GET'])
def get_context37():
    return jsonify({'context': list(map(make_public_task37, context))})

@app.route('/api37/get/context/<int:task_id>', methods=['GET'])
def get_task37(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task37(task[0])})

@app.route('/api37/post/context', methods=['POST'])
def create_task37():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task37(task)}), 201

@app.route('/api37/put/context/<int:task_id>', methods=['PUT'])
def update_task37(task_id):
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
    return jsonify({'task': make_public_task37(task[0])})

@app.route('/api37/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task37(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api37/fib/<int:x>')
def fib37(x):
    return str(calcfib(x))

@app.route('/api37/sleep/<int:x>')
def delay37(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api37/count')
def count37():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api37/redisping')
def proxy37():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api38/')
def index38():
    return render_template('index.html')

def make_public_task38(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task38', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api38/get/context', methods=['GET'])
def get_context38():
    return jsonify({'context': list(map(make_public_task38, context))})

@app.route('/api38/get/context/<int:task_id>', methods=['GET'])
def get_task38(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task38(task[0])})

@app.route('/api38/post/context', methods=['POST'])
def create_task38():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task38(task)}), 201

@app.route('/api38/put/context/<int:task_id>', methods=['PUT'])
def update_task38(task_id):
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
    return jsonify({'task': make_public_task38(task[0])})

@app.route('/api38/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task38(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api38/fib/<int:x>')
def fib38(x):
    return str(calcfib(x))

@app.route('/api38/sleep/<int:x>')
def delay38(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api38/count')
def count38():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api38/redisping')
def proxy38():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api39/')
def index39():
    return render_template('index.html')

def make_public_task39(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task39', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api39/get/context', methods=['GET'])
def get_context39():
    return jsonify({'context': list(map(make_public_task39, context))})

@app.route('/api39/get/context/<int:task_id>', methods=['GET'])
def get_task39(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task39(task[0])})

@app.route('/api39/post/context', methods=['POST'])
def create_task39():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task39(task)}), 201

@app.route('/api39/put/context/<int:task_id>', methods=['PUT'])
def update_task39(task_id):
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
    return jsonify({'task': make_public_task39(task[0])})

@app.route('/api39/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task39(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api39/fib/<int:x>')
def fib39(x):
    return str(calcfib(x))

@app.route('/api39/sleep/<int:x>')
def delay39(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api39/count')
def count39():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api39/redisping')
def proxy39():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api40/')
def index40():
    return render_template('index.html')

def make_public_task40(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task40', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api40/get/context', methods=['GET'])
def get_context40():
    return jsonify({'context': list(map(make_public_task40, context))})

@app.route('/api40/get/context/<int:task_id>', methods=['GET'])
def get_task40(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task40(task[0])})

@app.route('/api40/post/context', methods=['POST'])
def create_task40():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task40(task)}), 201

@app.route('/api40/put/context/<int:task_id>', methods=['PUT'])
def update_task40(task_id):
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
    return jsonify({'task': make_public_task40(task[0])})

@app.route('/api40/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task40(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api40/fib/<int:x>')
def fib40(x):
    return str(calcfib(x))

@app.route('/api40/sleep/<int:x>')
def delay40(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api40/count')
def count40():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api40/redisping')
def proxy40():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api41/')
def index41():
    return render_template('index.html')

def make_public_task41(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task41', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api41/get/context', methods=['GET'])
def get_context41():
    return jsonify({'context': list(map(make_public_task41, context))})

@app.route('/api41/get/context/<int:task_id>', methods=['GET'])
def get_task41(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task41(task[0])})

@app.route('/api41/post/context', methods=['POST'])
def create_task41():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task41(task)}), 201

@app.route('/api41/put/context/<int:task_id>', methods=['PUT'])
def update_task41(task_id):
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
    return jsonify({'task': make_public_task41(task[0])})

@app.route('/api41/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task41(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api41/fib/<int:x>')
def fib41(x):
    return str(calcfib(x))

@app.route('/api41/sleep/<int:x>')
def delay41(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api41/count')
def count41():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api41/redisping')
def proxy41():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api42/')
def index42():
    return render_template('index.html')

def make_public_task42(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task42', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api42/get/context', methods=['GET'])
def get_context42():
    return jsonify({'context': list(map(make_public_task42, context))})

@app.route('/api42/get/context/<int:task_id>', methods=['GET'])
def get_task42(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task42(task[0])})

@app.route('/api42/post/context', methods=['POST'])
def create_task42():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task42(task)}), 201

@app.route('/api42/put/context/<int:task_id>', methods=['PUT'])
def update_task42(task_id):
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
    return jsonify({'task': make_public_task42(task[0])})

@app.route('/api42/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task42(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api42/fib/<int:x>')
def fib42(x):
    return str(calcfib(x))

@app.route('/api42/sleep/<int:x>')
def delay42(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api42/count')
def count42():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api42/redisping')
def proxy42():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api43/')
def index43():
    return render_template('index.html')

def make_public_task43(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task43', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api43/get/context', methods=['GET'])
def get_context43():
    return jsonify({'context': list(map(make_public_task43, context))})

@app.route('/api43/get/context/<int:task_id>', methods=['GET'])
def get_task43(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task43(task[0])})

@app.route('/api43/post/context', methods=['POST'])
def create_task43():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task43(task)}), 201

@app.route('/api43/put/context/<int:task_id>', methods=['PUT'])
def update_task43(task_id):
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
    return jsonify({'task': make_public_task43(task[0])})

@app.route('/api43/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task43(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api43/fib/<int:x>')
def fib43(x):
    return str(calcfib(x))

@app.route('/api43/sleep/<int:x>')
def delay43(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api43/count')
def count43():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api43/redisping')
def proxy43():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api44/')
def index44():
    return render_template('index.html')

def make_public_task44(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task44', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/api44/get/context', methods=['GET'])
def get_context44():
    return jsonify({'context': list(map(make_public_task44, context))})

@app.route('/api44/get/context/<int:task_id>', methods=['GET'])
def get_task44(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    return jsonify({'task': make_public_task44(task[0])})

@app.route('/api44/post/context', methods=['POST'])
def create_task44():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task44(task)}), 201

@app.route('/api44/put/context/<int:task_id>', methods=['PUT'])
def update_task44(task_id):
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
    return jsonify({'task': make_public_task44(task[0])})

@app.route('/api44/delete/context/<int:task_id>', methods=['DELETE'])
def delete_task44(task_id):
    task = list(filter(lambda t: t['id'] == task_id, context))
    if len(task) == 0:
        abort(404)
    context.remove(task[0])
    return jsonify({'result': True})

@app.route('/api44/fib/<int:x>')
def fib44(x):
    return str(calcfib(x))

@app.route('/api44/sleep/<int:x>')
def delay44(x):
    time.sleep(x)
    return "delayed by " + str(x) + " seconds"

@app.route('/api44/count')
def count44():
    r.incr('hits')
    counter = str(r.get('hits'), 'utf-8')
    return counter

@app.route('/api44/redisping')
def proxy44():
    headers = {}
    headers.update(zipkin.create_http_headers_for_new_span())
    return get(f'{SITE_NAME}/ping', headers=headers).content



@app.route('/api45/')
def index45():
    return render_template('index.html')

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
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': context[-1]['id'] + 1,
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


