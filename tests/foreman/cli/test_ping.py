from itertools import izip
from robottelo import ssh
from robottelo.config import settings
from robottelo.test import CLITestCase


class PingTestCase(CLITestCase):
    """Tests related to the hammer ping command"""

    def test_hammer_ping(self):
        """@test: hammer ping return code

        @feature: hammer ping

        @steps:
        1. Execute hammer ping
        2. Check its return code, should be 0 if all services are ok else != 0

        @assert: hammer ping returns a right return code

        """
        result = ssh.command('hammer -u {0} -p {1} ping'.format(
            settings.server.username,
            settings.server.password
        ))
        self.assertEqual(len(result.stderr), 0)

        status_count = 0
        ok_count = 0

        # iterate over the lines grouping every 3 lines
        # example [1, 2, 3, 4, 5, 6] will return [(1, 2, 3), (4, 5, 6)]
        # only the status line is relevant for this test
        for _, status, _ in izip(*[iter(result.stdout)] * 3):
            status_count += 1

            if status.split(':')[1].strip().lower() == 'ok':
                ok_count += 1

        if status_count == ok_count:
            self.assertEqual(
                result.return_code, 0,
                'Return code should be 0 if all services are ok')
        else:
            self.assertNotEqual(
                result.return_code, 0,
                'Return code should not be 0 if any service is not ok')
