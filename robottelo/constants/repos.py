"""Only External Repos url specific constants module"""
from robottelo.config import settings

if not settings.configured:
    settings.configure()

REPOS_URL = settings.repos_hosting_url

CUSTOM_FILE_REPO = 'https://fixtures.pulpproject.org/file/'
CUSTOM_KICKSTART_REPO = 'http://ftp.cvut.cz/centos/8/BaseOS/x86_64/kickstart/'
CUSTOM_RPM_REPO = 'https://fixtures.pulpproject.org/rpm-signed/'
CUSTOM_RPM_SHA_512 = 'https://fixtures.pulpproject.org/rpm-with-sha-512/'
CUSTOM_MODULE_STREAM_REPO_1 = f'{REPOS_URL}/module_stream1'
CUSTOM_MODULE_STREAM_REPO_2 = f'{REPOS_URL}/module_stream2'
CUSTOM_SWID_TAG_REPO = f'{REPOS_URL}/swid_zoo'
FAKE_0_YUM_REPO = f'{REPOS_URL}/fake_yum0'
FAKE_1_YUM_REPO = f'{REPOS_URL}/fake_yum1'
FAKE_2_YUM_REPO = f'{REPOS_URL}/fake_yum2'
FAKE_3_YUM_REPO = f'{REPOS_URL}/fake_yum3'
FAKE_4_YUM_REPO = f'{REPOS_URL}/fake_yum4'
FAKE_5_YUM_REPO = 'http://{0}:{1}@rplevka.fedorapeople.org/fakerepo01/'
FAKE_6_YUM_REPO = f'{REPOS_URL}/needed_errata'
FAKE_7_YUM_REPO = f'{REPOS_URL}/pulp/demo_repos/large_errata/zoo/'
FAKE_8_YUM_REPO = f'{REPOS_URL}/lots_files'
FAKE_9_YUM_REPO = f'{REPOS_URL}/multiple_errata'
FAKE_10_YUM_REPO = f'{REPOS_URL}/modules_rpms'
FAKE_11_YUM_REPO = f'{REPOS_URL}/rpm_deps'
FAKE_YUM_DRPM_REPO = 'https://fixtures.pulpproject.org/drpm-signed/'
FAKE_YUM_SRPM_REPO = 'https://fixtures.pulpproject.org/srpm-signed/'
FAKE_YUM_SRPM_DUPLICATE_REPO = 'https://fixtures.pulpproject.org/srpm-duplicate/'
FAKE_YUM_MIXED_REPO = f'{REPOS_URL}/yum_mixed'
FAKE_YUM_MD5_REPO = 'https://fixtures.pulpproject.org/rpm-with-md5/'
CUSTOM_PUPPET_REPO = f'{REPOS_URL}/custom_puppet'
FAKE_0_PUPPET_REPO = f'{REPOS_URL}/fake_puppet0'
FAKE_1_PUPPET_REPO = f'{REPOS_URL}/fake_puppet1'
FAKE_2_PUPPET_REPO = f'{REPOS_URL}/fake_puppet2'
FAKE_3_PUPPET_REPO = f'{REPOS_URL}/fake_puppet3'
FAKE_4_PUPPET_REPO = f'{REPOS_URL}/fake_puppet4'
FAKE_5_PUPPET_REPO = f'{REPOS_URL}/fake_puppet5'
FAKE_6_PUPPET_REPO = f'{REPOS_URL}/fake_puppet6'
FAKE_7_PUPPET_REPO = 'http://{0}:{1}@rplevka.fedorapeople.org/fakepuppet01/'
FAKE_8_PUPPET_REPO = f'{REPOS_URL}/fake_puppet8'
# Fedora's OSTree repo changed to a single repo at
#   https://kojipkgs.fedoraproject.org/compose/ostree/repo/
# With branches for each version. Some tests (test_positive_update_url) still need 2 repos URLs,
# We will use the archived versions for now, but probably need to revisit this.
FEDORA26_OSTREE_REPO = 'https://kojipkgs.fedoraproject.org/compose/ostree-20190207-old/26/'
FEDORA27_OSTREE_REPO = 'https://kojipkgs.fedoraproject.org/compose/ostree-20190207-old/26/'
OSTREE_REPO = 'https://fixtures.pulpproject.org/ostree/small/'
REPO_DISCOVERY_URL = f'{REPOS_URL}/repo_discovery/'
FAKE_0_INC_UPD_URL = f'{REPOS_URL}/inc_update/'
FAKE_PULP_REMOTE_FILEREPO = f'{REPOS_URL}/pulp_remote'
FAKE_0_YUM_REPO_STRING_BASED_VERSIONS = (
    'https://fixtures.pulpproject.org/rpm-string-version-updateinfo/'
)
EPEL_REPO = f'{REPOS_URL}/epel_repo'
