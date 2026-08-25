#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""From named readings to a WeeWX packet.

This is where the catalog, the user's own mapping and the inference meet. It stays
free of WeeWX imports so that it can be tested with nothing but a captured payload:
the unit groups it wants registered come back as data, and the driver does the
registering.
"""

import logging
import re

from . import catalog, infer, protocol

log = logging.getLogger(__name__)

# What to do about a field the catalog does not cover.
OFF = 'off'          # drop it, the way every other driver does
SERIES = 'series'    # take it when it continues a series, report the rest
ALL = 'all'          # take whatever can be named, including from rules
MODES = (OFF, SERIES, ALL)


class Mapper:
    """Turns raw readings into a WeeWX packet.

    Args:
        extensions (dict): Raw field -> WeeWX field, overriding the catalog. This is
            the user's own mapping, from the configuration file.
        infer_unknown (str): 'off', 'series' or 'all'. See above. Default 'series',
            i.e. accept what can be derived and merely report what was guessed.
    """

    def __init__(self, extensions=None, infer_unknown=SERIES):
        if infer_unknown not in MODES:
            raise ValueError("infer_unknown must be one of %s, not '%s'"
                             % (', '.join(MODES), infer_unknown))
        self.mode = infer_unknown
        self.fields = dict(catalog.FIELDS)
        self.fields.update(extensions or {})
        self.groups = dict(catalog.GROUPS)
        self.inferrer = infer.Inferrer(self.fields, self.groups)
        # Every unmapped field is looked at once. After that it is either part of the
        # mapping or a known refusal, and either way it does not need saying again.
        self.seen = {}
        self.ignored = set()

    def to_packet(self, text, now=None):
        """Return (packet, guesses) for one payload.

        The packet is ready for WeeWX apart from its unit system, which the caller
        sets, because that is a decision about the whole driver rather than about one
        reading. Guesses are the fields that were not in the mapping, whether or not
        they made it into the packet.
        """
        raw = protocol.parse(text)
        readings, _ = protocol.numbers(raw)

        packet = {}
        fresh = []
        for name, value in readings.items():
            field = self.fields.get(name)
            if field is None:
                field = self._unmapped(name, fresh)
                if field is None:
                    continue
            packet[field] = value

        stamp = protocol.device_time(raw, now=now)
        packet['dateTime'] = int(stamp if stamp is not None
                                 else (now if now is not None else _now()))
        return packet, fresh

    def _unmapped(self, name, fresh):
        """Decide what happens to a field that is not in the mapping."""
        if name in self.ignored:
            return None
        if name in self.seen:
            return self.seen[name].field

        guess = self.inferrer.guess(name)
        if guess is None:
            log.info("No idea what '%s' is. Left out.", name)
            self.ignored.add(name)
            return None

        fresh.append(guess)
        take = self.mode == ALL or (self.mode == SERIES and guess.certain)
        if not take:
            log.info("New field '%s' looks like %s (%s), but it was only guessed. "
                     "Left out. Add it to field_map_extensions to keep it.",
                     name, guess.group or 'unknown', guess.why)
            self.ignored.add(name)
            return None

        log.info("New field '%s' -> '%s' (%s), %s.%s", name, guess.field,
                 guess.group or 'no group', guess.why, placement_note(name) or '')
        self.seen[name] = guess
        if guess.group:
            self.groups[guess.field] = guess.group
        return guess.field

    def wanted_groups(self):
        """Unit groups the packet needs, for the caller to register with WeeWX."""
        return dict(self.groups)


def placement_note(raw):
    """Say so when the field name claims more than the hardware does.

    A WN34 reports on tf_chN whether it is a probe in a bed or a lead in a pool, and
    the catalog has to call it something. Whoever installed it is the only one who
    knows, so the moment a new channel turns up is the moment to say that.
    """
    for prefix, note in catalog.PLACEMENT_UNKNOWN.items():
        if re.match(re.escape(prefix) + r'\d', raw):
            return " Placement is a convention, not a reading: " + note
    return None


def _now():
    import time
    return time.time()
