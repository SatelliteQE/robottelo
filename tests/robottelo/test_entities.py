"""Tests for :mod:`robottelo.entities`."""
from fauxfactory import FauxFactory
from robottelo.common import conf
from robottelo import entities, orm
from unittest import TestCase
# (Too many public methods) pylint: disable=R0904


class PathTestCase(TestCase):
    """Tests for methods which override :meth:`robottelo.orm.Entity.path`."""
    def setUp(self):  # pylint:disable=C0103
        """Backup and customize objects, and generate an ID."""
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        self.id_ = FauxFactory.generate_integer(min_value=1)

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        conf.properties = self.conf_properties

    def test_activationkey_path(self):
        """Tests for :meth:`robottelo.entities.ActivationKey.path`.

        Make the following assertions:

        1. The method returns the correct string when ``which`` is not
           specified.
        2. The method returns the correct string when ``which == 'releases'``.
        3. The method raises :class:`robottelo.orm.NoSuchPathError` when
           ``which == 'releases'`` and no entity ID is provided.

        """
        # 1
        self.assertIn('/activation_keys', entities.ActivationKey().path())
        self.assertIn(
            '/activation_keys/{0}'.format(self.id_),
            entities.ActivationKey(id=self.id_).path()
        )
        # 2
        self.assertIn(
            '/activation_keys/{0}/releases'.format(self.id_),
            entities.ActivationKey(id=self.id_).path(which='releases')
        )
        # 3
        with self.assertRaises(orm.NoSuchPathError):
            entities.ActivationKey().path(which='releases')

    def test_repository_path(self):
        """Tests for :meth:`robottelo.entities.Repository.path`.

        Make the following assertions:

        1. The method returns the correct string when ``which`` is not
           specified.
        2. The method returns the correct string when ``which == 'sync'``.
        3. The method raises :class:`robottelo.orm.NoSuchPathError` when
           ``which == 'sync'`` and no entity ID is provided.

        """
        # 1
        self.assertIn('/repositories', entities.Repository().path())
        self.assertIn(
            '/repositories/{0}'.format(self.id_),
            entities.Repository(id=self.id_).path()
        )
        # 2
        self.assertIn(
            '/repositories/{0}/sync'.format(self.id_),
            entities.Repository(id=self.id_).path(which='sync')
        )
        # 3
        with self.assertRaises(orm.NoSuchPathError):
            entities.Repository().path(which='sync')

    def test_foreman_task_path(self):
        """Tests for :meth:`robottelo.entities.ForemanTask.path`.

        Make the following assertions:

        1. The method raises :class:`robottelo.orm.NoSuchPathError` when
           ``which`` is not specified and no ID is provided.
        2. The method returns the correct string when ``which`` is not specified
           and an ID is provided.
        3. The method return the correct string when ``which = 'bulk_search'``.

        """
        # 1
        with self.assertRaises(orm.NoSuchPathError):
            entities.ForemanTask().path()
        # 2
        self.assertIn(
            '/foreman_tasks/api/tasks/{0}'.format(self.id_),
            entities.ForemanTask(id=self.id_).path()
        )
        # 3
        for gen_path in (
                entities.ForemanTask().path(which='bulk_search'),
                entities.ForemanTask(id=self.id_).path(which='bulk_search')):
            self.assertIn('/foreman_tasks/api/tasks/bulk_search', gen_path)
