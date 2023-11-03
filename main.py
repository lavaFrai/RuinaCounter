import json
import os.path
import random
import time
from datetime import datetime, timedelta

import cachetools.func
from threading import Thread

import requests
from flask import Flask, render_template, send_from_directory

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)


def is_online():
    scopes = ["https://www.googleapis.com/auth/youtube"]
    channel = "https://www.youtube.com/@ZakvielChannel"

    credentials = None
    if os.path.exists('secret.json'):
        print("Loading credentials from token")
        credentials = Credentials.from_authorized_user_file('secret.json', scopes)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print(f"refresh token")
            credentials.refresh(Request())
        else:
            print(f"asking for token")
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
            credentials = flow.run_local_server(port=0)

        print(f"writing token file")
        with open('secret.json', 'w') as token_file:
            token_file.write(credentials.to_json())

    youtube = googleapiclient.discovery.build("youtube", 'v3', credentials=credentials)

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        # channelId="UC8PH_guEODbrSfcBYnC_WGQ",
        forUsername="ZakvielChannel",
        maxResults=25
    )
    _id = response = request.execute()['items'][0]['id']
    print("Id:", _id)

    request = youtube.search().list(
        part="snippet",
        channelId="UC8PH_guEODbrSfcBYnC_WGQ",
        maxResults=25
    )
    response = request.execute()['items']
    response = list(filter(lambda x: x['id']['kind'] == "youtube#channel", response))

    while len(response) < 1:
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            # channelId="UC8PH_guEODbrSfcBYnC_WGQ",
            forUsername="ZakvielChannel",
            maxResults=25
        )
        _id = response = request.execute()['items'][0]['id']
        print("Id:", _id)

        request = youtube.search().list(
            part="snippet",
            channelId="UC8PH_guEODbrSfcBYnC_WGQ",
            maxResults=25
        )
        response = request.execute()['items']
        response = list(filter(lambda x: x['id']['kind'] == "youtube#channel", response))

    response = response[0]
    return response['snippet']['liveBroadcastContent'] == 'live'


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
    data = get_data()
    return render_template('index.html',
                           current=(datetime.now() - datetime.fromtimestamp(data['lastonline'])).days,
                           highscore=data['highscore'],
                           online=(datetime.now() - datetime.fromtimestamp(data['lastonline'])) < timedelta(minutes=30))


@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    t = Thread(target=update_by_timer)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=80)
