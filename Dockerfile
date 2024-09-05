FROM fedora:38
MAINTAINER https://github.com/SatelliteQE

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN dnf install -y gcc git make cmake libffi-devel openssl-devel python3-devel \
    redhat-rpm-config which libcurl-devel libxml2-devel

COPY / /robottelo/
WORKDIR /robottelo

ENV PYCURL_SSL_LIBRARY=openssl
ENV UV_SYSTEM_PYTHON=1
RUN uv pip install -r requirements.txt

CMD make test-robottelo
