#!/bin/bash -e

touch certindex.txt
mkdir -p certs/
mkdir -p private/

export CERT_HOST=""
sed -i 's/<cert_hostname>/'$HOSTNAME'/g' ./openssl.cnf

openssl req -new -x509 -extensions v3_ca -nodes -keyout private/cakey.crt \
	-out cacert.crt -days 3650 -config ./openssl.cnf
