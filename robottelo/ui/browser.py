from robottelo.config import settings
from selenium import webdriver


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
