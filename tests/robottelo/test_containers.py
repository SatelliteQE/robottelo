import docker
from robottelo import containers


PUBLIC_IMAGE = {
    "image": "alpine",
    "tag": "latest"
}


def setup_module():
    """Setup module to pull docker public docker image down"""
    client = docker.Client(version="1.22")
    client.pull(f'{PUBLIC_IMAGE["image"]}:{PUBLIC_IMAGE["tag"]}')


def test_positive_create_with_default():
    """Getting a container up with default settings"""
    test_container = containers.Container(**PUBLIC_IMAGE)
    assert test_container.name


def test_positive_create_with_custom_args():
    """Getting a container up with all custom arguments"""
    test_container = containers.Container(
        runtime="docker", **PUBLIC_IMAGE, agent=True)
    assert test_container.name
    test_container.delete()


def test_positive_execute_commands():
    """Ensuring executing command in container host is successful"""
    test_container = containers.Container(**PUBLIC_IMAGE)
    result = test_container.execute("hostname").strip()
    assert result == test_container.name
    test_container.delete()
