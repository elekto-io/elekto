FROM python:3.6.12-stretch

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt 

ENTRYPOINT ./entrypoint.sh
