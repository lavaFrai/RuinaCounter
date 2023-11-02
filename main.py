import json
import os.path
import random
import time
from datetime import datetime

import cachetools.func
from threading import Thread

import requests
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


def is_online():
    request = requests.get("https://www.youtube.com/@ZakvielChannel/streams")
    return "В ЭФИРЕ" in request.text


def get_stored_data():
    if not os.path.exists('data.json'):
        with open('data.json', 'w') as f:
            f.write('{"last": 0, "highscore": 0}')
    with open('data.json', 'r') as f:
        return json.loads(f.read())


def update_by_timer():
    while True:
        get_data()
        print("Data updated")
        time.sleep(30*60 + random.randint(0, 100))


@cachetools.func.ttl_cache(maxsize=128, ttl=60)
def get_data():
    print("Data updated2")
    data = get_stored_data()

    data['highscore'] = max((datetime.now() - datetime.fromtimestamp(data['lastonline'])).days, data['highscore'])
    if is_online():
        data['lastonline'] = datetime.now().timestamp()

    with open('data.json', 'w') as f:
        f.write(json.dumps(data))
    return data


@app.route('/index.html')
@app.route('/index.htm')
@app.route('/')
def hello():
    data = get_data()
    return render_template('index.html',
                           current=(datetime.now() - datetime.fromtimestamp(data['lastonline'])).days,
                           highscore=data['highscore'])


@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    t = Thread(target=update_by_timer)
    t.daemon = True
    t.start()

    app.run()
