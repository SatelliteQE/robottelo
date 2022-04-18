import contextlib
import random

from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.logging import logger


class CapsuleInfo:
    """Miscellaneous Capsule helper methods"""

    def get_available_capsule_port(self, port_pool=None):
        """returns a list of unused ports dedicated for fake capsules
        This calls an ss command on the server prompting for a port range. ss
        returns a list of ports which have a PID assigned (a list of ports
        which are already used). This function then substracts unavailable ports
        from the other ones and returns one of available ones randomly.

        :param port_pool: A list of ports used for fake capsules (for RHEL7+: don't
            forget to set a correct selinux context before otherwise you'll get
            Connection Refused error)

        :return: Random available port from interval <9091, 9190>.
        :rtype: int
        """
        if port_pool is None:
            from robottelo.config import settings

            port_pool_range = settings.fake_capsules.port_range
            if isinstance(port_pool_range, str):
                port_pool_range = tuple(port_pool_range.split('-'))
            if isinstance(port_pool_range, tuple) and len(port_pool_range) == 2:
                port_pool = range(int(port_pool_range[0]), int(port_pool_range[1]))
            else:
                raise TypeError(
                    'Expected type of port_range is a tuple of 2 elements,'
                    f'got {type(port_pool_range)} instead'
                )
        # returns a list of strings
        ss_cmd = self.execute(
            f"ss -tnaH sport ge {port_pool[0]} sport le {port_pool[-1]}"
            " | awk '{n=split($4, p, \":\"); print p[n]}' | sort -u"
        )
        if ss_cmd.stderr[1]:
            raise CapsuleTunnelError(
                f'Failed to create ssh tunnel: Error getting port status: {ss_cmd.stderr}'
            )
        # converts a List of strings to a List of integers
        try:
            used_ports = map(
                int, [val for val in ss_cmd.stdout.splitlines()[:-1] if val != 'Cannot stat file ']
            )

        except ValueError:
            raise CapsuleTunnelError(
                f'Failed parsing the port numbers from stdout: {ss_cmd.stdout.splitlines()[:-1]}'
            )
        try:
            # take the list of available ports and return randomly selected one
            return random.choice([port for port in port_pool if port not in used_ports])
        except IndexError:
            raise CapsuleTunnelError(
                'Failed to create ssh tunnel: No more ports available for mapping'
            )

    @contextlib.contextmanager
    def default_url_on_new_port(self, oldport, newport):
        """Creates context where the default capsule is forwarded on a new port

        :param int oldport: Port to be forwarded.
        :param int newport: New port to be used to forward `oldport`.

        :return: A string containing the new capsule URL with port.
        :rtype: str

        """
        pre_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
        with self.session.shell() as channel:
            # if ncat isn't backgrounded, it prevents the channel from closing
            command = f'ncat -kl -p {newport} -c "ncat {self.hostname} {oldport}" &'
            logger.debug(f'Creating tunnel: {command}')
            channel.send(command)
            post_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
            ncat_pid = set(post_ncat_procs).difference(set(pre_ncat_procs))
            if not len(ncat_pid):
                stderr = channel.get_exit_status()[1]
                logger.debug(f'Tunnel failed: {stderr}')
                # Something failed, so raise an exception.
                raise CapsuleTunnelError(f'Starting ncat failed: {stderr}')
            forward_url = f'https://{self.hostname}:{newport}'
            logger.debug(f'Yielding capsule forward port url: {forward_url}')
            try:
                yield forward_url
            finally:
                logger.debug(f'Killing ncat pid: {ncat_pid}')
                self.execute(f'kill {ncat_pid.pop()}')
