"""Test important behavior in robottelo's direct dependencies"""


def test_cryptography():
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.asymmetric import rsa

    fake_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    ).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key = serialization.load_pem_private_key(
        fake_key, password=None, backend=default_backend()
    )
    assert private_key.key_size == 2048
    signature = private_key.sign(b"test", padding.PKCS1v15(), hashes.SHA256())
    assert len(signature) == 256


def test_deepdiff():
    from deepdiff import DeepDiff

    assert DeepDiff({'a': 1}, {'a': 2})


def test_dynaconf():
    from robottelo.config import settings

    assert settings


def test_fauxfactory():
    import fauxfactory

    meth_args = {
        'gen_alpha': {'length': 10},
        'gen_alphanumeric': {'length': 20},
        'gen_cjk': {'length': 30},
        'gen_html': {'length': 40},
        'gen_integer': {'min_value': 1, 'max_value': 10},
        'gen_ipaddr': {},
        'gen_string': {'str_type': 'alphanumeric', 'length': 50},
        'gen_url': {},
    }
    for meth, args in meth_args.items():
        result = getattr(fauxfactory, meth)(**args)
        assert result
        if 'length' in args and meth != 'gen_html':
            assert len(result) == args['length']


def test_jinja2():
    import jinja2

    template = jinja2.Template("Hello {{ name }}!")
    assert template.render(name="John Doe") == "Hello John Doe!"


def test_navmazing():
    from navmazing import NavigationTriesExceeded

    assert NavigationTriesExceeded


def test_productmd():
    from productmd.common import parse_nvra

    assert parse_nvra('foo-1.0-1.x86_64.rpm') == {
        'arch': 'x86_64',
        'epoch': 0,
        'name': 'foo',
        'release': '1',
        'version': '1.0',
    }


def test_pyotp():
    import pyotp

    fake_secret = 'JBSWY3DPEHPK3PXP'
    totp = pyotp.TOTP(fake_secret)
    assert totp.now()


def test_python_box():
    from box import Box

    assert Box({'a': 1}).a == 1


def test_pyyaml():
    import yaml

    assert yaml.safe_load('a: 1') == {'a': 1}
    assert yaml.safe_dump({'a': 1}).strip() == 'a: 1'


def test_requests():
    import requests

    assert requests.get('https://www.redhat.com').status_code == 200
    from requests.exceptions import HTTPError

    assert HTTPError


def test_tenacity():
    from tenacity import retry
    from tenacity import stop_after_attempt
    from tenacity import wait_fixed

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def test():
        raise Exception('test')

    try:
        test()
    except Exception:
        pass


def test_testimony():
    import testimony

    test_cases = testimony.get_testcases(['tests/foreman/api/test_activationkey.py'])
    assert test_cases


def test_wait_for():
    from wait_for import wait_for

    assert wait_for(lambda: True, num_sec=1, delay=1)


def test_wrapanapi():
    from wrapanapi.systems.google import GoogleCloudSystem

    assert GoogleCloudSystem
    from wrapanapi.systems.virtualcenter import VMWareSystem

    assert VMWareSystem
    from wrapanapi.entities.vm import VmState

    assert VmState
