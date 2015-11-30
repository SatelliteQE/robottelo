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
        self.settings = self.settings_patcher.start()
        self.webdriver = self.webdriver_patcher.start()

    def tearDown(self):
        self.settings_patcher.stop()
        self.webdriver_patcher.stop()

    def test_browser_firefox(self):
        self.settings.webdriver = 'firefox'
        self.webdriver.firefox.firefox_binary.FirefoxBinary.side_effect = [
            None]
        browser()
        self.webdriver.Firefox.assert_called_once_with(firefox_binary=None)

    def test_browser_chrome(self):
        self.settings.webdriver = 'chrome'
        self.settings.webdriver_binary = None
        browser()
        self.webdriver.Chrome.assert_called_once_with()

    def test_browser_ie(self):
        self.settings.webdriver = 'ie'
        self.settings.webdriver_binary = None
        browser()
        self.webdriver.Ie.assert_called_once_with()

    def test_browser_phantomjs(self):
        self.settings.webdriver = 'phantomjs'
        browser()
        self.webdriver.PhantomJS.assert_called_once_with(
            service_args=['--ignore-ssl-errors=true'])

    def test_browser_remote(self):
        self.settings.webdriver = 'remote'
        browser()
        self.webdriver.Remote.assert_called_once_with()
