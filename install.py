#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Installer for the Ecowitt driver."""

from weecfg.extension import ExtensionInstaller

VERSION = '0.1.2'


def loader():
    return EcowittInstaller()


class EcowittInstaller(ExtensionInstaller):
    def __init__(self):
        super(EcowittInstaller, self).__init__(
            version=VERSION,
            name='ecowitt',
            description='Collect data from Ecowitt hardware that uploads to a '
                        'custom server.',
            author="Manuel Hilgert",
            author_email="hilman2@gmail.com",
            config={
                'Station': {
                    'station_type': 'Ecowitt'},
                'Ecowitt': {
                    'driver': 'user.ecowitt.driver',
                    'port': '8000',
                    'infer_unknown': 'series',
                    # 'compat' is deliberately absent. Fields that drivers place
                    # differently stay out until somebody says which placement is
                    # wanted, because the wrong one cannot be undone.
                    'field_map_extensions': {}}},
            files=[
                ('bin/user', ['bin/user/listener.py']),
                # Every module in the package. A test keeps this list complete,
                # because a missing one shows up as an ImportError on somebody else's
                # machine and nowhere earlier.
                ('bin/user/ecowitt', ['bin/user/ecowitt/__init__.py',
                                      'bin/user/ecowitt/__main__.py',
                                      'bin/user/ecowitt/catalog.py',
                                      'bin/user/ecowitt/columns.py',
                                      'bin/user/ecowitt/driver.py',
                                      'bin/user/ecowitt/infer.py',
                                      'bin/user/ecowitt/mapping.py',
                                      'bin/user/ecowitt/protocol.py',
                                      'bin/user/ecowitt/report.py']),
            ]
        )
