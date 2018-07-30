"""Tools to help getting a browser instance to run UI tests."""
from fauxfactory import gen_string
import logging
import six
import time

from robottelo.config import settings
from selenium import webdriver

try:
    import docker
except ImportError:
    # Let if fail later if not installed
    docker = None


LOGGER = logging.getLogger(__name__)


class DockerBrowserError(Exception):
    """Indicates any issue with DockerBrowser."""


def _sauce_ondemand_url(saucelabs_user, saucelabs_key):
    """Get sauce ondemand URL for a given user and key."""
    return 'http://{0}:{1}@ondemand.saucelabs.com:80/wd/hub'.format(
        saucelabs_user, saucelabs_key)


# Dict of callables to format the output of selenium commands logging
param_formatters = {
    # normally this value is ['a', 'b', 'c'] but we want ['abc']
    'sendKeysToElement': lambda x: {
        'id': x['id'], 'value': ''.join(x['value'])
    }
}


class DriverLoggerMixin(object):
    """Custom Driver Mixin to allow logging of commands execution"""
    def execute(self, driver_command, params=None):
        # execute and intercept the response
        response = super(DriverLoggerMixin, self).execute(driver_command,
                                                          params)

        # skip messages for commands not in settings
        if driver_command not in settings.log_driver_commands:
            return response

        if params:
            # we dont need the sessionId in the log output
            params.pop('sessionId', None)
            value = response.get('value')
            id_msg = ''
            # append the 'id' of element in the front of message
            if isinstance(value, webdriver.remote.webelement.WebElement):
                id_msg = "id: %s" % value.id
            # Build the message like 'findElement: id: 1: {using: xpath}'
            msg = '%s: %s %s' % (
                driver_command,
                id_msg,
                param_formatters.get(driver_command, lambda x: x)(params)
            )
        else:
            msg = driver_command

        # output the log message
        LOGGER.debug(msg)

        return response


class Firefox(DriverLoggerMixin, webdriver.Firefox):
    """Custom Firefox for custom logging"""


class Chrome(DriverLoggerMixin, webdriver.Chrome):
    """Custom Chrome for custom logging"""


class Edge(DriverLoggerMixin, webdriver.Edge):
    """Custom Edge for custom logging"""


class Ie(DriverLoggerMixin, webdriver.Ie):
    """Custom Ie for custom logging"""


class PhantomJS(DriverLoggerMixin, webdriver.PhantomJS):
    """Custom PhantomJS for custom logging"""


class Remote(DriverLoggerMixin, webdriver.Remote):
    """Custom Remote for custom logging"""


def browser(browser_name=None, webdriver_name=None):
    """Creates a webdriver browser.

    :param browser_name: one of selenium, saucelabs, docker
    :param webdriver_name: one of firefox, chrome, edge, ie, phantomjs

    If any of the params are None then will be read from properties file.
    """

    webdriver_name = webdriver_name or settings.webdriver
    browser_name = browser_name or settings.browser
    webdriver_name = webdriver_name.lower()
    browser_name = browser_name.lower()

    if browser_name == 'selenium':
        if webdriver_name == 'firefox':
            return Firefox(
                firefox_binary=webdriver.firefox.firefox_binary.FirefoxBinary(
                    settings.webdriver_binary)
            )
        elif webdriver_name == 'chrome':
            return (
                Chrome() if settings.webdriver_binary is None
                else Chrome(
                    executable_path=settings.webdriver_binary)
            )
        elif webdriver_name == 'ie':
            return (
                Ie() if settings.webdriver_binary is None
                else Ie(executable_path=settings.webdriver_binary)
            )
        elif webdriver_name == 'edge':
            capabilities = webdriver.DesiredCapabilities.EDGE.copy()
            capabilities['acceptSslCerts'] = True
            capabilities['javascriptEnabled'] = True
            return (
                Edge(capabilities=capabilities)
                if settings.webdriver_binary is None
                else Edge(
                    capabilities=capabilities,
                    executable_path=settings.webdriver_binary,
                )
            )
        elif webdriver_name == 'phantomjs':
            return PhantomJS(
                service_args=['--ignore-ssl-errors=true'])
        elif webdriver_name == 'remote':
            return Remote(
                command_executor=settings.command_executor,
                desired_capabilities=settings.webdriver_desired_capabilities)
    elif browser_name == 'saucelabs':
        if webdriver_name == 'chrome':
            desired_capabilities = webdriver.DesiredCapabilities.CHROME.copy()
        elif webdriver_name == 'ie':
            desired_capabilities = (
                webdriver.DesiredCapabilities.INTERNETEXPLORER.copy())
        elif webdriver_name == 'edge':
            desired_capabilities = webdriver.DesiredCapabilities.EDGE.copy()
            desired_capabilities['acceptSslCerts'] = True
            desired_capabilities['javascriptEnabled'] = True
        else:
            desired_capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        if settings.webdriver_desired_capabilities:
            desired_capabilities.update(
                settings.webdriver_desired_capabilities)
        return Remote(
            command_executor=_sauce_ondemand_url(
                settings.saucelabs_user, settings.saucelabs_key),
            desired_capabilities=desired_capabilities
        )
    elif browser_name == 'docker':
        # in test_cases you should use `with DockerBrowser()`
        # this options here is useful only for local command line testing
        # note: docker_browser is not destroyed when using `manage ui browse`
        _docker_browser = DockerBrowser()
        _docker_browser.start()
        return _docker_browser.webdriver
    else:
        raise NotImplementedError(
            "Supported browsers are: selenium, saucelabs, docker"
        )


class DockerBrowser(object):
    """Provide a browser instance running inside a docker container."""
    def __init__(self, name=None):
        if docker is None:
            raise DockerBrowserError(
                'Package docker-py is not installed. Install it in order to '
                'use DockerBrowser.'
            )
        self.webdriver = None
        self.container = None
        self._client = None
        self._name = name
        self._started = False

    def start(self):
        """Start all machinery needed to run a browser inside a docker
        container.
        """
        if self._started:
            return
        self._init_client()
        self._create_container()
        self._init_webdriver()
        self._started = True

    def stop(self):
        self._quit_webdriver()
        self._remove_container()
        self._close_client()
        self.webdriver = None
        self.container = None
        self._client = None
        self._started = False

    def _init_webdriver(self):
        """Init the selenium Remote webdriver."""
        if self.webdriver or not self.container:
            return
        exception = None
        # An exception can be raised while the container is not ready
        # yet. Give up to 10 seconds for a container being ready.
        for attempt in range(20):
            try:
                self.webdriver = Remote(
                    command_executor='http://127.0.0.1:{0}/wd/hub'.format(
                        self.container['HostPort']),
                    desired_capabilities=webdriver.DesiredCapabilities.FIREFOX
                )
            except Exception as err:
                # Capture the raised exception for later usage and wait
                # a few for the next attempt.
                exception = err
                time.sleep(.5)
            else:
                # Connection succeeded time to leave the for loop
                break
        else:
            # Reraise the captured exception.
            # For more info about raise from syntax:
            # https://docs.python.org/3/reference/simple_stmts.html#grammar-token-raise_stmt
            six.raise_from(
                DockerBrowserError(
                    'Failed to connect the webdriver to the containerized '
                    'selenium.'
                ),
                exception
            )

    def _quit_webdriver(self):
        """Quit the selenium Remote webdriver."""
        if not self.webdriver:
            return
        self.webdriver.quit()

    def _init_client(self):
        """Init docker Client.

        Make sure that docker service to be published under the
        unix://var/run/docker.sock unix socket.

        Use auto for version in order to allow docker client to
        automatically figure out the server version.
        """
        if self._client:
            return
        self._client = docker.Client(
            base_url='unix://var/run/docker.sock', version='auto')

    def _close_client(self):
        """Close docker Client."""
        if not self._client:
            return
        self._client.close()

    def _create_container(self):
        """Create a docker container running a standalone-firefox
        selenium.

        Make sure to have the image selenium/standalone-firefox already
        pulled.
        """
        if self.container:
            return
        self.container = self._client.create_container(
            detach=True,
            environment={
                'SCREEN_WIDTH': '1920',
                'SCREEN_HEIGHT': '1080',
            },
            host_config=self._client.create_host_config(
                publish_all_ports=True),
            image='selenium/standalone-firefox',
            name=self._name.split('.', 4)[-1] + '_{0}'.format(
                    gen_string('alphanumeric', 3)),
            ports=[4444],
        )
        LOGGER.debug('Starting container with ID "%s"', self.container['Id'])
        self._client.start(self.container['Id'])
        self.container.update(
            self._client.port(self.container['Id'], 4444)[0])

    def _remove_container(self):
        """Turn off and clean up container from system."""
        if not self.container:
            return
        LOGGER.debug('Stopping container with ID "%s"', self.container['Id'])
        self._client.stop(self.container['Id'])
        self._client.wait(self.container['Id'])
        self._client.remove_container(self.container['Id'], force=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
