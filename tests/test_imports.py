#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Import every module.

Sounds trivial. It is not: __main__.py is never imported by the other tests, so a
syntax error in it would ship. This is the cheapest possible guard against that.
"""

import importlib

import pytest

WITHOUT_WEEWX = ['ecowitt', 'ecowitt.catalog', 'ecowitt.columns',
                 'ecowitt.infer', 'ecowitt.mapping', 'ecowitt.protocol', 'listener']
WITH_WEEWX = ['ecowitt.driver', 'ecowitt.__main__']


@pytest.mark.parametrize('name', WITHOUT_WEEWX)
def test_imports_without_weewx(name):
    assert importlib.import_module(name)


@pytest.mark.parametrize('name', WITH_WEEWX)
def test_imports_with_weewx(name):
    pytest.importorskip('weewx', reason="WeeWX is not installed")
    assert importlib.import_module(name)


def test_the_command_line_help_works():
    """argparse builds its help from the same strings the module defines."""
    pytest.importorskip('weewx', reason="WeeWX is not installed")
    from ecowitt.__main__ import main

    with pytest.raises(SystemExit) as caught:
        main(['--help'])
    assert caught.value.code == 0
