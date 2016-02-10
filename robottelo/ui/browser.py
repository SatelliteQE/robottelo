"""Tools to help getting a browser instance to run UI tests."""
import six
import time

from robottelo.config import settings
from selenium import webdriver

try:
    import docker
except ImportError:
    # Let if fail later if not installed
    docker = None


class DockerBrowserError(Exception):
    """Indicates any issue with DockerBrowser."""


def browser():
    """Creates a webdriver browser instance based on configuration."""
    webdriver_name = settings.webdriver.lower()
    if webdriver_name == 'firefox':
        return webdriver.Firefox(
            firefox_binary=webdriver.firefox.firefox_binary.FirefoxBinary(
                settings.webdriver_binary)
        )
    elif webdriver_name == 'chrome':
        return (
            webdriver.Chrome() if settings.webdriver_binary is None
            else webdriver.Chrome(executable_path=settings.webdriver_binary)
        )
    elif webdriver_name == 'ie':
        return (
            webdriver.Ie() if settings.webdriver_binary is None
            else webdriver.Ie(executable_path=settings.webdriver_binary)
        )
    elif webdriver_name == 'phantomjs':
        return webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
    elif webdriver_name == 'remote':
        return webdriver.Remote()


class DockerBrowser(object):
    """Provide a browser instance running inside a docker container."""
    def __init__(self):
        if docker is None:
            raise DockerBrowserError(
                'Package docker-py is not installed. Install it in order to '
                'use DockerBrowser.'
            )
        self.webdriver = None
        self.container = None
        self._client = None
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
                self.webdriver = webdriver.Remote(
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
            ports=[4444],
        )
        self._client.start(self.container['Id'])
        self.container.update(
            self._client.port(self.container['Id'], 4444)[0])

    def _remove_container(self):
        """Turn off and clean up container from system."""
        if not self.container:
            return
        self._client.stop(self.container['Id'])
        self._client.wait(self.container['Id'])
        self._client.remove_container(self.container['Id'], force=True)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
