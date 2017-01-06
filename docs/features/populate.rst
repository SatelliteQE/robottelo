Populate
========

This section explains Robottelo data populate.

.. contents::

Commands
--------
Using :code:`$ manage` in the robottelo environment and root directory
In the subgroup `data` you can find the ``populate`` and ``validate`` commands.
That commands are used to read data description from YAML file and
populate the system or validate populated entities.

Read more in specific documentation in :doc:`populate </api/robottelo.populate>`

Having ``test_data.yaml`` with the following content.

  "By default ``tests/foreman/data`` is the path to look for yaml files
  but you can include a leading :code:`/` to the path ``/tmp/file.yaml``"

.. code-block:: console

    vars:
      org_label_suffix = inc
    actions:
      - model: Organization
        log: The first organization...
        register: org_1
        data:
          name: MyOrg
          label: MyOrg{{org_label_suffix}}


To populate the system

.. code-block:: console

    (robottelo_env)[you@host robottelo]$ manage data populate test_data.yaml -v
    2017-01-04 04:31:17 - robottelo.populate.base - INFO - CREATE: The first organization...
    2017-01-04 04:31:19 - robottelo.populate.base - INFO - search: Organization {'query': {'search': 'name=MyOrg,label=MyOrg'}} found unique item
    2017-01-04 04:31:19 - robottelo.populate.base - INFO - create: Entity already exists: Organization 36
    2017-01-04 04:31:19 - robottelo.populate.base - INFO - registry: org_1 registered

To validate the system

.. code-block:: console

    (robottelo_env)[you@host robottelo]$ manage data validate test_data.yaml
    (robottelo_env)[you@host robottelo]$ echo $?
    0  # system validated else 1


Use :code:`$ manage data --help` and :code:`$ manage populate --help` for more info

Decorator
---------

Other way to use populate is via decorator, it is useful to decorate a test_case
forcing a populate or validate operation to be performed.

    Having a data_file like::

        actions:
          - model: Organization
            register: organization_1
            data:
              name: My Org

    Then you can use in decorators::

        @populate_with('file.yaml')
        def test_case_(self):
            'My Org exists in system test anything here'

    And getting the populated entities inside the test_case::

        @populate_with('file.yaml', context=True)
        def test_case_(self, context):
            assert context.entities.organization_1.name == 'My Org'

    You can also set a name to the context argument::

        @populate_with('file.yaml', context='my_context')
        def test_case_(self, my_context):
            assert my_context.organization_1.name == 'My Org'


And if you dont want to have YAML file you can provide a dict::

    data = {
        'actions': [
            {
                'model': 'Organization',
                'register': 'organization_1',
                'data': {
                    'name': 'My Organization 1',
                    'label': 'my_organization_1'
                }
            },
        ]
    }


    @populate_with(data, context=True, verbose=1)
    def test_org_1(context):
        """a test with populated data"""
        assert context.registry['organization_1'].name == "MyOrganization1"


The YAML data file
------------------

In the YAML data file it is possible to specify 3 sections, ``config``, ``vars`` and ``actions``.


config
++++++

The config may be used to define special behavior of populator and its keys are:

- populator

  The name of the populator defined in ``populators``
- populators

  The specification of populator modules to be loaded
- verbose

  The verbosity of logging 0, 1 or 2, it can be overwritten with -vvv in commands.

example:

.. code-block:: console

    config:
      verbose: 3
      populator: api
      populators:
        api:
          module: robottelo.populate.api.APIPopulator
        cli:
          module: robottelo.populate.cli.CLIPopulator

vars
++++

Variables to be available in the rendering context of the YAML data
every var defined here is available to be referenced using ``Jinja`` syntax in
any action.

.. code-block:: console

      vars:
        admin_username: admin
        admin_password: changeme
        org_name_list:
          - company7
          - company8
        prefix: aaaa
        suffix: bbbb
        my_name: me

actions
+++++++

The actions is the most important section of the YAML, it is a list of actions
being each action a dictionary containing special keys depending on the action type.

The action type is defined in ``action`` key and available actions are:

Actions are executed in the defined order and order is very important because
each action can ``register`` its result to the internal registry to be referenced
later in any other action.


**CRUD ACTIONS**

Crud actions takes a ``model`` argument, any from ``nailgun.entities`` is valid.


- create (the default)

  Creates a new entity if not exists, else gets existing.
- update

  Updates entity with provided ``data`` by ``id`` or unique search
- delete

  deleted entity with ``id`` or unique search

**SPECIAL ACTIONS**

- echo

  Logs and print output to the console
- register

  Register a variable in the internal registry
- unregister

  removes a variable from register
- assertion

  perform assertion operations, if any fails returns exit code 1

Dynamic Data
++++++++++++

There are some ways to fetch dynamic data in action definitions, it depends
on the action type.

For any key you can use ``Jinja`` to provide a dynamic value as in::

  value: "{{ get_something }}"
  value: "{{ fauxfactory.gen_string('alpha')}}"
  value: user_{{ item }}

For some actions you can provide a ``data`` key, that data is used to create
new entities and also to perform searches or build the action function.

Every ``data`` key accepts 4 special reference directives in its sub-keys.

- from_registry

  Gets anything from registry::

    data:
      organization:
        from_registry: default_org
      name:
        from_registry: my_name

- from_object

  Gets any Python object available in the environment::

    data:
      url:
        from_object:
          name: robottelo.constants.FAKE_0_YUM_REPO

- from_search

  Perform a search and return its result::

    data:
      organization:
        from_search:
          model: Organization
          data:
            name: Default Organization

- from_read

  Perform a read operation, which is useful when we have unique data or id::

    data:
      organization:
        from_read:
          model: Organization
          data:
            id: 1


The internal registry
+++++++++++++++++++++

Every action which returns a result can write its result to the registry, so
it is available to be accessed by other actions.

Provide a ``register`` unique name in ``action`` definition.

The actions that support ``register`` are:

- create
- update
- register
- assertion

All dynamic directives ``from_*`` supports the use of ``register``

Example::

  - action: create
    model: Organization
    register: my_org
    data:
      name: my_org

  - model: User
    log: Creating user under {{ register.my_org.name }}
    data:
      organization:
        from_registry: my_org

