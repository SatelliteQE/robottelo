from robottelo.common import conf
from robottelo.common.helpers import update_dictionary
from robottelo.ui.login import Login
from robottelo.ui.navigator import Navigator
from robottelo.ui.org import Org


class Session(object):
    """A session context manager that manages login and logout"""

    def __init__(self, browser, user=None, password=None):
        self.browser = browser
        self.login = Login(browser)
        self.nav = Navigator(browser)

        if user is None:
            self.user = conf.properties['foreman.admin.username']
        else:
            self.user = user

        if password is None:
            self.password = conf.properties['foreman.admin.password']
        else:
            self.password = password

    def __enter__(self):
        self.login.login(self.user, self.password)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.login.logout()


def make_org(browser, **kwargs):
    create_args = {
        'org_name': None,
        'parent_org': None,
        'label': None,
        'desc': None,
        'users': None,
        'proxies': None,
        'subnets': None,
        'resources': None,
        'medias': None,
        'templates': None,
        'domains': None,
        'envs': None,
        'hostgroups': None,
        'locations': None,
        'edit': False,
        'select': True,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    with Session(browser) as session:
        session.nav.go_to_org()
        Org(session.browser).create(**create_args)
