#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Check that the installer ships every file the driver needs.

A module left out of install.py is invisible here and in CI. It shows up as an
ImportError the first time somebody installs the release, which is the worst place
to find out.
"""

import glob
import os.path
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def installed_files():
    """The paths install.py says it will copy."""
    with open(os.path.join(ROOT, 'install.py'), encoding='utf-8') as fd:
        return set(re.findall(r"'(bin/user/[\w/]+\.py)'", fd.read()))


def package_files():
    """The paths that actually exist."""
    found = set()
    for path in glob.glob(os.path.join(ROOT, 'bin', 'user', '**', '*.py'),
                          recursive=True):
        found.add(os.path.relpath(path, ROOT).replace(os.sep, '/'))
    return found


def test_every_module_is_installed():
    missing = package_files() - installed_files()

    assert not missing, "install.py does not ship: %s" % ', '.join(sorted(missing))


def test_nothing_is_installed_that_does_not_exist():
    phantom = installed_files() - package_files()

    assert not phantom, "install.py ships files that are gone: %s" % ', '.join(sorted(phantom))


def test_the_version_matches_the_package():
    import ecowitt

    with open(os.path.join(ROOT, 'install.py'), encoding='utf-8') as fd:
        declared = re.search(r"VERSION = '([^']+)'", fd.read()).group(1)

    assert declared == ecowitt.VERSION
