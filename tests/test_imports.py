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

# The parser, the catalog and the inference are the parts that have to work with
# nothing but Python, so that the tests can run from a captured payload.
WITHOUT_WEEWX = ['ecowitt', 'ecowitt.catalog', 'ecowitt.columns',
                 'ecowitt.infer', 'ecowitt.mapping', 'ecowitt.protocol']
# The listener is WeeWX's own file, bundled here for older installations. It uses
# weeutil, as the core copy does, so it needs WeeWX like the driver does.
WITH_WEEWX = ['ecowitt.driver', 'ecowitt.__main__', 'user.listener']


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
