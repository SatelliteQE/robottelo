# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Roles CLI
"""

from tests.foreman.cli.basecli import BaseCLI
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common.decorators import (bzbug)
import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest
    

class TestRole(BaseCLI):

      @bzbug('1046206')
      @unittest.skip(NOT_IMPLEMENTED)
      def test_positive_create_role_1(self):
          """
           @test: Create new roles and assign to the custom user
           @feature: Roles
           @assert: Assert creation of roles
           @status: manual
          """

          pass

      @bzbug('1046208')
      @unittest.skip(NOT_IMPLEMENTED)
      def test_create_role_permission_1(self):
          """
           @test: Create new roles Use different set of permission
           @feature: Roles
           @assert: Assert creation of roles with set of permission
           @status: manual
          """

          pass
