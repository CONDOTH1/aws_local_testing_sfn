FROM python:3.11-slim as base

WORKDIR /app/

# Install Poetry
RUN pip3 install --upgrade pip poetry

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry config virtualenvs.create false
RUN poetry install -v --only main
RUN poetry add awscli

ENV PYTHONPATH=/app

FROM base as tests

COPY ./tests /app/app

FROM base as localapp

COPY ./app /app/app