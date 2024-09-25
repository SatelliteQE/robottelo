FROM quay.io/fedora/python-312:latest
MAINTAINER https://github.com/SatelliteQE

ENV PYCURL_SSL_LIBRARY=openssl \
    ROBOTTELO_DIR="${HOME}/robottelo" \
    UV_PYTHON="${APP_ROOT}/bin/python3" \
    UV_NO_CACHE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

USER 1001
COPY --chown=1001:0 / ${ROBOTTELO_DIR}

WORKDIR "${ROBOTTELO_DIR}"
RUN git config --global --add safe.directory ${ROBOTTELO_DIR} && \
    uv pip install -r requirements.txt

CMD make test-robottelo
