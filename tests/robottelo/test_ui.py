import six
import unittest2

from robottelo.ui.browser import browser

if six.PY2:
    import mock
else:
    from unittest import mock


class BrowserTestCase(unittest2.TestCase):
    def setUp(self):
        self.settings_patcher = mock.patch('robottelo.ui.browser.settings')
        self.webdriver_patcher = mock.patch('robottelo.ui.browser.webdriver')
        self.firefox_patcher = mock.patch('robottelo.ui.browser.Firefox')
        self.chrome_patcher = mock.patch('robottelo.ui.browser.Chrome')
        self.ie_patcher = mock.patch('robottelo.ui.browser.Ie')
        self.phantomjs_patcher = mock.patch('robottelo.ui.browser.PhantomJS')
        self.remote_patcher = mock.patch('robottelo.ui.browser.Remote')

        self.settings = self.settings_patcher.start()
        self.webdriver = self.webdriver_patcher.start()
        self.firefox = self.firefox_patcher.start()
        self.chrome = self.chrome_patcher.start()
        self.ie = self.ie_patcher.start()
        self.phantomjs = self.phantomjs_patcher.start()
        self.remote = self.remote_patcher.start()

        self.settings.browser = 'selenium'

    def tearDown(self):
        self.settings_patcher.stop()
        self.webdriver_patcher.stop()
        self.firefox_patcher.stop()
        self.chrome_patcher.stop()
        self.ie_patcher.stop()
        self.phantomjs_patcher.stop()
        self.remote_patcher.stop()

    def test_browser_firefox(self):
        self.settings.webdriver = 'firefox'
        self.webdriver.firefox.firefox_binary.FirefoxBinary.side_effect = [
            None]
        browser()
        self.firefox.assert_called_once_with(firefox_binary=None)

    def test_browser_chrome(self):
        self.settings.webdriver = 'chrome'
        self.settings.webdriver_binary = None
        browser()
        self.chrome.assert_called_once_with()

    def test_browser_ie(self):
        self.settings.webdriver = 'ie'
        self.settings.webdriver_binary = None
        browser()
        self.ie.assert_called_once_with()

    def test_browser_phantomjs(self):
        self.settings.webdriver = 'phantomjs'
        browser()
        self.phantomjs.assert_called_once_with(
            service_args=['--ignore-ssl-errors=true'])

    def test_browser_remote(self):
        self.settings.webdriver = 'remote'
        browser()
        self.remote.assert_called_once_with(
            command_executor=self.settings.command_executor,
            desired_capabilities=self.settings.webdriver_desired_capabilities
        )
