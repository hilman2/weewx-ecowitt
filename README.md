# weewx-ecowitt

A WeeWX driver for Ecowitt hardware that uploads to a custom server. It listens for the
uploads a gateway or console sends, and turns them into WeeWX records.

Works with anything that offers "Customized" upload in the WSView app, which is most of
the range: GW1000, GW1100, GW1200, GW2000, GW3000, HP2551, HP2561, WS3800, WS3900,
WS3910, WN1980 and their relatives. Both the Ecowitt protocol and the Weather
Underground protocol are read.

## Why another one

Because the field lists are the hard part, and they keep changing. Ecowitt ships new
sensors faster than drivers get updated, and the usual outcome is that readings arrive
and are thrown away. A current HP2561AE Pro sends 45 fields. `weewx-interceptor` maps
25 of them and logs `unrecognized parameter` for the other 20, including the lightning
sensor, both soil probes and the whole WH52.

The raw field names come from Werner Krenn's `ecowittcustom`, which knows more of them
than anything else. Where they belong in WeeWX is decided here, from what the sensors
actually are. On top of that:

- **New fields are not silently dropped.** A field that continues a series the catalog
  already describes is taken, so a channel the hardware gains needs no release. A field
  that is merely recognisable by its name is reported with what it looks like, and left
  out until somebody decides.
- **The socket is not ours.** It comes from `weewx.listener`, so threads, shutdown,
  body limits, IPv6 and token checking are the core's problem and not another private
  copy of the same 200 lines.

## Install

    weectl extension install https://github.com/hilman2/weewx-ecowitt/releases/latest/download/weewx-ecowitt.zip
    weectl station reconfigure

Then point the hardware at it. In the WSView app: *Weather Services*, then *Customized*,
protocol *Ecowitt*, server the address of the machine running WeeWX, path and port as
configured below.

## Configure

```ini
[Ecowitt]
    driver = user.ecowitt.driver
    port = 8000

    # Accept this path only. Hardware can rarely send a token any other way, so a path
    # nobody can guess is the practical way to keep strangers out.
    path = /change-me/report

    # What to do with a field the driver does not know yet.
    infer_unknown = series

    [[field_map_extensions]]
        # Your own mapping wins over the built-in one.
        yearlyrainin = rain_year
```

`port`, `address`, `path`, `token`, `allowed_hosts`, `trust_proxy`, `max_body` and
`log_raw` are passed to the listener. They are documented in the WeeWX customization
guide, under *Porting to new hardware*.

### infer_unknown

| Value | What happens to a field the catalog does not cover |
|---|---|
| `off` | Dropped, the way other drivers do it. Still logged. |
| `series` | Taken when it continues a known series **and** the family's placement is not in question. Anything else is reported and left out. This is the default. |
| `all` | Taken whenever the name says what it measures, e.g. `mph` is a wind speed. |

`series` is the default because a derived field is not a guess. But being sure where a
channel *belongs* is not the same as being sure the field is *free*. A new WN34 channel
would land on `extraTemp`, where a sensor you set up two years ago may already have its
history, and two series in one column cannot be told apart afterwards. So a channel from
a family whose placement is a convention waits for you, with the line to paste:

    INFO user.ecowitt.mapping: New channel 'temp9f' would go to 'extraTemp9'. Which
        sensor that is, and whether that field is free, only you know. Add
        'temp9f = extraTemp9' under [[field_map_extensions]] to accept it.

Families with nowhere else to be, such as a laser rangefinder's depth or a lightning
count, are taken without asking. `all` will get you everything sooner, at the risk of a
unit nobody checked.

Whatever the setting, the log says what turned up:

    INFO user.ecowitt.mapping: New field 'leafwetness_ch5' -> 'leafWet5'
        (group_percent), continues leafwetness_ch, e.g. leafWet1

A field only reaches the database if the archive table has a column for it. Fields
outside the standard schema need `weectl database add-column` first.

## Documentation

| | |
|---|---|
| [Installation](docs/Installation.md) | install, point the hardware at it, start |
| [Configuration](docs/Configuration.md) | every option, with worked examples |
| [Field map](docs/Field-map.md) | how a reading gets to a column |
| [Hardware](docs/Hardware.md) | every device: arrays, consoles, sensors, older Fine Offset kit |
| [Sensors](docs/Sensors.md) | every field this driver knows, by sensor |
| [Unknown fields](docs/Unknown-fields.md) | what happens to a field the catalog misses |
| [Several consoles](docs/Several-consoles.md) | a second gateway, without the two overwriting each other |
| [Database columns](docs/Database-columns.md) | which columns a station needs |
| [Diagnostics](docs/Diagnostics.md) | one command that answers most questions |
| [Reporting a new sensor](docs/New-sensors.md) | exactly what to send |
| [Troubleshooting](docs/Troubleshooting.md) | symptoms and what they mean |
| [Keeping strangers out](docs/Security.md) | path, token, addresses, TLS |
| [Development](docs/Development.md) | layout, tests, rebuilding the catalog |

## Where the fields come from

The catalog is generated, not typed. `tools/import_catalog.py` reads the raw field
names out of the `ecowittcustom` driver by [Werner
Krenn](https://github.com/WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin) and writes
`bin/user/ecowitt/catalog.py`. Run it again when Ecowitt ships something new and the
addition is a reviewable diff rather than a merge nobody can check.

What a field *is* comes from the hardware and is not negotiable. Where it *goes* is
decided in that tool, in three lists that are meant to be read:

- `CHANNELS`, how far each sensor family reaches, from Ecowitt's compatibility table.
- `REMAP`, families placed differently from upstream, with the reason next to them.
  The WN34 and the WH52 are there.
- `OVERRIDES`, single fields, likewise with the reason. Currently one, the lightning
  timestamp that upstream keeps in a counter.

The generator reports what it could not settle: fields written by more than one
reading, readings upstream sends to more than one field, and raw names with no target
at all. None of that is allowed to pass quietly.

## Tests

    pip install pytest
    python -m pytest tests -q

The parser, the catalog and the inference need nothing but Python. That is deliberate:
the tests run from captured payloads, so a change that would have dropped a field fails
a test rather than turning up in somebody's database a month later. Captured payloads
live in `tests/fixtures`, with the `PASSKEY` removed.

## Credit and licence

GPLv3, like everything it descends from.

- The field catalog comes from `ecowittcustom` by Werner Krenn.
- That driver descends from `weewx-interceptor` by Matthew Wall, which is where the
  approach of listening for the upload comes from in the first place.
- WeeWX is by Tom Keffer and Matthew Wall.
