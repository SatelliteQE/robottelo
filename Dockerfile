FROM fedora
MAINTAINER https://github.com/SatelliteQE

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN dnf install -y gcc git libffi-devel openssl-devel python3-devel \
    redhat-rpm-config which

COPY / /robottelo/
WORKDIR /robottelo

RUN pip3 install -r requirements.txt

CMD make test-robottelo
