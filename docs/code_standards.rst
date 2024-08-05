
Code Standards
==============


General
-------

In order to provide a code base that is easy to maintain, as well as easy to
contribute to, **Robottelo** has adopted a set of code standards that all
contributors are held to. Violations to our strictly held standards will result in a rejected pull request until all violations have been resolved. While not adhering to our recommended standards isn't a show stopper, keeping to them will help our code base to stay great!


Strictly Held
-------------

Black

* Robottelo uses the code formatting tool called 'black'.
* This tool will handle the general formatting regarding indentation and others.
* In general, if black makes a change to your code, that is what we also desire.
* Our CI checks that each pull request is black compliant, so make sure it is run via pre-commit hook or manually before submitting a pull request.

Linting

* All code will be linted to black-compatible `PEP8`_ standards using `ruff linter`_.
* In the root of the **Robottelo** directory, run :code:`ruff check .`
* If ruff linter returns errors, make corrections before submitting a pull request.
* pre-commit configuration is available, and its use is strongly encouraged in local development.

Docstrings

* Every class, method and function will have a sphinx formatted docstring.
* Docstring will also contain `testimony`_ and `sphinx`_ directives, as
  appropriate.

  * testimony docstrings are specific to foreman tests, so every test in
    tests/foreman/* should have the testimony tags.

* In the root of the **Robottelo** directory, run :code:`make test-docstrings`
  to ensure you did not miss adding a docstring.

Strings

* Use string methods instead of the string module.
* Use f-strings for string formatting whenever possible.
* Use the string's format method when an f-string would become too complex.
* When using format, leave out indices, unless absolutely necessary (e.g. variable re-use).

  * Keyword vs positional index preference is up to the reviewers.

Examples ::code::

    simple_example = f'This is a {simple_var} example'
    moderate_example = f'{some_var}: {some_func(arg="foo")}'
    multi_line_example = f'You can also do {"larger"} '
        'f-strings. Only using the f notation when a '
        f'string requires it like this one: {some_func()}'

    complex_formatting = 'This {} contains both {} and {}'.format(
        'string',
        '"layered"',
        ' '.join(['a', 'non-trivial list', 'converted to', 'a', 'string'])
    )
    indices_needed = (
        'this {var1} is a {var1} that has the {var2} {var1} {var3}'.format(
            var1='sentence', var2='word', var3='multiple times'
        )
    )

Naming

Variable names must follow the standards below in addition to Python's own language requirements for valid variable names.

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

Furthermore, when writing fixtures, make their scope clear at the beginning of the fixture function's name. An unspecified scope is assumed to be function-level

* org
* module_org
* session_org


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
* Use :code:`.join()` for non-trivial string concatenation.
* Trivial string concatenation can be done either via f-strings or `+`, though f-strings are preferred.
    * string to string concatenation is faster with `+`.
    * if one or more values need to be converted to a string, f-strings are faster.
* Handle data aggregation inside of functions when able.

Style

* Use single quotes instead of double quotes whenever possible. Single quotes
  are less visually noisy, and they are easier to type.
* When mixing nested strings, and you have exhausted both single and double quotes, use triple quotes on the outer string. ::code::

      bad = f'This "quoted \'string\' is \'messy\''.'''
      good = f'''This 'quoted "string" reads "better"'.'''

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
.. _ruff linter: https://docs.astral.sh/ruff/linter/
.. _testimony: https://github.com/SatelliteQE/testimony
.. _sphinx: http://sphinx-doc.org/markup/para.html
.. _properly format strings: https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting
.. _Python Style Guide: http://docs.python-guide.org/en/latest/writing/style/
.. _pre-commit Tutorial: https://pre-commit.com/#usage
.. _Code Like a Pythonista: http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html
