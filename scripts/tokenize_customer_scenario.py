"""
This script adds ':customerscenario: true' to all tests by uuid
depends on `pip install https://github.com/facebook/codemod/tarball/master`

On command line should be like:

$ codemod -i -d tests/foreman/cli/ --extension py \
    ':id: 65ba89f0-9bee-43d9-814b-9f5a194558f8' \
    ':id: 65ba89f0-9bee-43d9-814b-9f5a194558f8\n\n        :customerscenario: true'  # noqa

But in this script we are doing programatically and interactivelly in Python

On robottelo root dir run:
$ python scripts/tokenize_customer_scenario.py
"""

import codemod
from codemod import Query, regex_suggestor, run_interactive
from codemod.helpers import path_filter

codemod.base.yes_to_all = True

# this script can be changed to accept this list as param
# or to use robozilla to parse for those ids in BZ api
uids = [
    # '65ba89f0-9bee-43d9-814b-9f5a194558f8',
]

query_options = {'root_directory': 'tests/foreman'}
query_options['path_filter'] = path_filter(['py'], None)

for uid in uids:
    match = f':id: {uid}'
    subst = f':id: {uid}\n\n        :customerscenario: true'
    case_i = True
    query_options['suggestor'] = regex_suggestor(match, subst, ignore_case=True)
    run_interactive(query=Query(**query_options))
