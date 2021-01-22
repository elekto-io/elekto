FROM python:3.6.12-stretch

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt 

CMD uwsgi --http 127.0.0.1:3031 --wsgi-file console --callable APP --processes 4 --threads 2 --stats 127.0.0.1:9191
