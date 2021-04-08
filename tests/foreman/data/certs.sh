#!/bin/bash

CERTS_DIR=certs

function generate_certs(){
   CERT_NAME=$1
   SUBJ=$2
   extensions=$3
   if [[ ! -f "$CERTS_DIR/${CERT_NAME}.key" || ! -f "$CERTS_DIR/$CERT_NAME.crt" ]]; then
        echo "Generating server certificate"
        openssl genrsa -out $CERTS_DIR/$CERT_NAME.key 2048
        openssl req -new -key $CERTS_DIR/$CERT_NAME.key -out $CERTS_DIR/$CERT_NAME.csr -subj $SUBJ
        openssl x509 -req -in $CERTS_DIR/$CERT_NAME.csr -CA $CERTS_DIR/$CA_CERT_NAME.crt -CAkey $CERTS_DIR/$CA_CERT_NAME.key -CAcreateserial -out $CERTS_DIR/$CERT_NAME.crt -days 3650 -sha256 -extfile extensions.txt -extensions $extensions
    else
        echo "Server certificate exists. Skipping."
   fi
}

THIRDPARTY_CA_CERT_NAME=ca-thirdparty
if [[ ! -f "$CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key" || ! -f "$CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt" ]]; then
  echo "Generating CA"
  openssl genrsa -out $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key 2048
  openssl req -x509 -new -nodes -key $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.key -sha256 -days 3650 -out $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt -subj "/CN=Thirdparty CA"
else
  echo "Thirdparty CA certificate exists. Skipping."
fi

CA_CERT_NAME=ca
if [[ ! -f "$CERTS_DIR/$CA_CERT_NAME.key" || ! -f "$CERTS_DIR/$CA_CERT_NAME.crt" ]]; then
  echo "Generating CA"
  openssl genrsa -out $CERTS_DIR/$CA_CERT_NAME.key 2048
  openssl req -x509 -new -nodes -key $CERTS_DIR/$CA_CERT_NAME.key -sha256 -days 3650 -out $CERTS_DIR/$CA_CERT_NAME.crt -subj "/CN=Test Self-Signed CA"
else
  echo "CA certificate exists. Skipping."
fi

CA_BUNDLE=ca-bundle
if [[ ! -f "$CERTS_DIR/$CA_BUNDLE.crt" ]]; then
  echo "Generating CA bundle"
  cat $CERTS_DIR/$THIRDPARTY_CA_CERT_NAME.crt $CERTS_DIR/$CA_CERT_NAME.crt > $CERTS_DIR/$CA_BUNDLE.crt
else
  echo "CA certificate bundle exists. Skipping."
fi

# generate certs with hostname 'foreman.example.com'
generate_certs "foreman.example.com" "/CN=foreman.example.com" "extensions"

# generate invalid certs with hostname as 'foreman.example.com'
generate_certs "invalid" "/CN=foreman.example.com" "client_extensions"

# generate certs with wildcard
generate_certs "wildcard" "/CN=*.example.com" "wildcard_extensions"

# generate certs with short hostname
generate_certs "shortname" "/CN=foreman" "shortname_extensions"
