
Committing
==========

Every open source project lives from the generous help by contributors that
sacrifice their time and **Robottelo** is no different.

To make participation as pleasant as possible, this project adheres to
the `Code of Conduct`_ by the Python Software Foundation.

If you have something great but aren’t sure whether it adheres, or even can
adhere, to the rules below: please submit a pull request anyway! In the best
case, we can mold it into something; in the worst case, the pull request gets
politely closed. There’s absolutely nothing to fear.

Thank you for considering contributing to Robottelo! If you have any question
or concerns, feel free to reach out to the team. We can be found on the
#robottelo channel on `freenode`_.


Before you commit
-----------------

Ensure your code follows the guidelines in the **Robottelo**
:doc:`code standards </code_standards>`.

All modules, classes, and functions should have well written docstrings.

See also:

* `testimony`_
* `sphinx`_

Don’t *ever* break backward compatibility. If it ever has to happen for higher
reasons, Robottelo will follow the proven `procedures`_ of the Twisted project.

**Always** add tests and docs for your code. This is a hard rule; patches with
missing tests or documentation won’t be merged. If a feature is not tested or
documented, it doesn’t exist.

In order to ensure you are able to pass the Travis CI build, it is recommended
that you run the following commands in the base of your Robottelo directory.::

    $ ruff check .
    $ make test-docstrings
    $ make test-robottelo

:code:`ruff linter` will ensure that the changes you made are not in violation of
PEP8 standards. If the command gives no output, then you have passed. If not,
then address any corrections recommended.

:code:`test-docstrings` will check if there are parts of the code base that are
missing docstrings.

:code:`test-robottelo` will run all the tests created to ensure Robottelo is
working as expected. If you added a test, it will be run now.

Peforming the commit
--------------------

Proper commit messages

* The title should be a brief summary of the changes.

* The body of the message should effectively explain the changes.

* `This link`_ has much more information on proper commit messages.

* `Close an issue`_ by stating "Fixes #XXXX" where XXXX is the issue number.

Fetch and rebase from upstream/master

Push the commit to your forked repository


Initiating a Pull Request
-------------------------

Navigate to your forked repository on GitHub and click the Pull Request button.

The title and message should auto-populate from your commit. If not, then
recreate them now.

Submit the request!

Did you add or change a test? Include the results in a comment.

Closely monitor the discussion on GitHub to address any questions or
suggestions.

**Never** merge your own pull request. Other members of the team are
responsible for that action.


Making Changes
--------------

If the code review process identifies something that needs to be changed,
perform the change locally.

Use :code:`commit --amend` or squash the change commit down into the previous.

Finally, push again [#note]_ and continue monitoring the discussion.

.. [#note] git may kick back that your GitHub repo is ahead of your current
           commit. Just use the :code:`--force` to push it anyway.


Cleaning up
-----------

If you created a branch, in your forked repository, you may merge it now.


.. _Close an issue: https://help.github.com/articles/closing-issues-via-commit-messages/
.. _Code of Conduct: http://www.python.org/psf/codeofconduct/
.. _freenode: http://freenode.net/
.. _procedures: http://twistedmatrix.com/trac/wiki/CompatibilityPolicy
.. _sphinx: http://sphinx-doc.org/rest.html
.. _testimony: https://github.com/SatelliteQE/testimony
.. _This link: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
