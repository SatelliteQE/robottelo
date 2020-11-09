FROM fedora
MAINTAINER https://github.com/SatelliteQE

RUN dnf install -y gcc git make cmake libffi-devel openssl-devel python3-devel \
    python3-pip redhat-rpm-config which libcurl-devel libxml2-devel

COPY / /robottelo/
WORKDIR /robottelo
RUN curl https://raw.githubusercontent.com/SatelliteQE/broker/master/broker_settings.yaml.example -o broker_settings.yaml

ENV PYCURL_SSL_LIBRARY=openssl
RUN pip install -r requirements.txt

CMD make test-robottelo
