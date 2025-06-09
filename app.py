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

# Helper function to safely generate the next task id (handles empty context list)

def get_next_id():
    return context[-1]['id'] + 1 if context else 1

# Sample initial context list (if not defined elsewhere) for demonstration purposes
context = [
    { 'id': 1, 'title': 'Initial task', 'description': 'This is a sample', 'done': False }
]

############################
# API endpoints definitions
############################

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
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
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

# The following endpoints (api2 to api45) follow a similar pattern
# For brevity, only the create_task* functions are shown with the fix applied

@app.route('/api2/post/context', methods=['POST'])
def create_task2():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task2(task)}), 201

@app.route('/api3/post/context', methods=['POST'])
def create_task3():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task3(task)}), 201

@app.route('/api4/post/context', methods=['POST'])
def create_task4():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task4(task)}), 201

@app.route('/api5/post/context', methods=['POST'])
def create_task5():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task5(task)}), 201

@app.route('/api6/post/context', methods=['POST'])
def create_task6():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task6(task)}), 201

@app.route('/api7/post/context', methods=['POST'])
def create_task7():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task7(task)}), 201

@app.route('/api8/post/context', methods=['POST'])
def create_task8():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task8(task)}), 201

@app.route('/api9/post/context', methods=['POST'])
def create_task9():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task9(task)}), 201

@app.route('/api10/post/context', methods=['POST'])
def create_task10():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task10(task)}), 201

@app.route('/api11/post/context', methods=['POST'])
def create_task11():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task11(task)}), 201

@app.route('/api12/post/context', methods=['POST'])
def create_task12():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task12(task)}), 201

@app.route('/api13/post/context', methods=['POST'])
def create_task13():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task13(task)}), 201

@app.route('/api14/post/context', methods=['POST'])
def create_task14():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task14(task)}), 201

@app.route('/api15/post/context', methods=['POST'])
def create_task15():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task15(task)}), 201

@app.route('/api16/post/context', methods=['POST'])
def create_task16():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task16(task)}), 201

@app.route('/api17/post/context', methods=['POST'])
def create_task17():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task17(task)}), 201

@app.route('/api18/post/context', methods=['POST'])
def create_task18():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task18(task)}), 201

@app.route('/api19/post/context', methods=['POST'])
def create_task19():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task19(task)}), 201

@app.route('/api20/post/context', methods=['POST'])
def create_task20():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task20(task)}), 201

@app.route('/api21/post/context', methods=['POST'])
def create_task21():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task21(task)}), 201

@app.route('/api22/post/context', methods=['POST'])
def create_task22():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task22(task)}), 201

@app.route('/api23/post/context', methods=['POST'])
def create_task23():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task23(task)}), 201

@app.route('/api24/post/context', methods=['POST'])
def create_task24():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task24(task)}), 201

@app.route('/api25/post/context', methods=['POST'])
def create_task25():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task25(task)}), 201

@app.route('/api26/post/context', methods=['POST'])
def create_task26():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task26(task)}), 201

@app.route('/api27/post/context', methods=['POST'])
def create_task27():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task27(task)}), 201

@app.route('/api28/post/context', methods=['POST'])
def create_task28():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task28(task)}), 201

@app.route('/api29/post/context', methods=['POST'])
def create_task29():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task29(task)}), 201

@app.route('/api30/post/context', methods=['POST'])
def create_task30():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task30(task)}), 201

@app.route('/api31/post/context', methods=['POST'])
def create_task31():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task31(task)}), 201

@app.route('/api32/post/context', methods=['POST'])
def create_task32():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task32(task)}), 201

@app.route('/api33/post/context', methods=['POST'])
def create_task33():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task33(task)}), 201

@app.route('/api34/post/context', methods=['POST'])
def create_task34():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task34(task)}), 201

@app.route('/api35/post/context', methods=['POST'])
def create_task35():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task35(task)}), 201

@app.route('/api36/post/context', methods=['POST'])
def create_task36():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task36(task)}), 201

@app.route('/api37/post/context', methods=['POST'])
def create_task37():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task37(task)}), 201

@app.route('/api38/post/context', methods=['POST'])
def create_task38():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task38(task)}), 201

@app.route('/api39/post/context', methods=['POST'])
def create_task39():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task39(task)}), 201

@app.route('/api40/post/context', methods=['POST'])
def create_task40():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task40(task)}), 201

@app.route('/api41/post/context', methods=['POST'])
def create_task41():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task41(task)}), 201

@app.route('/api42/post/context', methods=['POST'])
def create_task42():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task42(task)}), 201

@app.route('/api43/post/context', methods=['POST'])
def create_task43():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task43(task)}), 201

@app.route('/api44/post/context', methods=['POST'])
def create_task44():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task44(task)}), 201

@app.route('/api45/post/context', methods=['POST'])
def create_task45():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'id': get_next_id(),
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    context.append(task)
    return jsonify({'task': make_public_task45(task)}), 201

# The remaining endpoints (PUT, DELETE, fib, sleep, count, redisping) for APIs 2 to 45 follow the same pattern as for the first API and are left unchanged.

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
