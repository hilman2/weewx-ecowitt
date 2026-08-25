#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Make the driver importable, and hand the captured payloads to the tests."""

import os.path
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bin', 'user'))


@pytest.fixture
def payload():
    """Return a captured payload by name, e.g. payload('hp2561ae_pro')."""

    def _load(name):
        with open(os.path.join(HERE, 'fixtures', name + '.txt'), encoding='utf-8') as fd:
            return fd.read().strip()

    return _load
