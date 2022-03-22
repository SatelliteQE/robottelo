Containerized test runs.
========================

Run tests in docker container.
------------------------------

Build the image

$ podman build -t robottelo-hands-on -f Dockerfile.hands-on
...
--> 3d3b8cd1e5c
STEP 10/10: WORKDIR /robottelo
COMMIT robottelo-hands-on
--> fd0ae971a48
Successfully tagged localhost/robottelo-hands-on:latest
fd0ae971a4808c8125b38bdd2dbd0da994e30cbfc476eabcfb6e942e8de133c7

Create the container and run the shell in it.

    podman run --rm --name robottelo-hands-on -it -v .:/robottelo:Z localhost/robottelo-hands-on:latest /bin/bash
    [root@aefa31919419 robottelo]#

Now you are working in the container.
In case you exit the container, there is a way to to re-attach the container again (the next day).

    podman restart robottelo-hands-on && podman attach robottelo-hands-on
    aefa3191941907d14ceba536dda595cce475891719e81a198185ca8f8ebfaa9b
    [root@aefa31919419 robottelo]#

---
** NOTE **
The bash history will not be preserved over the restart of the container.
---

To delete the container

    podman rm robottelo-hands-on

To delete the image

    podman rmi robottelo-hands-on

Running the tests directly.
---------------------------

Running the tests directly makes easier starting the tests, but may be more difficult to debug the tests after problem
was hit.

    podman run --name robottelo-hands-off -it -v .:/robottelo:Z localhost/robottelo-hands-on:latest py.test -s tests/foreman/api/test_bookmarks.py

When problem was hit, you have more options:
https://medium.com/@pimterry/5-ways-to-debug-an-exploding-docker-container-4f729e2c0aa8 the most powerful is to commit
the container into an image and start new container:

    podman commit robottelo-hands-off robottelo-hands-off-broken
    podman run -it -v .:/robottelo robottelo-hands-off-broken /bin/bash

Then you can do cleanup:

    podman rm robottelo-hands-off
    podman rmi robottelo-hands-off-broken
