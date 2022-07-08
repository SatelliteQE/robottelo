#!/bin/bash

WORKERS_COUNT=$((${1:-1}))  # The default is 1 worker.
HUB_IMAGE=${HUB_IMAGE:-"selenium/hub:4.3.0"}
NODE_IMAGE=${NODE_IMAGE:-"selenium/node-chrome:4.3.0"}
LISTEN_DEVICE=${LISTEN_DEVICE:-tun0}

function get_first_ip_from_iface_name {
    ip -N a show dev "$1" | awk '/inet /{ print $2 }' | sed 's/\(.*\)\/.*/\1/' | head -n1
}

LISTEN_IP=${2:-`get_first_ip_from_iface_name "$LISTEN_DEVICE"`}  # The default is 1 worker.

function run_hub {
    echo "Running selenium hub:"
    podman run --name selenium-hub \
               --restart unless-stopped \
               -d \
               --net=selenium-grid \
        -p 4442-4445:4442-4445 \
        "$HUB_IMAGE"
}


function run_nodes {
    echo "Running $WORKERS_COUNT workers:"
    for ((i=0; i<$WORKERS_COUNT; i++))
    do
        podman run -d --name "selenium-node-chrome-$i" \
            -e SE_EVENT_BUS_HOST="$LISTEN_IP" \
            -e SE_EVENT_BUS_PUBLISH_PORT=4442 \
            -e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
            --net=selenium-grid --shm-size=2g \
            "$NODE_IMAGE"
    done
}

run_hub
run_nodes
