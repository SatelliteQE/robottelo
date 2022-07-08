#!/bin/bash

HUB_IMAGE=${HUB_IMAGE:-"selenium/hub:4.3.0"}
NODE_IMAGE=${NODE_IMAGE:-"selenium/node-chrome:4.3.0"}

function get_first_ip_from_iface_name {
    ip -N a show dev "$1" | awk '/inet /{ print $2 }' | sed 's/\(.*\)\/.*/\1/' | head -n1
}

function selenium_grid_start_hub {
    echo "Running selenium hub:"
    podman run --name selenium-hub \
               --restart unless-stopped \
               -d \
               --net=selenium-grid \
        -p 4442-4445:4442-4445 \
        "$HUB_IMAGE" | tee -a started_selenium_containers
}

function selenium_grid_start_node {
    SUFFIX=`tr -dc A-Za-z0-9 < /dev/urandom | head -c 5`
    LISTEN_IP=`get_first_ip_from_iface_name "${LISTEN_DEVICE:-tun0}"`
    podman run -d --name "selenium-node-chrome-$SUFFIX" \
        -e SE_EVENT_BUS_HOST="$LISTEN_IP" \
        -e SE_EVENT_BUS_PUBLISH_PORT=4442 \
        -e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
        --net=selenium-grid --shm-size=2g \
        "$NODE_IMAGE" | tee -a started_selenium_containers
}

function selenium_grid_cleanup {
    while read container; do
        echo Removing container "$container"
        podman rm -f "$container"
    done < started_selenium_containers
    rm started_selenium_containers
}
