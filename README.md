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

This driver takes the field catalog from Werner Krenn's `ecowittcustom`, which is the
most complete one there is, and adds two things:

- **New fields are not silently dropped.** A field that continues a series the catalog
  already describes is taken. `tf_ch1` to `tf_ch8` are known to be `soilTemp1` to
  `soilTemp8`, so `tf_ch9` is `soilTemp9`, and no release is needed for that. A field
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
| `series` | Taken when it continues a known series. Anything else is reported and left out. This is the default. |
| `all` | Taken whenever the name says what it measures, e.g. `mph` is a wind speed. |

`series` is the default because a derived field is not a guess. `all` will get you the
reading sooner, at the risk of a unit nobody checked. Whatever the setting, the log says
what turned up:

    INFO user.ecowitt.mapping: New field 'tf_ch9' -> 'soilTemp9' (group_temperature),
        continues tf_ch, e.g. soilTemp1

A field only reaches the database if the archive table has a column for it. Fields
outside the standard schema need `weectl database add-column` first.

## Where the fields come from

The catalog is generated, not typed. `tools/import_catalog.py` reads the field maps out
of the `ecowittcustom` driver by [Werner
Krenn](https://github.com/WernerKr/Ecowitt-or-DAVIS-stations-and-Season-skin) and writes
`bin/user/ecowitt/catalog.py`. Running it again after an update upstream produces a diff
that can be reviewed, rather than a merge nobody can check.

Where this driver knowingly differs from upstream, the reason is written down in the
tool. There are two kinds of difference so far: a reading that upstream maps to more
than one field goes to the one in the WeeWX schema, so that skins find it; and the time
of the last lightning strike goes to `lightning_time` rather than into a counter.

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
