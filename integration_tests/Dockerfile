FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install
RUN playwright install-deps

COPY tests tests

CMD ["pytest", "tests"]
