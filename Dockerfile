FROM python:3.8

RUN mkdir /elections
WORKDIR /elections
ADD . /elections
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "console", "--host", "0.0.0.0"]
