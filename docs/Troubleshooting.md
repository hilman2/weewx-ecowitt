# Troubleshooting

## Nothing arrives at all

The log should show this at startup:

```
INFO weewx.listener: Listening for HTTP requests on *:8000
```

If it does not, the driver is not running. Check `station_type = Ecowitt` and that
the `[Ecowitt]` section has `driver = user.ecowitt.driver`.

If it does, watch the port:

```
sudo tcpdump -i any -n port 8000
```

Nothing there means the problem is between console and machine:

- Address or port wrong in WS View Plus. Check the page again after leaving it; the
  app sometimes reports a save that did not happen.
- Protocol set to *Wunderground* instead of *Ecowitt*.
- A firewall. `sudo ufw allow 8000/tcp` where ufw is in use.
- The console on a different network segment from WeeWX.

## Address already in use

```
ERROR weewx.listener: Cannot listen on 0.0.0.0:8000: [Errno 98] Address already in use
```

Something else holds the port:

```
ss -tlnp | grep 8000
```

Either stop it, or give the driver another port and change the console to match. A
second WeeWX instance with the same port is a common cause.

## Requests arrive but nothing is stored

Check the response first. The console treats an upload as failed until it has read
one, and stops trying after enough failures.

```
curl -s -o /dev/null -w '%{http_code}\n' -X POST -d 'tempf=59.7' http://localhost:8000/
```

| Code | Meaning |
|---|---|
| 200 | Fine. |
| 404 | `path` is set and does not match what the console sends. |
| 403 | `token` or `allowed_hosts` rejected it. |
| 413 | The upload is larger than `max_body`. |

## A sensor is missing from reports

In order:

**1. Does it arrive?**

```
python -m user.ecowitt --port 8001
```

Not listed means the console is not sending it. Check that the sensor is registered
in WS View Plus and shows a reading there.

**2. Is it waiting for a decision?**

```
WARNING user.ecowitt.mapping: 'tf_ch1' is not being written, because drivers
disagree about where it goes.
```

Name it in `field_map_extensions`. See [Field map](Field-map).

**3. Was it unknown?**

```
INFO user.ecowitt.mapping: No idea what 'newfield_ch1' is. Left out.
```

See [Reporting a new sensor](New-sensors).

**4. Does it have a column?**

A field without a column appears as a current value and is gone at the next archive
record. See [Database columns](Database-columns).

**5. Does the skin show that field?**

Most skins list which fields they display. A field the skin does not name will not
appear however well it is stored.

## Rain stays empty

Ecowitt hardware sends rain as running counters: `dailyrainin`, `hourlyrainin`,
`eventrainin`. It never sends the amount that fell since the last upload, which is
what WeeWX calls `rain` and what every rain total is built from.

`StdDelta` turns one into the other. The installer sets it up, so a fresh install
needs nothing. Versions up to 0.3.0 did not, and there `rain` is empty in every
packet and the daily total never moves. Reinstall the extension, or add this by hand:

```ini
[StdWXCalculate]
    [[Delta]]
        [[[rain]]]
            input = dayRain
```

The counter resets at midnight. WeeWX notices and logs `'rain' counter reset
detected`, then skips that one interval rather than recording a day's worth of rain
in it.

## Readings look wrong by a factor

Almost always a unit. The Ecowitt protocol carries US units: °F, inHg, inches, mph.
The driver reports the packet as US and WeeWX converts for display.

A field the driver had to guess may have been given the wrong group. `infer_unknown =
all` accepts guesses, and this is the risk it carries. Map the field explicitly
instead, and report it so the catalog gets it right.

## Two sensors in one column

```
WARNING user.ecowitt.mapping: Both 'soilmoisture3' and 'soil_ec_hum3' arrived, and
they map to the same field. One will overwrite the other.
```

A WH51 and a WH52 on the same channel number. Give one of them a field of its own:

```ini
[[field_map_extensions]]
    soil_ec_hum3 = soilMoist11
```

The readings already mixed cannot be separated afterwards.

## Gaps in the data

Check the upload interval in WS View Plus against the archive interval in WeeWX. An
archive record is written from whatever arrived during the interval; if nothing did,
the record is empty.

```
WARNING weewx.listener: Queue full. Dropped the oldest request (3 so far).
```

means uploads arrived faster than they were processed. Raise `queue_size`, or lower
the upload frequency. At an eight second interval this can happen while reports are
being generated on a slow machine.

## The driver stops after a while

Look for what came before it in the log. Two known shapes:

- The console changed address, e.g. after a DHCP lease expired, and `allowed_hosts`
  no longer matches.
- The machine slept. A listener does not survive suspend on every platform; restart
  WeeWX.

## Reporting a problem

Include:

- What the log says, with a few lines before it
- The output of `python -m user.ecowitt --port 8001`, with the `PASSKEY` replaced
- Console model and firmware, from *About* in WS View Plus
- WeeWX version, from `weectl --version`

<https://github.com/hilman2/weewx-ecowitt/issues>
