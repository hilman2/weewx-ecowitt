# Development

## Layout

```
bin/user/ecowitt/
    protocol.py    text in, named readings out. No sockets, no clock, no WeeWX.
    catalog.py     generated. Raw field to WeeWX field, unit groups, channel counts.
    infer.py       what to do with a field the catalog does not cover.
    mapping.py     the three above, combined into a packet. Still no WeeWX.
    columns.py     which database columns a packet needs.
    driver.py      the WeeWX end: loop packets, unit groups, shutdown.
    __main__.py    the diagnostic command.
bin/user/listener.py   WeeWX's own listener, bundled for WeeWX older than 5.6.
tools/                 catalog and reference generators.
tests/                 pytest, with captured payloads in tests/fixtures.
```

Everything below `driver.py` runs without WeeWX installed. That is what lets the
tests work from a captured payload rather than from mocks.

## Tests

```
pip install pytest
python -m pytest tests -q
```

Without WeeWX, the tests that need it are skipped. With it, everything runs:

```
pip install weewx
python -m pytest tests -q
```

CI runs both, across Python 3.8 to 3.13, plus a vermin check against 3.7.

## The catalog

`bin/user/ecowitt/catalog.py` is generated, not written:

```
python tools/import_catalog.py path/to/ecowittcustom.py \
    --schema path/to/weewx/schemas/wview_extended.py
```

Three lists in `tools/import_catalog.py` decide where a reading goes:

- `CHANNELS` — how far each sensor family reaches
- `REMAP` — families placed differently from the source, with the reason
- `OVERRIDES` — single fields, likewise

The tool reports what it could not settle: fields written by more than one reading,
readings with more than one candidate field, raw names with no target. None of it
passes quietly.

`CONTESTED` in the generated catalog comes from `REMAP` and `OVERRIDES`, so the list
of fields that wait for the user cannot drift from the decisions that made them wait.

## The sensor reference

`docs/Sensors.md` is generated too:

```
python tools/build_reference.py
```

## Checking against Ecowitt

Ecowitt publishes its cloud API, and the pages behind the site come from a plain
endpoint. The channel counts can be verified rather than trusted:

```
python tools/check_against_ecowitt.py
```

```
Ecowitt family           model    documented ours
leaf_ch                  WN35     8          8
soil_ch                  WH51     16         16
temp_ch                  WN34     8          8
```

What this cannot check is the raw field names. The cloud API says
`soil_ch1.soilmoisture` where a console posts `soilmoisture1`, and nothing published
connects the two.

## The bundled listener

`bin/user/listener.py` is a copy of `weewx/listener.py`, byte for byte. A test
compares the two when WeeWX has one, so the copy cannot drift. Do not edit it; when
the core carries the listener, the driver picks that up on its own and the copy can
go.

## Adding a field

1. Add the raw name to the catalog through the generator, not by hand.
2. Give it a unit group if WeeWX does not know the field.
3. If it belongs to a sensor family the driver does not know, add the family to
   `CHANNELS` with its channel count.
4. Add a captured payload to `tests/fixtures` and a test that says what should come
   out of it.

## Releasing

Set the version in `install.py` and `bin/user/ecowitt/__init__.py`, update
`CHANGELOG.md`, then tag:

```
git tag v0.2.0
git push origin v0.2.0
```

The release workflow checks that the tag matches both files, builds the extension
zip, and publishes it.
