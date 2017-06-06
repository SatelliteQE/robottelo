# coding: utf-8
"""
Implement basic assertions to be used in assertion action
"""


def eq(value, other):
    """Equal"""
    return value == other


def ne(value, other):
    """Not equal"""
    return value != other


def gt(value, other):
    """Greater than"""
    return value > other


def lt(value, other):
    """Lower than"""
    return value < other


def gte(value, other):
    """Greater than or equal"""
    return value >= other


def lte(value, other):
    """Lower than or equal"""
    return value <= other


def identity(value, other):
    """Identity check using ID"""
    return value is other
