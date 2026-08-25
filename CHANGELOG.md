# Changelog

## 0.1.0 (unreleased)

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
