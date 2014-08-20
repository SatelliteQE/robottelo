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
    longMessage = True

    def setUp(self):  # pylint:disable=C0103
        """Backup and customize ``conf.properties``, and generate an ID."""
        self.conf_properties = conf.properties.copy()
        conf.properties['main.server.hostname'] = 'example.com'
        self.id_ = FauxFactory.generate_integer(min_value=1)

    def tearDown(self):  # pylint:disable=C0103
        """Restore ``conf.properties``."""
        conf.properties = self.conf_properties

    @data(
        (entities.ActivationKey, '/activation_keys'),
        (entities.ContentView, '/content_views'),
        (entities.ContentViewVersion, '/content_view_versions'),
        (entities.Repository, '/repositories'),
    )
    @unpack
    def test_path_without_which(self, entity, path):
        """Test what happens when the ``which`` argument is omitted.

        Assert that ``path`` returns a valid string when the ``which`` argument
        is omitted, regardless of whether an entity ID is provided.

        """
        self.assertIn(path, entity().path(), entity)
        self.assertIn(
            '{0}/{1}'.format(path, self.id_),
            entity(id=self.id_).path(),
            entity.__name__,
        )

    @data(
        (entities.ActivationKey, '/activation_keys', 'releases'),
        (entities.ContentView, '/content_views', 'content_view_versions'),
        (entities.ContentView, '/content_views', 'publish'),
        (entities.ContentView, '/content_views',
         'available_puppet_module_names'),
        (entities.ContentViewVersion, '/content_view_versions', 'promote'),
        (entities.Repository, '/repositories', 'sync'),
    )
    @unpack
    def test_path_with_which(self, entity, path, which):
        """Test what happens when an entity ID is given and ``which=which``.

        Assert that when ``entity(id=<id>).path(which=which)`` is called, the
        resultant path contains the following string:

            'path/<id>/which'

        """
        gen_path = entity(id=self.id_).path(which=which)
        self.assertIn(
            '{0}/{1}/{2}'.format(path, self.id_, which),
            gen_path,
            entity.__name__
        )
        self.assertRegexpMatches(
            gen_path,
            '{0}$'.format(which),
            entity.__name__
        )

    @data(
        (entities.ActivationKey, 'releases'),
        (entities.ContentView, 'content_view_versions'),
        (entities.ContentView, 'publish'),
        (entities.ContentView, 'available_puppet_module_names'),
        (entities.ContentViewVersion, 'promote'),
        (entities.Repository, 'sync'),
        (entities.ForemanTask, 'this'),
        (entities.System, 'this'),
    )
    @unpack
    def test_no_such_path(self, entity, path):
        """Test what happens when no entity ID is provided and ``which=path``.

        Assert that :class:`robottelo.orm.NoSuchPathError` is raised.

        """
        with self.assertRaises(orm.NoSuchPathError):
            entity().path(which=path)

    def test_foremantask_path(self):
        """Test :meth:`robottelo.entities.ForemanTask.path`.

        Assert that correct paths are returned when:

        * an entity ID is provided and the ``which`` argument to ``path`` is
          omitted
        * ``which = 'bulk_search'``

        """
        self.assertIn(
            '/foreman_tasks/api/tasks/{0}'.format(self.id_),
            entities.ForemanTask(id=self.id_).path()
        )
        for gen_path in (
                entities.ForemanTask().path(which='bulk_search'),
                entities.ForemanTask(id=self.id_).path(which='bulk_search')):
            self.assertIn('/foreman_tasks/api/tasks/bulk_search', gen_path)

    def test_system_path(self):
        """Test :meth:`robottelo.entities.System.path`.

        Assert that correct paths are returned when:

        * A UUID is provided and ``which`` is omitted.
        * A UUID is provided and ``which='this'``.
        * A UUID is omitted and ``which`` is omitted.
        * A UUID is omitted and ``which='all'``.

        """
        for gen_path in (
                entities.System(uuid=self.id_).path(),
                entities.System(uuid=self.id_).path(which='this')):
            self.assertIn('/systems/{0}'.format(self.id_), gen_path)
            self.assertRegexpMatches(gen_path, '{0}$'.format(self.id_))
        for gen_path in (
                entities.System().path(),
                entities.System().path(which='all')):
            self.assertIn('/systems', gen_path)
            self.assertRegexpMatches(gen_path, 'systems$')
