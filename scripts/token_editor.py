#!/usr/bin/env python
"""Token editor

Reads Python test modules under test/foreman and edit docstring tokens' prefix
from ``OLD_TOKEN_PREFIX`` to ``NEW_TOKEN_PREFIX``.
"""

import glob
import os
import re

ROOT_PATH = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir)
)
TESTIMONY_TOKENS_RE = re.compile(r'TESTIMONY_TOKENS="([\w, ]+)"')
OLD_TOKEN_PREFIX = '@'
NEW_TOKEN_PREFIX = ':'

with open('Makefile') as handler:
    match = TESTIMONY_TOKENS_RE.search(handler.read())

if not match:
    raise ValueError('Not able to fetch TESTIMONY_TOKENS from Makefile')

valid_tokens = [token.strip() for token in match.group(1).split(',')]
TOKEN_RE = re.compile(
    r'{}({}):'.format(OLD_TOKEN_PREFIX, '|'.join(valid_tokens)), flags=re.IGNORECASE
)

test_modules = glob.glob(os.path.join(ROOT_PATH, 'tests', 'foreman', '*', 'test_*.py'))
for test_module in test_modules:
    with open(test_module) as handler:
        content = handler.read()
    content = TOKEN_RE.sub(rf'{NEW_TOKEN_PREFIX}\1:', content)
    with open(test_module, 'w') as handler:
        handler.write(content)
