"""Tests for :mod:`robottelo.entities`."""
from robottelo.common import conf
from robottelo import entities, orm
from unittest import TestCase
# (Too many public methods) pylint: disable=R0904


class ActivationKeyTestCase(TestCase):
    """Tests for :class:`robottelo.entities.ActivationKey`."""
    def setUp(self):  # pylint:disable=C0103
        """Backup and customize objects."""
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        conf.properties = self.conf_properties

    def test_path_1(self):
        """Tests for :meth:`robottelo.entities.ActivationKey.path`.

        Assert the method returns the correct string when ``which`` is not
        specified.

        """
        self.assertIn('/activation_keys', entities.ActivationKey().path())
        self.assertIn(
            '/activation_keys/5',
            entities.ActivationKey(id=5).path()
        )

    def test_path_2(self):
        """Tests for :meth:`robottelo.entities.ActivationKey.path`.

        Assert the method returns the correct string when ``which`` is
        ``'releases'``.

        """
        self.assertIn(
            '/activation_keys/5/releases',
            entities.ActivationKey(id=5).path(which='releases')
        )

    def test_path_3(self):
        """Tests for :meth:`robottelo.entities.ActivationKey.path`.

        Assert the method raises :class:`robottelo.orm.NoSuchPathError` when
        ``which`` is ``'releases'`` and no entity ID is provided.

        """
        with self.assertRaises(orm.NoSuchPathError):
            entities.ActivationKey().path(which='releases')
