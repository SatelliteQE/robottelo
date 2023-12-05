FROM fedora:38
MAINTAINER https://github.com/SatelliteQE

RUN dnf install -y gcc git make cmake libffi-devel openssl-devel python3-devel \
    python3-pip redhat-rpm-config which libcurl-devel libxml2-devel

COPY / /robottelo/
WORKDIR /robottelo

ENV PYCURL_SSL_LIBRARY=openssl
RUN pip install -r requirements.txt

CMD make test-robottelo
