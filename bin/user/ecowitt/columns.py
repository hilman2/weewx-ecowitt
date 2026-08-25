#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Which database columns a station actually needs.

A reading only survives the archive interval if the table has a column for it. The
standard schema has 113 of them, and Ecowitt hardware can fill four times that, so
something has to give.

Two ways to handle it. Ship a schema with every field anyone might own, which is what
the alternatives do, and carry four hundred columns for the twelve sensors in the
garden. Or look at what the hardware actually sends and add those.

This does the second. It needs a payload, not a catalog, which is why it lives next to
the listener rather than in the installer.
"""

# Types by unit group, for the columns we have to create. REAL for anything measured,
# INTEGER for anything counted.
COUNTED = frozenset([
    'group_count', 'group_time', 'group_boolean', 'group_data',
])


def schema_fields():
    """The fields WeeWX's standard schema already has. Needs WeeWX importable."""
    from weewx.schemas.wview_extended import table
    return {name for name, _type in table}


def missing(packet, groups, known=None):
    """Return the columns a packet needs and the database does not have.

    Args:
        packet (dict): A loop packet, i.e. what the driver produced.
        groups (dict): WeeWX field -> unit group, for choosing a column type.
        known (set): Fields the database already has. Defaults to the standard schema.

    Returns:
        A list of (field, sql_type), sorted, without the bookkeeping fields.
    """
    if known is None:
        known = schema_fields()
    wanted = []
    for field in sorted(packet):
        if field in ('dateTime', 'usUnits', 'interval') or field in known:
            continue
        sql_type = 'INTEGER' if groups.get(field) in COUNTED else 'REAL'
        wanted.append((field, sql_type))
    return wanted


def commands(wanted, config='/etc/weewx/weewx.conf'):
    """Render the columns as the commands that create them."""
    return ["weectl database add-column %s --type %s --config=%s -y" % (field, sql, config)
            for field, sql in wanted]
