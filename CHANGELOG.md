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
- `compat = ecowittcustom` keeps the field names of the driver a history was started
  under, so a series does not stop and a different sensor does not continue it.
- `python -m user.ecowitt` reports which of the fields it would write to already hold
  readings, before anything is changed.
- Uses `weewx.listener` where available, and ships a copy for older WeeWX.
