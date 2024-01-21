import json
import os.path
import random
import time
import requests
from datetime import datetime, timedelta

import cachetools.func
from threading import Thread

from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__)

global visitors, last_visitor, visitors_list
visitors = 0
last_visitor = 0
visitors_list = []


def is_online():
    api_link = 'https://api.twitch.tv/'
    channel_id = '44407373'
    response = False

    res = requests.get(api_link+'helix/streams?user_id='+channel_id, headers={'Authorization': 'Bearer '+os.environ("token"), 'Client-Id': str(os.environ("client"))}).text
    if res != '{"data":[],"pagination":{}}':
        response = True

    return response


def get_stored_data():
    if not os.path.exists('data.json'):
        with open('data.json', 'w') as f:
            f.write('{"lastonline": 0, "highscore": 0}')
    with open('data.json', 'r') as f:
        return json.loads(f.read())


def update_by_timer():
    while True:
        get_data()
        print("Data updated")
        time.sleep(45*60 + random.randint(0, 100))


@cachetools.func.ttl_cache(maxsize=128, ttl=60*20)
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
    global visitors, last_visitor, visitors_list
    user_id = f"{request.remote_addr}:{request.headers.get('User-Agent')}:{request.headers.get('X-Real-IP')}"

    if datetime.fromtimestamp(last_visitor).day != datetime.now().day:
        visitors = 0
        visitors_list = []
    if user_id not in visitors_list:
        visitors += 1
        visitors_list.append(user_id)
    last_visitor = datetime.now().timestamp()

    data = get_data()
    delta = (datetime.now() - datetime.fromtimestamp(data['lastonline']))

    return render_template('index.html',
                           current=delta.days if delta > timedelta(days=1) else delta.seconds // 3600,
                           highscore=data['highscore'],
                           timescale_hours=delta < timedelta(days=1),
                           online=delta < timedelta(minutes=30),
                           visitors=visitors)


@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    t = Thread(target=update_by_timer)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=80)
