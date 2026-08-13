#!/bin/bash

HUB_IMAGE=${HUB_IMAGE:-"docker.io/selenium/hub:latest"}
NODE_IMAGE=${NODE_IMAGE:-"docker.io/selenium/node-chrome:latest"}
STANDALONE_IMAGE=${STANDALONE_IMAGE:-"docker.io/selenium/standalone-chrome:latest"}

function get_first_ip_from_iface_name {
    ip -4 -N -o a show dev "$1" | awk '{ split($4, a, "/"); print a[1]; exit }'
}

function selenium_grid_start_hub {
    echo "Creating grid network:"
    podman network create selenium-grid
    echo "Running selenium hub:"
    podman run --name selenium-hub \
      -d --restart unless-stopped \
      --net=selenium-grid \
      -p 4442-4445:4442-4445 \
      "$HUB_IMAGE"
}

function selenium_grid_start_node {
    echo "Running selenium node:"
    SUFFIX=$(tr -dc A-Za-z0-9 < /dev/urandom | head -c 5)
    LISTEN_IP=$(get_first_ip_from_iface_name "${LISTEN_DEVICE:-tun0}")
    podman run --name "selenium-node-chrome-$SUFFIX" \
      -d --restart unless-stopped \
      --net=selenium-grid \
      --shm-size=2g \
      -e SE_EVENT_BUS_HOST="$LISTEN_IP" \
      -e SE_EVENT_BUS_PUBLISH_PORT=4442 \
      -e SE_EVENT_BUS_SUBSCRIBE_PORT=4443 \
      "$NODE_IMAGE"
}

function selenium_grid_cleanup {
    echo "Cleaning up the grid:"
    podman network rm -f selenium-grid
}

function selenium_standalone_start {
    echo "Running selenium browser:"
    podman run --name standalone-chrome \
      -d --restart unless-stopped \
      -p 4444:4444 \
      -p 7900:7900 \
      --shm-size="2g" \
      "$STANDALONE_IMAGE"
}

function selenium_standalone_cleanup {
    echo "Cleaning up selenium browser:"
    podman rm -f standalone-chrome
}
