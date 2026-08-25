#
#    Copyright (c) 2026 Manuel Hilgert
#
#    See the file LICENSE for your full rights.
#
"""Listen once, and say what the hardware is sending.

Run this before wiring anything up, or when a sensor is missing from the reports:

    python -m user.ecowitt --port 8000

It waits for one upload, then prints what arrived, what the driver could not place,
and the commands that would give the readings somewhere to live. Nothing is changed,
and WeeWX does not have to be stopped as long as this uses a different port.
"""

import argparse
import logging
import sys

from . import VERSION, columns, infer
from .mapping import Mapper, placement_note

try:
    from weewx.listener import HTTPListener
except ImportError:
    from user.listener import HTTPListener

ECOWITT_RESPONSE = '{"errcode":"0","errmsg":"ok"}'


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m user.ecowitt', description=__doc__)
    parser.add_argument('--port', default=8000, help="Port to listen on. Default 8000.")
    parser.add_argument('--address', default='', help="Address to bind to.")
    parser.add_argument('--path', help="Accept this path only.")
    parser.add_argument('--samples', type=int, default=1,
                        help="How many uploads to wait for. Default 1.")
    parser.add_argument('--timeout', type=int, default=300,
                        help="Seconds to wait before giving up. Default 300.")
    parser.add_argument('--config', default='/etc/weewx/weewx.conf',
                        help="Path to weewx.conf, for the commands printed at the end.")
    parser.add_argument('--infer-unknown', default='all', choices=['off', 'series', 'all'],
                        help="Default 'all' here, so that everything gets a proposal.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    print("weewx-ecowitt %s. Listening on %s:%s. Point the console here."
          % (VERSION, args.address or '*', args.port))

    mapper = Mapper(infer_unknown=args.infer_unknown)
    packet = {}
    guesses = []
    seen = 0

    listener = HTTPListener(port=args.port, address=args.address, path=args.path,
                            response=ECOWITT_RESPONSE, content_type='application/json')
    try:
        while seen < args.samples:
            request = listener.get(timeout=args.timeout)
            if request is None:
                print("Nothing arrived in %d seconds." % args.timeout, file=sys.stderr)
                return 1
            print("\n%s" % request)
            one, fresh = mapper.to_packet(request.text)
            packet.update(one)
            guesses.extend(fresh)
            seen += 1
    finally:
        listener.close()

    _report(packet, guesses, mapper, args.config)
    return 0


def _report(packet, guesses, mapper, config):
    readings = {f: v for f, v in packet.items() if f != 'dateTime'}
    print("\n%d readings" % len(readings))
    for field, value in sorted(readings.items()):
        print("  %-26s %s" % (field, value))

    if guesses:
        print("\n%d fields were not in the catalog" % len(guesses))
        for line in infer.report(guesses):
            print("  " + line)
        flagged = {g.raw for g in guesses if placement_note(g.raw)}
        if flagged:
            print("\n  Placement of these is a convention, not a reading. Say where they"
                  "\n  really are with field_map_extensions: %s" % ' '.join(sorted(flagged)))

    try:
        wanted = columns.missing(packet, mapper.wanted_groups())
    except ImportError:
        print("\nWeeWX is not importable here, so the columns cannot be worked out.",
              file=sys.stderr)
        return

    if not wanted:
        print("\nEvery reading has a column already.")
        return
    print("\n%d readings have nowhere to live. They will show up in reports as current"
          "\nconditions and be gone at the next archive interval. To keep them:\n"
          % len(wanted))
    for command in columns.commands(wanted, config):
        print("  " + command)
    print("\nBack up the database first. Adding a column rewrites the table.")


if __name__ == '__main__':
    sys.exit(main())
