# -*- encoding: utf-8 -*-
"""Base data model for UI locators"""

import logging
from collections import defaultdict
from selenium.webdriver.common.by import By
from six.moves import reduce


logger = logging.getLogger(__name__)


class LocatorValue(str):
    """Extends str just to allow logging interpolation operator `%`"""

    def __mod__(self, other):
        new_value = super(LocatorValue, self).__mod__(other)
        # logger.debug(u'Locator value replaced to: %s', new_value)
        return new_value


class Locator(defaultdict):
    """This class is the base dataModel for locators
    It works as a taxonomy-tree with autovivification of nested items

    A Locator is a Node object, and can have nested nodes infinitely,
    every time an attribute is accessed if it does not exists a new default
    empty Locator node is created for that attribute and that allows the
    `taxonomy-like` definitions.

    Examples:

    It can be initialized as an empty root node::

        menu_locators = Locator()
        menu_locators.home = Locator(By.XPATH, "//a[@class='home']")
        menu_locators.config = Locator(By.XPATH, "//div[@class='config']")

    Assign a locator using Locator or list/tuple types and the assignation
    will transform list/tuple in to Locator::

        menu_locators.config.users = (By.XPATH, "//a[@class='users']")
        type(menu_locators.config.users) -> 'Locator'

    Root nodes are created automatically, no need to declare it before::

        menu_locators.dashboard.tasks.monitor_panel = (By.XPATH, '//div/m/%s')
        menu_locators.dashboard.tasks.monitor_panel.button = (By.ID, 'button')

    With that 'dashboard, tasks, monitor_panel' were created as empty nodes
    and will not contain a valid locator::

        print(menu_locators.dashboard)
        <contains=['tasks']>
        print(menu_locators.dashboard.tasks)
        <contains=['monitor_panel']>

    But 'monitor_panel' is a locator and it is also node containing a button::

        print(menu_locators.dashboard.tasks.monitor_panel)
        <|strategy=xpath|value=//div/m/%s|contains=['button']>

    Locator 'location' attributes are::

        menu_locators.dashboard.tasks.monitor_panel._strategy
        'xpath'
        menu_locators.dashboard.tasks.monitor_panel._value
        '//div/m/%s'

    But it still works as a simple tuple::

        strategy, value = menu_locators.dashboard.tasks.monitor_panel
        print strategy, value
        xpath //div/m/%s

    The %s placeholders can be direct interpolated resulting in a new Locator::

        panel_a = menu_locators.dashboard.tasks.monitor_panel % 'panel-a'
        print(panel_a)
        <|strategy=xpath|value=//div/m/panel-a>

    Auto completion works in Pycharm, Ipython and other IDEs::

        dir(menu_locators)
        ['dashboard', '_store', '_strategy', '_value']
        dir(menu_locators.dashboard)
        ['tasks', '_store', '_strategy', '_value']

    It can still be used also as a dictionary::

        locator = Locator({'navbar.spinner': (By.XPATH, '//div/spinner')})
        locator['navbar']
        <contains=['spinner']>

    All those forms of access returns the same object::

        locator['navbar.spinner']
        locator['navbar']['spinner']
        locator['navbar'].spinner
        locator.navbar['spinner']
        locator.navbar.spinner
        <|strategy=xpath|value=//div/spinner>

    And also can be used to assign new locators::

        locator['menu.home.button'] = Locator('xpath', '//div/foo/bar')
        locator.menu.home.button = ('xpath', '//div/foo/bar')
        locator['menu']['home']['button'] = ('xpath', '//div/foo/bar')

    Caveats::

        # If a node doesn't exists it is created on the fly
        locator.foo.bla.zaz.blaz.catz  # created 5 nodes all empty

        # So there is no `false` node
        hasattr(locator.bazinga)  # always True
        getattr(locator, 'schubrebers')  # always get a new node Locator

        # But it can be achieved using the contains statement
        'bazinga' in locator  # False
        locator.bazinga  # created a new node 'bazinga'
        'bazinga' in locator  # True

    """

    def __init__(self, *args, **kwargs):
        """Initialize Locator or LocatorDict with params
        :param args: (strategy, value) or a dict of locators
        :param kwargs: named locators
        """
        super(Locator, self).__init__(Locator)
        # _store is where (strategy, value) is stored
        self._store = [
            item for item in args if not isinstance(item, (dict, tuple))
        ]
        if len(self._store) not in (0, 2):
            raise ValueError(
                "Locator stores only 2 values e.g: Locator('xpath', '//div')"
            )

        # if we have a _store populated it means this instance is a locator
        # not only an empty node, so we need to store the casted value
        if len(self._store) > 1:
            self._store[1] = LocatorValue(self._store[1])

        # this class can also be initialized from locator dicts
        _dicts = [item for item in args if isinstance(item, dict)]
        _dicts.append(kwargs)
        for _dict in _dicts:
            for attr, val in _dict.items():
                self.__setitem__(attr, val)

    def __getattribute__(self, item):  # noqa
        """This method is called for every dotted access
        so we can control special names like the ones in the list below:
        copy,update,values,clear,get,items
        that names are reserved because can be a locator name and also a
        method of this object"""
        reserved_names = ('copy', 'update', 'values', 'clear', 'get', 'items')
        if item in reserved_names and item in self:
            return self.__getitem__(item)
        return defaultdict.__getattribute__(self, item)

    def __getattr__(self, attr):
        """When attribute is not found in the class, Python looks for this
        special method, so "self.inexistent" will get here and so we can
        forward it to the __getitem__ self['inexistent'] and then the
        defaultdict can return a new empty node, but if it starts with _ it is
        treated as a normal attribute like _strategy, _store, _value
        """
        if not attr.startswith('_'):
            return self[attr]
        return defaultdict.__getattribute__(self, attr)

    def __setattr__(self, attr, val):
        """Every dotted assignation `self.foo = bar` will be catch here
        so instead of assign a new attribute we add a new key to the dict as
        `self['foo'] = 'bar'`, Normal attribute only if it starts with _.
        """
        if not attr.startswith('_'):
            self[attr] = val
        else:
            defaultdict.__setattr__(self, attr, val)

    def __getitem__(self, item):
        """This is where all access is intercepted, dotted.attribute is
        forwarded to here and also ['multi.keys.access'] so this method
        manages how to get the proper element from node tree.
        if multiple keys it uses a map-reduce like access, if only a single key
        access it directly from the self dictionary, if doesn't exists, the
        default dict will return an empty locator node.
        """
        if isinstance(item, int):
            return self._store[:2][item]

        keys = item.split('.')
        if len(keys) > 1:
            return reduce(getattr, keys, self)
        else:
            locator = defaultdict.__getitem__(self, item)
            # The logging below is too verbose
            # if locator._is_root:
            #     logger.debug(u'Locator node: %s', item)
            # else:
            #     logger.debug(u'Getting locator: %s', item)
            return locator

    def __setitem__(self, key, value):
        """This method is where all new item assignation is performed,
         new items should always be list, tuple or Locator instance
         All values is casted to Locator, this way we ensure nodes are all
         Locator types.
         This method manages `obj.foo.bar = blaz` and
         also `obj['foo.bar'] = blaz` forms of item assignation.
         if assignation is performed in to an existing Locator, all the
         values are merged.
        """
        if not isinstance(value, (list, tuple, Locator)):
            raise ValueError('Value must be iterable or Locator')
        if not isinstance(value, Locator):
            value = Locator(*value)
        keys = key.split('.')
        if len(keys) > 1:
            obj_key = keys.pop(-1)
            obj = reduce(getattr, keys, self)
            setattr(obj, obj_key, value)
        else:
            if key not in self:
                defaultdict.__setitem__(self, key, value)
            else:
                # if exists, should be merged
                self[key]._store = value._store
                for k, v in value.items():
                    self[key][k] = v

    def __dir__(self):
        """Returns only members to allow auto-complete in IDEs
        the following values are suppressed:
            `dir(type(self)) + list(self.__dict__.keys())`
        """
        return list(self.keys()) + ['_store', '_strategy', '_value']

    def __repr__(self):
        """Provides representation for console in the form of:
        <|strategy=x|value=y|contains=[nested nodes]|>
        """
        msg = ["<"]
        if len(self._store) > 1:
            msg.append("strategy=%s" % self._store[0])
            msg.append("value=%s" % self._store[1])
        keys = self.keys()
        if keys:
            msg.append("contains=%s" % str(keys))
        msg.append(">")
        return u"|".join(msg)

    def _repr_pretty_(self, p, cycle):
        """This is __repr__ for iPython, Notebook and other IDEs"""
        return p.text(self.__repr__())

    @property
    def _strategy(self):
        """Selenium strategy is the first element in _store"""
        return self._store[0] if self._store else None

    @property
    def _value(self):
        """Selenium value is the second element in _store"""
        return self._store[1] if self._store else None

    @property
    def _is_root(self):
        """Helper to check if this node has nested nodes"""
        return self._strategy is None and self._value is None

    def __iter__(self):
        """This allows tuple(*unpacking) behavior"""
        return iter(self._store[:2])

    def __len__(self):
        """Also to provide tuple interface"""
        return len(self._store[:2])

    def __mod__(self, other):
        """This is called for `'%s' % value` interpolations, so it returns
        a new Locator with _value interpolated is returned
        """
        if not self._store:
            raise RuntimeError('Empty Locator does not allow interpolation')
        return Locator(self._strategy, self._value % other)

    def __delattr__(self, k):
        """Deletes attribute k if it exists, otherwise deletes key k.
           A KeyError raised by deleting the key--such as when the key
           is missing--will propagate as an AttributeError instead.
        """
        try:
            # Throws exception if not in prototype chain
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)

    def __eq__(self, other):
        """If locators has the same _store they are equals"""
        return self._store == other._store

    @classmethod
    def XPATH(cls, value):
        """Return a valid XPATH locator
        :param value: a valid xpath expression
        :return: Locator
        """
        return cls(By.XPATH, value)

    @classmethod
    def NAME(cls, value):
        """Return a valid NAME locator
        :param value: a valid html form name
        :return: Locator
        """
        return cls(By.NAME, value)

    @classmethod
    def ID(cls, value):
        """Return a valid ID locator
        :param value: a valid html element id
        :return: Locator
        """
        return cls(By.ID, value)

    @classmethod
    def TAG(cls, value):
        """Return a valid TAG_NAME locator
        :param value: a valid html tag name
        :return: Locator
        """
        return cls(By.TAG_NAME, value)

    @classmethod
    def LINK_TEXT(cls, value, partial=False):
        """Return a valid LINK_TEXT locator
        :param value: a valid text or partial text
        :param partial: If true use partial matching
        :return: Locator
        """
        strategy = By.LINK_TEXT if not partial else By.PARTIAL_LINK_TEXT
        return cls(strategy, value)

    @classmethod
    def CLASS(cls, value):
        """Return a valid CLASS_NAME locator
        :param value: a valid html class name
        :return: Locator
        """
        return cls(By.CLASS_NAME, value)

    @classmethod
    def CSS(cls, value):
        """Return a valid CSS_SELECTOR locator
        :param value: a valid css selector expression
        :return: Locator
        """
        return cls(By.CSS_SELECTOR, value)


LocatorDict = Locator
