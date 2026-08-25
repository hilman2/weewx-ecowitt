#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Installer for the Ecowitt driver."""

from weecfg.extension import ExtensionInstaller

VERSION = '0.1.0'


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
                    'field_map_extensions': {}}},
            files=[
                ('bin/user', ['bin/user/listener.py']),
                ('bin/user/ecowitt', ['bin/user/ecowitt/__init__.py',
                                      'bin/user/ecowitt/catalog.py',
                                      'bin/user/ecowitt/driver.py',
                                      'bin/user/ecowitt/infer.py',
                                      'bin/user/ecowitt/mapping.py',
                                      'bin/user/ecowitt/protocol.py']),
            ]
        )
