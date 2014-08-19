"""Tests for :mod:`robottelo.entities`."""
from ddt import data, ddt, unpack
from fauxfactory import FauxFactory
from robottelo.common import conf
from robottelo import entities, orm
from unittest import TestCase
# (Too many public methods) pylint: disable=R0904


@ddt
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

    @data(
        (entities.ActivationKey, '/activation_keys'),
        (entities.Repository, '/repositories'),
    )
    @unpack
    def test_path_without_which(self, entity, path):
        """Tests for :meth:`robottelo.entities.path`.

        Make the following assertions:

        1. The method returns the correct string when ``which`` is not
           specified.

        """
        self.assertIn(
            path,
            entity().path(),
            "Path {0} was not found for entity {1}".format(
                path, entity
            )
        )
        self.assertIn(
            '{0}/{1}'.format(path, self.id_),
            entity(id=self.id_).path(),
        )

    @data(
        (entities.ActivationKey, '/activation_keys', 'releases'),
        (entities.Repository, '/repositories', 'sync'),
    )
    @unpack
    def test_path_with_which(self, entity, path1, path2):
        """Tests for :meth:`robottelo.entities.path`.

        Make the following assertions:

        1. The method returns the correct string when ``which == 'path2'``.

        """

        self.assertIn(
            '{0}/{1}/{2}'.format(path1, self.id_, path2),
            entity(id=self.id_).path(which=path2)
        )

    @data(
        (entities.ActivationKey, 'releases'),
        (entities.Repository, 'sync'),
        (entities.ForemanTask, 'this')
    )
    @unpack
    def test_no_such_path(self, entity, path):
        """Tests for :meth:`robottelo.entities.path`.

        Make the following assertions:

        1. The method raises :class:`robottelo.orm.NoSuchPathError` when
           ``which == 'path'`` and no entity ID is provided.

        """
        # 1
        with self.assertRaises(orm.NoSuchPathError):
            entity().path(which=path)

    def test_foreman_task_path(self):
        """Tests for :meth:`robottelo.entities.ForemanTask.path`.

        Make the following assertions:

        1. The method returns the correct string when ``which`` is not
        specified
           and an ID is provided.
        2. The method return the correct string when ``which = 'bulk_search'``.

        """
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
