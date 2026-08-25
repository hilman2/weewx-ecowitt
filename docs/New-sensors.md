# Reporting a new sensor

Ecowitt adds sensors faster than any driver keeps up. When one of yours is missing
from the reports, the driver needs three things to learn it, and all three are in the
output of one command.

## What to send

Run this on the machine that runs WeeWX, on a port WeeWX is not using:

```
python -m user.ecowitt --port 8001
```

Then point the console at that port for one upload: **WS View Plus** → *Weather
Services* → *Customized*, change the port to 8001, save, and wait for the upload
interval. Change it back afterwards.

Copy everything the command printed. It contains:

1. **The raw upload.** The line beginning `POST / from ...`, followed by the readings.
   This is the part that matters most: it is what your console actually sends, which
   no documentation reliably says.
2. **What the driver made of it**, including anything it could not place.
3. **Which columns your database already has.**

If the command will not run, take the raw upload from the log instead. Set
`log_raw = True` in your driver section, restart WeeWX, and take the line that starts
`Raw request:` from the log.

## Remove your PASSKEY first

The upload begins with something like:

```
PASSKEY=3178AB6B42A759F51A5A4AD72E37F8DE&stationtype=EasyWeatherPro_V5.2.7&...
```

That value identifies your station to Ecowitt's servers. Replace it with `X` before
posting anything in public. Everything else in the payload is weather data.

## What else to write down

The upload alone does not say what the fields mean. Add:

| | Example |
|---|---|
| Console or gateway, with firmware | `HP2561AE Pro, V2.1.4` |
| The sensor, exact model | `WN34S, the one with the spike` |
| Which channel it is on | `channel 3` |
| Where it physically sits | `30 cm deep in a raised bed` |
| What the app shows for it | `18.7 °C at 14:05` |

The last row is worth the trouble. It ties a number in the payload to a reading you
can see, which is how a field gets identified beyond doubt. A `tf_ch3=65.7` means
nothing on its own; `tf_ch3=65.7` next to *18.7 °C in the app* settles both the field
and its unit.

## Where to send it

Open an issue: <https://github.com/hilman2/weewx-ecowitt/issues/new>

Title it with the sensor model, e.g. *WN36 not recognised*. Paste the output in a
fenced code block so the formatting survives.

## What happens then

A new field usually needs three things, and the issue gives all of them:

- an entry in the catalog, mapping the raw name to a WeeWX field
- a unit group, so reports can format it
- the channel count for its family, if the sensor is new to the driver

Fields that follow a pattern the driver already knows are handled without a release:
a ninth channel of a family that goes up to eight is derived from the eight. What
needs a release is a sensor nobody has seen before.

## If you cannot wait

Nothing stops you from mapping it yourself. The driver will tell you what it saw:

```
INFO user.ecowitt.mapping: No idea what 'newfield_ch1' is. Left out.
```

or, if the name is recognisable:

```
INFO user.ecowitt.mapping: New field 'newtemp_ch1' -> 'ecowitt_newtemp_ch1'
(group_temperature), name matches ^(temp|tf_|soiltemp|thermo)|temp.*f$
```

Either way you can place it yourself:

```ini
[Ecowitt]
    [[field_map_extensions]]
        newfield_ch1 = extraTemp7
```

Then add the column, if the field is not one your schema already has:

```
weectl database add-column extraTemp7 --type REAL -y
```

Please still open the issue. What works for you works for everybody with that sensor,
and the next person should not have to work it out again.
