"""Utilities for LDAP-related test helpers."""

from robottelo.config import settings


def get_ldap_cacert_pem(sat, server_type, hostname):
    """Fetch the LDAP CA certificate as PEM without installing it in the OS trust store.

    :param sat: Satellite host object
    :param str server_type: 'IPA' or 'AD'
    :param str hostname: LDAP server hostname
    :returns: PEM-encoded CA certificate string
    """
    if server_type == 'IPA':
        result = sat.execute(f'curl -sf http://{hostname}/ipa/config/ca.crt')
        assert result.status == 0, f'Failed to fetch IPA CA cert: {result.stderr}'
        return result.stdout
    if server_type == 'AD':
        sat.execute('yum -y --disableplugin=foreman-protector install cifs-utils')
        sat.execute(
            rf'mount -t cifs -o username=administrator,pass={settings.ldap.password} '
            rf'//{hostname}/c\$ /mnt'
        )
        try:
            cert_path = '/mnt/Users/Administrator/Desktop/satqe-QE-SAT6-AD-CA.cer'
            result = sat.execute(f'cat {cert_path}')
            assert result.status == 0, 'Failed to read AD CA cert'
            pem_content = result.stdout
            if not pem_content.strip().startswith('-----BEGIN'):
                result = sat.execute(f'openssl x509 -inform DER -in {cert_path}')
                assert result.status == 0, 'Failed to convert AD CA cert to PEM'
                pem_content = result.stdout
        finally:
            sat.execute('umount /mnt')
        return pem_content
    raise ValueError(f'Unsupported server_type for CA cert: {server_type}')
