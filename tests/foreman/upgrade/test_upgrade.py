"""
Todo This module is to be removed and is here only for testing and demo purpose
"""
from upgrade_tests import pre_upgrade, post_upgrade

from robottelo.decorators import fixture


@fixture
def f_failing():
    # a fixture that fail
    return 1/0


@pre_upgrade
def test_capsule_pre_upgrade_1(save_test_data):
    """A pre upgrade test that should pass and save data"""
    assert 1 == 1
    data_value = {'id': 100, 'env_id': 500}
    save_test_data(data_value)


@pre_upgrade
def test_capsule_pre_upgrade_2():
    """A pre upgrade test that should fail"""
    assert 1 == 0


@pre_upgrade
def test_capsule_pre_upgrade_2_2(f_failing):
    """A pre upgrade should fail with ERROR because of failing fixture f_failing"""
    assert 1 == 1


@pre_upgrade
def test_capsule_pre_upgrade_3(save_test_data):
    """A pre upgrade test that should pass and save data"""
    assert 1 == 1
    data_value = {'id': 1, 'cv_id': 3}
    save_test_data(data_value)


@pre_upgrade
def test_capsule_pre_upgrade_4():
    """A simple pre upgrade test that should pass"""
    assert 1 == 1


@post_upgrade(depend_on=[test_capsule_pre_upgrade_1, test_capsule_pre_upgrade_2])
def test_capsule_post_upgrade_1(pre_upgrade_data):
    # must be skipped as test_capsule_pre_upgrade_2 should fail
    assert 1 == 0


@post_upgrade(depend_on=test_capsule_pre_upgrade_2)
def test_capsule_post_upgrade_1_1(pre_upgrade_data):
    # must be skipped as test_capsule_pre_upgrade_2 should fail
    assert 1 == 0


@post_upgrade(depend_on=test_capsule_pre_upgrade_2_2)
def test_capsule_post_upgrade_1_2(pre_upgrade_data):
    # must be skipped as test_capsule_pre_upgrade_2_2 should fail with ERROR
    assert 1 == 0


@post_upgrade(depend_on=test_capsule_pre_upgrade_1)
def test_capsule_post_upgrade_2(pre_upgrade_data):
    """Test with one dependent pre_upgrade test"""
    assert pre_upgrade_data == {'id': 100, 'env_id': 500}


@post_upgrade(depend_on=[test_capsule_pre_upgrade_1, test_capsule_pre_upgrade_3])
def test_capsule_post_upgrade_3(pre_upgrade_data):
    """Test with multiple dependent pre_upgrade tests"""
    test_1_data, test_3_data = pre_upgrade_data
    assert test_1_data == {'id': 100, 'env_id': 500}
    assert test_3_data == {'id': 1, 'cv_id': 3}


@post_upgrade
def test_capsule_post_upgrade_4():
    """Test with no dependency"""
    assert 1 == 1
