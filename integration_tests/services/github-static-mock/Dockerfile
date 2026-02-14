FROM python:3.13

WORKDIR /app

# Install Poetry in a place that's already in $PATH
ENV POETRY_HOME=/usr/local
RUN curl -sSL https://install.python-poetry.org | python3 -

COPY . .
RUN poetry install

EXPOSE 9000
CMD ["poetry", "run", "start"]
