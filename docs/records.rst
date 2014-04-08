=======
Records
=======

.. module:: robottelo.common.records

A record is the source of information about test data. It
contains fields that are able to store and generate random data.
Each record maps to a single record on the system.

The basics:

* Each record is a Python class that subclasses
  :class:`robottelo.common.records.Record`.

* Each attribute of the record represents a record field.

* With all of this, Robottelo could give you automatically-generated
  data to be used on tests. Or just a place to store your own data.

Quick example
=============

This example record defines a ``Domain``::

    from robottelo.common import records

    class Domain(records.Record):
        name = records.StringField()

        def _postinit(self):
            self.name = name.upper()

``name`` is a field of the record. Each field is specified as class attribute and defines the kind of data that will be generated.

``_postinit`` is an optional method which, if defined, will be called after the record instance is created. You could use this hook to do post data generation processing. In this example, after a random ``name`` value is automatically generated, we update its value to be all in upper case.

Fields
======

Fields are specified by class attributes. A field defines which type of data will be generated.

Field options
-------------

Each field takes a certain set of field-specific arguments, but there's also a set of common arguments available to all field types. The common arguments are all
optional:

:attr:`~Field.default`
    The default value for the field. This can be a value or a callable
    object. If callable it will be called every time a new object is
    created.

:attr:`~Field.required`
    If ``False``, the field is not required to create the record. Default is ``True``.

    This helps describe the minimal required set of fields to create a record.

Field types
-----------

.. class:: StringField(format=r'{record_name}_\\d\\d\\d', maxlen=20, str_type='xeger', \**options)

Field that generates a random string with a max length of ``max`` option, default is 20. The type of the generated string can be defined by the ``str_type`` option, with the default being 'xeger'. Other possible options are described in the list below. The ``format`` option is required when the ``str_type`` is 'xeger', this will be the format used by the xeger generation.

* xeger: generates a random string from a regular expression. For example, using the format r'[A-Z]\d[A-Z] \d[A-Z]\d' then will be generated something like 'R6M 1W5'. Xeger works fine with most simple regular expressions, but it doesn't support all Python regular expression features.

* alphanumeric: generates a random alphanumeric string

* alpha: generates a random alpha string

* numeric: generates a random numeric string

* utf8: generates a random utf8 encoded string

* html: generates a random piece of html code

.. class:: IntegerField(min=1, max=10, \**options)

Field that generates a random integer in the range from ``min`` to ``max``. The default is to generate a random integer from 1 to 10.

.. class:: MACField(delimeter=':', \**options)

Field that generates a random MAC address. The delimiter could be changed by specifying the ``delimiter`` option, the default is :.

.. class:: IpAddrField(ip3=False, \**options)

Field that generate a random IP address in the format '999.999.999.999'. If the ``ip3`` option is ``True`` then the last group will be 0 for example '999.999.999.0', default ``False``.

.. class:: ChoiceField(choices, \**options)

Field that randomly selects an item from the ``choices`` options.

.. class:: RelatedField(record_class, \**options)

Field that relate one record to the other. ``record_class`` option defines which class will be used to random generate a complete object.

.. class:: ManyRelatedField(record_class, min, max, \**options)

The same as ``RelatedField`` but generates a list of related records. The length of the list will be a random value from ``min`` to ``max`` options.

Adding new fields
-----------------

You could also create a new field by creating a subclass the :class:`Field` class. The only required method to be overridden is the ``generate`` method. But also you could need some additional options to be passed to the generate method. To receive the options the ``__init__`` needs to be overridden.

The example bellow shows how to create a newer field::

    class MyField(Field):
        def __init__(self, myarg=None, **kwargs):
            super(MyField, self).__init__(**kwargs)
            self.myarg = myarg

        def generate(self):
            if self.myarg is None:
                # myarg is not defined, generate data without the myarg option
                pass
            else:
                # myarg is defined, genereate data based on the myarg
                pass

The example above shows a ``MyField`` class that has a ``myarg`` option which controls how the data will be generated. You could create as many options as needed.

All field types should be located in the module ``robottelo.common.records.fields`` bacause this new fields should be added there.
