FROM python:3.7-stretch

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

USER 10017

ENTRYPOINT ./entrypoint.sh
