# Reporting a new sensor

Send the raw upload. That is the whole thing.

## Get it

```
python -m user.ecowitt --port 8001
```

Point the console at that port for one upload: **WS View Plus** → *Weather Services*
→ *Customized*, change the port to 8001, save, wait for the interval. Change it back
afterwards.

Copy the line beginning `POST /` and the readings under it.

If that command will not run, take it from the log instead: set `log_raw = True` in
your driver section, restart WeeWX, and copy the line that starts `Raw request:`.

## Replace your PASSKEY

The upload begins with something like:

```
PASSKEY=3178AB6B42A759F51A5A4AD72E37F8DE&stationtype=EasyWeatherPro_V5.2.7&...
```

That value identifies your station to Ecowitt. Replace it with `X` before posting
anything in public. The rest is weather data.

## Send it

<https://github.com/hilman2/weewx-ecowitt/issues/new>

Title it with the sensor, e.g. *WN36 not recognised*. Paste the upload in a fenced
code block.

That is enough for most sensors. The payload already carries `model` and
`stationtype`, so the console and its firmware come with it, and a field name from a
family the driver knows needs nothing further.

## When more is needed

A genuinely new kind of sensor sends names nobody has seen. `bgt=75.3` says nothing
on its own: not the quantity, not the unit. If your sensor is the first of its kind,
add whatever you can:

- what the sensor is, e.g. *WN38, black globe thermometer*
- what the WS View Plus app shows for it at the same moment, e.g. *24.1 °C at 14:05*

That second one settles both the field and its unit, because it ties a number in the
payload to a reading you can see. If it is missing and the name is ambiguous, someone
will ask.

## What happens then

A field that follows a pattern the driver already knows needs no release: a ninth
channel of a family that goes up to eight is worked out from the eight. A sensor
nobody has seen before is added to the catalog and comes with the next version.

## If you cannot wait

Map it yourself. The driver says what it saw:

```
INFO user.ecowitt.mapping: No idea what 'newfield_ch1' is. Left out.
```

Then:

```ini
[Ecowitt]
    [[field_map_extensions]]
        newfield_ch1 = extraTemp7
```

and, if the field is not one your schema already has:

```
weectl database add-column extraTemp7 --type REAL -y
```

Please still open the issue. What works for you works for everybody with that sensor.
