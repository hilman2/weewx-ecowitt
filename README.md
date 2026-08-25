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

## Coming from another driver

Changing driver should not change what a column means, and this one does not place
everything the way its predecessors did. Somebody arriving from `ecowittcustom` has
years of WN34 readings in `soilTemp1`, because that is where that driver put them. Here
a WN34 goes to `extraTemp9` and a WH52 goes to `soilTemp1`, which is right for a fresh
install and quietly wrong for theirs: the old series stops, and a different sensor
starts writing into it.

So say where you came from:

```ini
[Ecowitt]
    compat = ecowittcustom      # or gw1000, or none
```

The profile is applied before your own `field_map_extensions`, so anything you set
still wins. To move a series onto the new field later, rename the column with
`weectl database rename-column` and drop the setting.

If you are not sure what is in there, look before you switch:

    python -m user.ecowitt --port 8001 --config /etc/weewx/weewx.conf

Point the console at that port for one upload, and it will tell you:

    12 of these fields already hold readings:

      soilTemp1                     104832 values, last 2026-08-25
      outTemp                       104832 values, last 2026-08-25

    If those came from the same sensor, there is nothing to do. If they came
    from a different one, this driver is about to write a second series into
    the same column, and afterwards the two cannot be told apart.

## Multi-channel sensors

Ecowitt sells the same sensor for several jobs. A WN34 comes as a soil probe, as a
silicone lead for a pool, with a short or a long cable, for indoor or outdoor use. All
of them report on `tf_chN`, and nothing in the upload says which is which. The same goes
for the WH31 on `tempN` and the WN35 on `leafwetness_chN`.

Ecowitt says as much itself: its compatibility table lists the three as one row,
"WN34 S/L/D", with one channel count between them. Nothing in an upload distinguishes
them, and no driver can.

So the catalog has to put them somewhere neutral. `tf_chN` goes to `extraTemp(N+8)`,
which is also where the Ecowitt gateway driver puts it, so a history from there lines
up. That is a convention, not a reading, and the driver says so the first time a
channel turns up:

    INFO user.ecowitt.mapping: New field 'tf_ch3' -> 'extraTemp11'
        (group_temperature). Placement is a convention, not a reading: WN34
        multi-channel temperature. Sold with a spike, with a PVC lead, ...

Only you know where the probe is, so say it:

```ini
[[field_map_extensions]]
    tf_ch1 = soilTemp5      # spike in the bed
    tf_ch2 = extraTemp10    # silicone lead in the pool
    tf_ch3 = extraTemp11    # north wall
```

The channels the catalog covers and the ones this driver derives behave the same way
here. Whatever you write wins.

### Which sensors have how many channels

The catalog carries the figures from Ecowitt's compatibility table, and they do more
than document: a channel past the end of a family is reported rather than derived,
because either the table is out of date or something else is going on.

They are checked rather than trusted. `tools/check_against_ecowitt.py` reads the
sensor families out of Ecowitt's own API documentation and compares them:

    Ecowitt family           model    documented ours
    leaf_ch                  WN35     8          8
    soil_ch                  WH51     16         16
    soil_moisture_ec_ch      WH52     16         16
    temp_and_humidity_ch     WH31     8          8
    temp_ch                  WN34     8          8

That last line is also the plainest answer to where a WN34 belongs. Ecowitt calls its
family `temp_ch`, not soil anything.

| Sensor | Channels | Placement |
|---|---|---|
| WH31 and relatives | 8 | yours |
| WN34 S/L/D | 8 | yours |
| WN35 | 8 | yours |
| WH51 and WH52 | 16, shared between them | soil |
| WH41, WH43 | 4 | yours |
| WH55 | 4 | leaks |
| WH54 / LDS01 | 4 | yours |
| WH45, WH46, WH57, WN38 | 1 | fixed |

The WH51 and the WH52 share one pool of 16, so `soilmoisture3` and `soil_ec_hum3` are
the same channel with a different probe in it. They map to the same field on purpose.

The cloud API documents sixteen channels for each of them separately, which would make
that wrong, so the driver does not simply assume it: if both ever arrive for the same
channel, it says so once and tells you to give one of them a field of its own.

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
