FROM debian:buster-slim

EXPOSE 8080

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-crypto \
        python3-setuptools \
        python3-pyodbc \
        tdsodbc \
        unixodbc-dev \
        # libmysqlclient-dev \
        unixodbc \
        freetds-dev

RUN mkdir /salic_ml_web

ADD . /salic_ml_web/

ADD odbcinst.ini /etc/odbcinst.ini

WORKDIR /salic_ml_web

RUN pip3 install -r requirements.txt
