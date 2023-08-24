import multiprocessing
from pathlib import Path
import random
from threading import Thread
import time

from robottelo.utils.shared_resource import SharedResource


def upgrade_action(*args, **kwargs):
    print(f"Upgrading satellite with {args=} and {kwargs=}")
    time.sleep(1)
    print("Satellite upgraded!")


def run_resource(resource_name):
    time.sleep(random.random() * 5)  # simulate random pre-setup
    with SharedResource(resource_name, upgrade_action) as resource:
        assert Path(f"/tmp/{resource_name}.shared").exists()
        time.sleep(5)  # simulate setup actions
        resource.ready()
        time.sleep(1)  # simulate cleanup actions


def test_shared_resource():
    """Test the SharedResource class."""
    with SharedResource("test_resource", upgrade_action, 1, 2, 3, foo="bar") as resource:
        assert Path("/tmp/test_resource.shared").exists()
        assert resource.is_main
        assert not resource.is_recovering
        assert resource.action == upgrade_action
        assert resource.action_args == (1, 2, 3)
        assert resource.action_kwargs == {"foo": "bar"}
        assert not resource.action_is_recoverable

        resource.ready()
        assert resource._check_all_status("ready")

    assert not Path("/tmp/test_resource.shared").exists()


def test_shared_resource_multiprocessing():
    """Test the SharedResource class with multiprocessing."""
    with multiprocessing.Pool(2) as pool:
        pool.map(run_resource, ["test_resource_mp", "test_resource_mp"])

    assert not Path("/tmp/test_resource_mp.shared").exists()


def test_shared_resource_multithreading():
    """Test the SharedResource class with multithreading."""
    t1 = Thread(target=run_resource, args=("test_resource_th",))
    t2 = Thread(target=run_resource, args=("test_resource_th",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert not Path("/tmp/test_resource_th.shared").exists()
