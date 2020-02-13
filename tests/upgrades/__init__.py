from automation_tools.satellite6.hammer import set_hammer_config
from fabric.api import env

from robottelo.test import settings
from robottelo.test import TestCase

# Fabric Config setup
TestCase.setUpClass()
env.host_string = settings.server.hostname
env.user = 'root'

# Hammer Config Setup
set_hammer_config()
