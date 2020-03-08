#!/bin/bash -e

touch certindex.txt
mkdir -p certs/
mkdir -p private/

export CERT_HOST=""
openssl req -new -x509 -extensions v3_ca -nodes -keyout private/cakey.crt \
	-out cacert.crt -days 3650 -config ./openssl.cnf
