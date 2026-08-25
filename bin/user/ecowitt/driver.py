#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""The WeeWX end of it.

Deliberately thin. The socket belongs to weewx.listener, the protocol to protocol.py,
the field names to catalog.py. What is left here is the part that has to know about
WeeWX: loop packets, unit groups, and shutting down when told to.

Configuration:

    [Ecowitt]
        driver = user.ecowitt.driver
        port = 8000
        # path = /a-secret-of-your-choosing/report
        # infer_unknown = series
        # [[field_map_extensions]]
        #     yearlyrainin = rain_year
"""

import logging

import weewx
import weewx.drivers
import weewx.units

from . import VERSION
from .mapping import Mapper

try:
    # WeeWX 5.6 and later carry the listener.
    from weewx.listener import HTTPListener
    LISTENER_FROM = 'weewx.listener'
except ImportError:
    # Older WeeWX gets the copy that ships with this extension. Byte for byte the same
    # file, checked by a test, and it stops shipping once 5.6 is everywhere.
    from user.listener import HTTPListener
    LISTENER_FROM = 'user.listener, the bundled copy'

log = logging.getLogger(__name__)

DRIVER_NAME = 'Ecowitt'
DRIVER_VERSION = VERSION

# What the gateway wants to hear before it counts the upload as delivered.
ECOWITT_RESPONSE = '{"errcode":"0","errmsg":"ok"}'


def loader(config_dict, _engine):
    return EcowittDriver(**config_dict[DRIVER_NAME])


def confeditor_loader():
    return EcowittConfEditor()


class EcowittDriver(weewx.drivers.AbstractDevice):
    """Receives uploads from Ecowitt hardware and turns them into loop packets."""

    def __init__(self, **stn_dict):
        log.info("Driver version is %s, listening with %s",
                 DRIVER_VERSION, LISTENER_FROM)

        self.model = stn_dict.get('model', 'Ecowitt')
        self.mapper = Mapper(extensions=dict(stn_dict.get('field_map_extensions', {})),
                             infer_unknown=stn_dict.get('infer_unknown', 'series'))
        self._register_units(self.mapper.wanted_groups())

        listener_options = dict(stn_dict)
        listener_options.pop('driver', None)
        listener_options.pop('field_map_extensions', None)
        listener_options.pop('infer_unknown', None)
        listener_options.pop('model', None)
        listener_options.setdefault('response', ECOWITT_RESPONSE)
        listener_options.setdefault('content_type', 'application/json')
        self.listener = HTTPListener(**listener_options)

    @property
    def hardware_name(self):
        return self.model

    def genLoopPackets(self):
        for request in self.listener:
            try:
                packet, guesses = self.mapper.to_packet(request.text)
            except Exception as e:
                log.error("Cannot read a payload from %s: %s", request.client_address, e)
                continue
            if guesses:
                self._register_units(self.mapper.wanted_groups())
            if len(packet) <= 1:
                # Nothing but the timestamp. Usually a probe or a health check.
                continue
            packet['usUnits'] = weewx.US
            yield packet

    def closePort(self):
        self.listener.close()

    @staticmethod
    def _register_units(groups):
        """Tell WeeWX what these fields are, so reports can format them.

        Only fields WeeWX does not already know about are touched. Overriding a group
        it ships with would change the meaning of a field for every other driver.
        """
        for field, group in groups.items():
            weewx.units.obs_group_dict.setdefault(field, group)


class EcowittConfEditor(weewx.drivers.AbstractConfEditor):

    @property
    def default_stanza(self):
        return """
[Ecowitt]
    # This section is for Ecowitt hardware that uploads to a custom server.

    # The port to listen on. Ports below 1024 need root.
    port = 8000

    # Accept this path only. Hardware can rarely send a token any other way, so a
    # path nobody can guess is the practical way to keep strangers out.
    # path = /change-me/report

    # What to do with a field the driver does not know yet:
    #   off     drop it
    #   series  keep it when it continues a known series, report the rest
    #   all     keep whatever can be named, including from naming rules
    infer_unknown = series

    # Some fields are placed differently by different drivers, and the wrong choice
    # puts two sensors in one column. So this has no default: until it says something,
    # those fields are left out and the log names them.
    #
    #   none            this driver's placement. For a fresh start.
    #   ecowittcustom   keep the field names of that driver, so an existing history
    #                   carries on where it is.
    #   gw1000          likewise for the Ecowitt gateway driver.
    #
    # compat = none

    # Your own mapping, which wins over the built-in one.
    [[field_map_extensions]]

    # The driver to use:
    driver = user.ecowitt.driver
"""

    def prompt_for_settings(self):
        settings = {}
        settings['port'] = self._prompt("port", '8000')
        return settings
