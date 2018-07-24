FROM python:3

ENV PYTHONBUFFERED 1

RUN mkdir /salic_ml_web

WORKDIR /salic_ml_web

ADD requirements.txt /salic_ml_web/

RUN pip install -r requirements.txt

ADD . /salic_ml_web/

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]