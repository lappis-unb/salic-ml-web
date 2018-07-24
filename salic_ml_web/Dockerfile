FROM python:3

EXPOSE 8080

ENV PYTHONBUFFERED 1

RUN mkdir /salic_ml_web

ADD . /salic_ml_web/

WORKDIR /salic_ml_web

RUN pip install -r requirements.txt
