FROM python:3.8-slim-buster

WORKDIR /listener

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql libpq-dev \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /listener/requirements.txt
RUN pip install -r requirements.txt

COPY . /listener
