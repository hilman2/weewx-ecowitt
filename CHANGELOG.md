# Changelog

## 0.1.2 (2026-08-25)

The listener now says when it has stopped listening. A dead thread used to look
exactly like a station that had gone quiet, and a driver waiting on it would have
waited for good.

Tests for the failure modes: a parser that raises costs one packet rather than the
process, rubbish and oversized uploads cost nothing, a response callback that raises
still stores the reading, and a flood drops readings rather than growing without
limit.

## 0.1.1 (2026-08-25)

Fixes an installation that could not start. `install.py` left out `columns.py`,
`report.py` and `__main__.py`, so `weectl extension install` copied a package that
raised `ImportError` on the first start. The release archive contained them; the
installer did not copy them.

A test now compares the file list in `install.py` against the package, so a module
cannot be left out again.

Nobody who installed 0.1.0 has a working driver. Install this one over it.

## 0.1.0 (2026-08-25)

First version.

- Reads the Ecowitt and Weather Underground protocols from a custom-server upload.
- Field catalog generated from `ecowittcustom` by Werner Krenn: 524 fields.
- Fields that continue a known series are taken without a release, e.g. `tf_ch9`
  becomes `soilTemp9`. Fields that are only recognisable by name are reported and left
  out unless `infer_unknown = all`.
- A reading that upstream maps to more than one field goes to the one in the WeeWX
  schema, so that skins and reports find it.
- The time of the last lightning strike goes to `lightning_time`, not into
  `lightning_disturber_count`.
- Fields whose placement the hardware does not settle are not written until they are
  named in `field_map_extensions`. Six of them on a station with two WN34 probes, a
  WH52 and a lightning sensor; the other twenty-nine readings arrive as usual.
- `python -m user.ecowitt` reports which of the fields it would write to already hold
  readings, before anything is changed.
- When a station sends something the driver cannot place, it writes the raw upload
  and its findings to `/var/tmp/weewx-ecowitt-report.txt`, with the PASSKEY replaced.
  Reporting a new sensor is then one `cat` and a paste.
- Uses `weewx.listener` where available, and ships a copy for older WeeWX.
