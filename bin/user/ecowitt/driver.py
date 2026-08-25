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

from . import VERSION, protocol, report
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
        self.infer_unknown = stn_dict.get('infer_unknown', 'series')

        # One mapping, or one per console. Two consoles both number their channels
        # from one, so without this a WN34 on channel 1 of each would overwrite the
        # other, and afterwards neither could be recovered.
        self.stations = self._read_stations(stn_dict.get('stations'))
        self.mapper = None if self.stations else Mapper(
            extensions=dict(stn_dict.get('field_map_extensions', {})),
            infer_unknown=self.infer_unknown)
        for mapper in self._mappers():
            self._register_units(mapper.wanted_groups())
        self.unknown_consoles = set()
        # Which fields each console has written, when they share one mapping. A second
        # console is common: people add a gateway to reach sensors the first cannot
        # hear. Both number their channels from one, so the same field can arrive from
        # both, and the later one would overwrite a reading nothing can recover.
        self.written_by = {}
        self.collisions = set()

        listener_options = dict(stn_dict)
        listener_options.pop('driver', None)
        listener_options.pop('field_map_extensions', None)
        listener_options.pop('infer_unknown', None)
        listener_options.pop('model', None)
        listener_options.pop('report_file', None)
        listener_options.pop('stations', None)
        listener_options.setdefault('response', ECOWITT_RESPONSE)
        listener_options.setdefault('content_type', 'application/json')

        self.report_file = stn_dict.get('report_file', report.DEFAULT_PATH)
        self.reported = False

        self.listener = HTTPListener(**listener_options)

    @property
    def hardware_name(self):
        return self.model

    def _read_stations(self, configured):
        """Return {PASSKEY: (name, Mapper)} for a station with several consoles."""
        if not configured:
            return {}
        stations = {}
        for name, options in configured.items():
            passkey = options.get('passkey')
            if not passkey:
                raise ValueError("Station '%s' has no 'passkey'. It is the value the "
                                 "console sends first in every upload." % name)
            stations[str(passkey).strip()] = (name, Mapper(
                extensions=dict(options.get('field_map_extensions', {})),
                infer_unknown=options.get('infer_unknown', self.infer_unknown)))
        log.info("Listening for %d consoles: %s",
                 len(stations), ', '.join(sorted(n for n, _ in stations.values())))
        return stations

    def _mappers(self):
        if self.mapper is not None:
            return [self.mapper]
        return [mapper for _name, mapper in self.stations.values()]

    def _mapper_for(self, text, client):
        """Which mapping this upload belongs to, or None to leave it alone."""
        if self.mapper is not None:
            return None, self.mapper
        passkey = protocol.station_id(text)
        found = self.stations.get(passkey)
        if found:
            return found
        if passkey not in self.unknown_consoles:
            self.unknown_consoles.add(passkey)
            log.warning("An upload from %s carries PASSKEY '%s', which is not one of "
                        "the consoles configured under [[stations]]. Ignoring it. Add "
                        "it there to keep its readings.", client, passkey)
        return None, None

    def genLoopPackets(self):
        for request in self.listener:
            name, mapper = self._mapper_for(request.text, request.client_address)
            if mapper is None:
                continue
            try:
                packet, guesses = mapper.to_packet(request.text)
            except Exception as e:
                log.error("Cannot read a payload from %s: %s", request.client_address, e)
                continue
            if guesses:
                self._register_units(mapper.wanted_groups())
            self._maybe_report(request.text, guesses)
            if self.mapper is not None:
                packet = self._one_console_per_field(packet, request.text)
            if len(packet) <= 1:
                # Nothing but the timestamp. Usually a probe or a health check.
                continue
            packet['usUnits'] = weewx.US
            if name:
                packet['station'] = name
            yield packet

    def _one_console_per_field(self, packet, text):
        """Keep a second console from overwriting the first, field by field.

        Only for stations that have not named their consoles. Two gateways is a
        normal arrangement and mostly harmless, because they usually carry different
        sensors. It stops being harmless when they carry the same channel: whichever
        uploaded last would win, and the two series could never be separated again.

        So the console that got there first keeps the field, and the other one's
        reading is dropped rather than written over it.
        """
        console = protocol.station_id(text)
        dropped = []
        for field in list(packet):
            if field == 'dateTime':
                continue
            owner = self.written_by.setdefault(field, console)
            if owner != console:
                del packet[field]
                dropped.append(field)
        if dropped:
            self._say_collision(console, dropped)
        return packet

    def _say_collision(self, console, dropped):
        fresh = [field for field in dropped if field not in self.collisions]
        if not fresh:
            return
        self.collisions.update(fresh)
        log.warning(
            "Two consoles are sending here, and both write %s. The readings from '%s' "
            "are being dropped, because mixing two sensors into one column cannot be "
            "undone afterwards. Give each console its own field map under "
            "[[stations]], one entry per PASSKEY. See the Several consoles page.",
            ', '.join("'%s'" % f for f in sorted(fresh)), console)

    def _maybe_report(self, payload, guesses):
        """Write out one upload, the first time something cannot be placed.

        Getting hold of a raw upload otherwise means reconfiguring the console and
        waiting for an interval. The driver has it in hand, so it writes it once and
        says where the file is.
        """
        if self.reported or not self.report_file:
            return
        waiting = {}
        for mapper in self._mappers():
            waiting.update({raw: field for raw, field in mapper.undecided.items()
                            if raw in mapper.warned})
        if not guesses and not waiting:
            return
        self.reported = True
        path = report.write(payload, guesses, waiting, self.report_file)
        if path:
            log.info("This station sends fields I cannot place on my own. Everything "
                     "needed to report them is in %s", path)

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

    # Where to leave a report when the station sends something the driver cannot
    # place. Set it empty to switch that off.
    report_file = /var/tmp/weewx-ecowitt-report.txt

    # A few fields are placed differently by different drivers, and the wrong choice
    # mixes two sensors into one column. Those are not written until you name them
    # below. The log prints both candidate lines the first time each one arrives.

    # Your own mapping, which wins over the built-in one.
    [[field_map_extensions]]

    # The driver to use:
    driver = user.ecowitt.driver
"""

    def prompt_for_settings(self):
        settings = {}
        settings['port'] = self._prompt("port", '8000')
        return settings
