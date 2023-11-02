FROM python:3.9.16-alpine3.17

COPY . /opt/tmp/
WORKDIR /opt/tmp

RUN apk update
RUN apk upgrade
RUN apk add --no-cache ffmpeg
RUN apk add build-base linux-headers

RUN python3 -m pip install -r requirements.txt

RUN rm -r /opt/tmp
WORKDIR /opt/app
CMD python3 main.py