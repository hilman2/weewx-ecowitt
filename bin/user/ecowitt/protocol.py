#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Turn what the hardware sent into named readings.

Ecowitt gateways and consoles speak two protocols, and both end up here:

    Ecowitt   POST, an urlencoded form body
    Wunderground   GET, the same shape in the query string

So a single function handles both. Everything in this module is pure: text in, a
dictionary out, no sockets, no clock, no configuration. That is what makes the field
work testable from a captured payload.
"""

import logging
import re
import time
import urllib.parse

log = logging.getLogger(__name__)

# Fields that identify the device rather than measure anything.
METADATA = frozenset([
    'PASSKEY', 'stationtype', 'model', 'freq', 'dateutc', 'ID', 'PASSWORD',
    'action', 'realtime', 'rtfreq', 'softwaretype', 'runtime', 'heap', 'interval',
])

# How the device stamps its own time.
DEVICE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def parse(text):
    """Split a payload into raw name/value pairs.

    Works for both protocols, because a urlencoded body and a query string are the same
    thing. Returns a dict of strings, in the order they arrived.
    """
    if not text:
        return {}
    if text.startswith('?'):
        text = text[1:]
    return dict(urllib.parse.parse_qsl(text, keep_blank_values=False))


def device_time(raw, now=None, tolerance=86400):
    """Return the timestamp the device sent, or None if it is not usable.

    Consoles are frequently wrong about the time, sometimes by years, and a record
    stamped in 2015 is worse than no record at all. So a device time is only accepted
    when it is close enough to ours to be plausible.
    """
    stamp = raw.get('dateutc')
    if not stamp or stamp == 'now':
        return None
    try:
        parsed = time.strptime(stamp, DEVICE_TIME_FORMAT)
    except ValueError:
        log.debug("Cannot read device time '%s'", stamp)
        return None
    # The device sends UTC. calendar.timegm would be the obvious call, but this keeps
    # the module free of one more import.
    seconds = _timegm(parsed)
    if now is None:
        now = time.time()
    if abs(seconds - now) > tolerance:
        log.warning("Device time %s is %.0f hours away from ours. Using ours.",
                    stamp, abs(seconds - now) / 3600.0)
        return None
    return seconds


def _timegm(parsed):
    """Seconds since the epoch for a struct_time that is already UTC."""
    import calendar
    return calendar.timegm(parsed)


def numbers(raw):
    """Split raw values into the numeric ones and the rest.

    Returns (readings, text), where readings holds everything that could be read as a
    number, and text holds identifiers, model names and anything else that could not.
    A value the hardware sends as an empty field, or as one of its several ways of
    saying "no reading", becomes None rather than being dropped, because a gap is a
    fact about the sensor.
    """
    readings = {}
    text = {}
    for name, value in raw.items():
        if name in METADATA:
            text[name] = value
            continue
        if value in ('', '--', '--.-', '-', 'None', 'null'):
            readings[name] = None
            continue
        try:
            readings[name] = float(value)
        except (TypeError, ValueError):
            text[name] = value
    return readings, text


# Values that identify a station rather than describe the weather.
SECRETS = ('PASSKEY', 'ID', 'PASSWORD', 'key', 'stationkey')


def redact(text):
    """Replace the values that identify a station, leaving the readings alone.

    A payload is going to be pasted into an issue tracker, and the PASSKEY is what
    Ecowitt's servers use to recognise a station. Everything else in there is weather.
    """
    for name in SECRETS:
        text = re.sub(r'(^|[?&])%s=[^&]*' % re.escape(name),
                      r'\g<1>%s=X' % name, text)
    return text
