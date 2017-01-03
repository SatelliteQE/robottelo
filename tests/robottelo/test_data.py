# coding: utf-8
"""
Tests for robottelo.populate module and commands
"""
from robottelo.populate import populate_with


@populate_with('test_data.yaml')
def test_anything():
    """a test with populated data"""
