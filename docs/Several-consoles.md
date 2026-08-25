# Several consoles

A second gateway is the usual way to reach sensors the first one cannot hear. Both
send to the same driver, and both number their channels from one, so a WN34 on
channel 1 of each would land in the same field. Whichever uploaded last would win,
and afterwards the two readings could not be separated.

Name them, and each gets its own mapping:

```ini
[Ecowitt]
    driver = user.ecowitt.driver
    port = 8000

    [[stations]]

        [[[garden]]]
            passkey = 3178AB6B42A759F51A5A4AD72E37F8DE
            [[[[field_map_extensions]]]]
                tf_ch1 = soilTemp1          # spike in the raised bed
                soil_ec_temp1 = soilTemp2

        [[[roof]]]
            passkey = 9A2B4C6D8E0F1A3B5C7D9E1F2A4B6C8D
            [[[[field_map_extensions]]]]
                tf_ch1 = extraTemp12        # the same channel, a different sensor
```

One port, one listener. The consoles are told apart by the `PASSKEY` they send first
in every upload, which is derived from their hardware address and does not change.

## If you have not configured them yet

The driver notices on its own. It keeps track of which console wrote which field, and
the moment a second one writes a field the first already owns, it says so and drops
the newcomer's value rather than writing it over the other:

```
WARNING user.ecowitt.driver: Two consoles are sending here, and both write
'extraTemp9'. The readings from 'BBBBBBBB' are being dropped, because mixing two
sensors into one column cannot be undone afterwards. Give each console its own field
map under [[stations]], one entry per PASSKEY.
```

Only the field that clashes is dropped. Everything else from that console arrives as
usual, so a second gateway carrying sensors the first one does not is not held up at
all:

```
Gateway A : {'extraTemp9': 66.0, 'outTemp': 59.7}
Gateway B : {'soilMoist1': 30.0}
```

Gateway B's `tf_ch1` is gone, because A already owns that field. Its soil sensor,
which A does not have, comes through.

Which console keeps a field is decided by which one sent it first after the driver
started. That is arbitrary, but it is stable: the series that is already running
keeps running. Naming both consoles under `[[stations]]` removes the restriction, and
then each writes wherever you send it.

## Finding a PASSKEY

It is the first value in the upload:

```
PASSKEY=3178AB6B42A759F51A5A4AD72E37F8DE&stationtype=EasyWeatherPro_V5.2.7&...
```

Point the console at the diagnostic command for one upload and read it from there:

```
python -m user.ecowitt --port 8001
```

Or turn on `log_raw` and take it from the log. Keep it out of anything public: it is
what Ecowitt's servers use to recognise your station.

## What changes

Every packet carries `station` with the name you gave, so a report can tell them
apart. `infer_unknown` can be set per console as well as for the whole driver.

An upload whose PASSKEY is in no `[[stations]]` entry is ignored, and the driver says
so once:

```
WARNING user.ecowitt.driver: An upload from 192.168.1.51 carries PASSKEY 'CCCC',
which is not one of the consoles configured under [[stations]]. Ignoring it. Add it
there to keep its readings.
```

That is deliberate. A station this driver does not know is more likely a neighbour, a
scanner, or a console you forgot about than something whose readings belong in your
database.

## When not to use this

**One console.** Leave `[[stations]]` out entirely and use `field_map_extensions` at
the top level, as before. Nothing changes.

**Two separate installations.** If the consoles measure different places and their
readings should not share a database, run two WeeWX instances instead. See the WeeWX
wiki article *Run multiple instances of WeeWX on one computer*.

**Different hardware.** An Ecowitt and a Davis in one WeeWX is what
[MetaDriver](https://github.com/tkeffer/weewx-metadriver) is for. It runs several
drivers side by side. This section is for several consoles of the same kind, which
MetaDriver cannot do: a driver's `loader()` reads its own configuration section by a
fixed name, so the same driver cannot be loaded twice.
