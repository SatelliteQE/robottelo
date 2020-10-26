
Code Standards
==============


General
-------

In order to provide a code base that is easy to maintain, as well as easy to
contribute to, **Robottelo** has adopted a set of code standards that all
contributers are held to. Violations to our strictly held standards will result
in a rejected pull request until all violations have been resolved. While not
adhering to our recomended standards isn't a show stopper, keeping to them will
help our code base to stay great!


Strictly Held
-------------

Linting

* All code will be linted to `PEP8`_ standards using `flake8`_.
* In the root of the **Robottelo** directory, run :code:`flake8 .`
* If flake8 returns errors, make corrections before submitting a pull request.
* pre-commit configuration is available, and its use is strongly encouraged in local development.
* pre-commit will apply flake, Black, and pyupgrade to lint and auto-format code.

Docstrings

* Every class, method and function will have a `properly formatted`_ docstring.
* Docstring will also contain `testimony`_ and `sphinx`_ directives, as
  appropriate.

  * testimony docstrings are specific to foreman tests, so every test in
    tests/foreman/* should have the testimony tags.

* In the root of the **Robottelo** directory, run :code:`make test-docstrings`
  to ensure you did not miss adding a docstring.

Strings

* Use string methods instead of the string module.
* Use the :code:`f''` f-string syntax to `properly format strings`_::

    formatted_string = f'I {key} a {value}.'

Naming

* module_name
* method_name
* function_name
* instance_variable_name
* local_variable_name
* function_parameter_name
* ClassName
* ExceptionName
* GLOBAL_CONSTANT_NAME
* _private_method
* _private_variable
* _PrivateClass

Style

* Absolutely no semi colons.
* Lines are not to exceed 99 characters in length.
* Code will be indented with **4 spaces** instead of tabs.


Recommended
-----------

Importing

* Import modules in alphabetical order.
* Each non-module import should be on their own line.
* Import order is:

  * standard library
  * third-party
  * application-specific

* Put a blank line between groups of imports.

General

* Avoid global variables.
* Use :code:`.join()` for string concatenation.
* Handle data aggregation inside of functions when able.

Style

* Use single quotes instead of double quotes whenever possible. Single quotes
  are less visually noisy, and they are easier to type.
* One statement per line.


Read More!
----------

`Python Style Guide`_

`pre-commit Tutorial`_

`Code Like a Pythonista`_


Todo
----
Compile a list of standards used by the **Robottelo** team

Categorize each standard into how strictly they are enforced


.. _PEP8: http://legacy.python.org/dev/peps/pep-0008/
.. _flake8: http://flake8.readthedocs.org/
.. _properly formatted: http://legacy.python.org/dev/peps/pep-0257/
.. _testimony: https://github.com/SatelliteQE/testimony
.. _sphinx: http://sphinx-doc.org/markup/para.html
.. _properly format strings: https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting
.. _Python Style Guide: http://docs.python-guide.org/en/latest/writing/style/
.. _pre-commit Tutorial: https://pre-commit.com/#usage
.. _Code Like a Pythonista: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html
