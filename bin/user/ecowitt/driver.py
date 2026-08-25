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

from . import VERSION, consoles, protocol, report
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
    options = dict(config_dict[DRIVER_NAME])
    # The console list belongs with the readings it protects, so the driver is given
    # what it needs to reach the database.
    options.setdefault('config_dict', config_dict)
    # Where to keep the list of consoles this driver answers to. Beside weewx.conf,
    # unless the driver section says otherwise.
    options.setdefault('weewx_root', config_dict.get('WEEWX_ROOT'))
    options.setdefault('sqlite_root',
                       config_dict.get('DatabaseTypes', {})
                                  .get('SQLite', {})
                                  .get('SQLITE_ROOT'))
    return EcowittDriver(**options)


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

        # Which consoles to answer to. Anyone who can reach the port can point a
        # console at it, and a second one writing the same channels would mix two
        # sensors into one column. So the driver accepts the ones it knows and
        # refuses the rest.
        self.console_file = consoles.path_for(stn_dict.get('weewx_root'),
                                              stn_dict.get('console_file'),
                                              stn_dict.get('sqlite_root'))
        self.store = consoles.Store(self.console_file, stn_dict.get('config_dict'),
                                    stn_dict.get('data_binding', 'wx_binding'))
        self.configured_passkey = stn_dict.get('passkey')
        self.known = self._known_consoles(self.configured_passkey)

        listener_options = dict(stn_dict)
        listener_options.pop('driver', None)
        listener_options.pop('field_map_extensions', None)
        listener_options.pop('infer_unknown', None)
        listener_options.pop('model', None)
        listener_options.pop('report_file', None)
        listener_options.pop('stations', None)
        listener_options.pop('passkey', None)
        listener_options.pop('console_file', None)
        listener_options.pop('weewx_root', None)
        listener_options.pop('sqlite_root', None)
        listener_options.pop('data_binding', None)
        listener_options.pop('config_dict', None)
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

    def _known_consoles(self, passkey):
        """The PASSKEYs this driver answers to.

        From the driver section, from [[stations]], or from the file where the first
        console ever heard was recorded. Empty means nothing has been heard yet, and
        the next console to upload is adopted.
        """
        known = set(self.stations)
        if passkey:
            known.add(str(passkey).strip())
        if known:
            return known
        remembered = set(self.store.read())
        if remembered:
            log.info("Answering to %d console(s) on record in the %s",
                     len(remembered), self.store.where)
        return remembered

    def _adopt(self, passkey, client):
        """Record the first console ever heard, and answer to it from then on."""
        self.known.add(passkey)
        where = self.store.add(passkey, "first console seen, from %s" % client)
        log.info("Console '%s' at %s is now this driver's station, on record in the "
                 "%s. Uploads from any other console are refused until it is named "
                 "under [[stations]].", passkey, client, where or 'log only')
        self._suggest_passkey(passkey)

    def _suggest_passkey(self, passkey):
        """Point at the setting that does not depend on a file surviving.

        The file is a convenience. A copied database, a rebuilt machine or a
        directory nobody backed up leaves it behind, and then the next console to
        upload becomes the station. One line in weewx.conf does not have that
        problem, so say so where somebody will see it.
        """
        if self.configured_passkey or self.stations:
            return
        log.info("To keep it independent of anything stored, put it in weewx.conf: "
                 "'passkey = %s' under [Ecowitt].", passkey)

    def _mapper_for(self, text, client):
        """Which mapping this upload belongs to, or None to leave it alone."""
        passkey = protocol.station_id(text)

        if not self.known:
            self._adopt(passkey, client)

        if passkey not in self.known:
            self._refuse(passkey, client)
            return None, None

        if self.mapper is not None:
            return None, self.mapper
        return self.stations[passkey]

    def _refuse(self, passkey, client):
        if passkey in self.unknown_consoles:
            return
        self.unknown_consoles.add(passkey)
        log.warning(
            "An upload from %s carries PASSKEY '%s', which is not one of this "
            "driver's consoles. Ignoring it. If it is yours, add it under "
            "[[stations]] with its own field map: two consoles number their channels "
            "from one, and would otherwise write into the same fields.",
            client, passkey)

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
            if len(packet) <= 1:
                # Nothing but the timestamp. Usually a probe or a health check.
                continue
            packet['usUnits'] = weewx.US
            if name:
                packet['station'] = name
            yield packet

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
