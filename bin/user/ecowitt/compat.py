#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Keeping a history that started under another driver.

Changing driver should not change what a column means. Somebody arriving from
`ecowittcustom` has years of WN34 readings in `soilTemp1`, because that is where that
driver put them. This driver puts a WN34 on `extraTemp9` and a WH52 on `soilTemp1`,
which is the right way round for a fresh install and quietly wrong for theirs: the
old series stops, and a different sensor starts writing into it.

So say where you came from:

    [Ecowitt]
        compat = ecowittcustom

The profile is applied before `field_map_extensions`, so anything you set yourself
still wins. Nothing here is permanent: to move a series onto the new field later,
rename the column with `weectl database rename-column` and drop the setting.
"""

import logging

log = logging.getLogger(__name__)

NONE = 'none'

# Raw field -> where the older driver put it.
PROFILES = {
    # Werner Krenn's ecowittcustom, and the interceptor forks that share its maps.
    'ecowittcustom': dict(
        [('tf_ch%d' % n, 'soilTemp%d' % n) for n in range(1, 17)]
        + [('tf_batt%d' % n, 'soilTempBatt%d' % n) for n in range(1, 17)]
        + [('soil_ec_temp%d' % n, 'soilmTemp%d' % n) for n in range(1, 17)]
        + [('lightning_time', 'lightning_disturber_count')]
    ),
    # The Ecowitt gateway driver, which this driver already agrees with about the
    # WN34. Listed so that saying where you came from is never wrong.
    'gw1000': dict(
        [('tf_ch%d' % n, 'extraTemp%d' % (n + 8)) for n in range(1, 9)]
    ),
}


def profile(name):
    """Return the mapping for a named profile. Unknown names are an error."""
    if not name or name == NONE:
        return {}
    try:
        mapping = PROFILES[name]
    except KeyError:
        raise ValueError("Unknown compat profile '%s'. Use one of: %s, %s"
                         % (name, ', '.join(sorted(PROFILES)), NONE))
    log.info("Keeping the field names of '%s' for %d fields, so an existing history "
             "carries on where it is.", name, len(mapping))
    return dict(mapping)
