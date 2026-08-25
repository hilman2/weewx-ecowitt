# Diagnostics

## When a sensor is missing

The driver writes out what it could not place, by itself:

```
cat /var/tmp/weewx-ecowitt-report.txt
```

That file appears the first time a station sends something the driver cannot handle.
It holds the raw upload with the PASSKEY replaced, and what the driver made of it.
See [Reporting a new sensor](New-sensors).

## Everything else

One command answers the rest:

```
python -m user.ecowitt --port 8001
```

It listens for one upload, prints what it made of it, and changes nothing. WeeWX can
keep running, as long as the port differs.

Point the console at that port for one interval: **WS View Plus** → *Weather
Services* → *Customized*, change the port, save. Change it back afterwards.

## Options

| Option | Default | Meaning |
|---|---|---|
| `--port` | 8000 | Port to listen on. |
| `--address` | every interface | Address to bind to. |
| `--path` | every path | Accept this path only. |
| `--samples` | 1 | How many uploads to wait for. |
| `--timeout` | 300 | Seconds before giving up. |
| `--config` | `/etc/weewx/weewx.conf` | Used for the database check and the printed commands. |
| `--infer-unknown` | `all` | Here everything gets a proposal, so nothing is hidden. |
| `--no-database` | | Skip the database check. |

## What it prints

**The upload, and every reading with the field it went to.**

```
POST / from 192.168.1.42, 762 bytes

37 readings
  UV                         2.0
  barometer                  29.92
  extraTemp9                 66.2
  lightning_distance         1.0
  soilMoist1                 30.0
  ...
```

**Anything the catalog did not cover**, with how it was worked out:

```
2 fields were not in the catalog
  last24hrainin  -> ecowitt_last24hrainin  group_rain  guessed: name matches rain.*in$
  yearlyrainin   -> ecowitt_yearlyrainin   group_rain  guessed: name matches rain.*in$
```

**The columns that are missing**, as commands to run:

```
20 readings have nowhere to live. To keep them:

  weectl database add-column soilTemp2 --type REAL --config=/etc/weewx/weewx.conf -y
  ...
```

**Fields waiting for a decision**, as a block to paste:

```
6 fields are not being written, because where they go is your call and
not the hardware's. Paste this into your driver section and uncomment the
line you want:

    [[field_map_extensions]]
        # tf_ch1
        #tf_ch1 = extraTemp9        # this driver
        #tf_ch1 = soilTemp1         # ecowittcustom
```

**Which of those columns already hold readings:**

```
12 of these fields already hold readings:

  soilTemp1                     104832 values, last 2026-08-25
```

## Raw uploads in the log

For a continuous view, or when the console cannot be pointed elsewhere:

```ini
[Ecowitt]
    log_raw = true
```

Restart WeeWX. Every upload appears at debug level:

```
DEBUG weewx.listener: Raw request: PASSKEY=...&tempinf=75.4&humidityin=51&...
```

Debug logging has to be on for it to be visible:

```ini
debug = 1
```

Turn both off afterwards. At an eight second interval this fills a log quickly.

## Is anything arriving at all

```
sudo tcpdump -i any -n port 8000
```

Nothing there means the problem is between the console and the machine: wrong
address, wrong port, a firewall, or the console not saving the setting. WS View Plus
sometimes reports a save that did not happen; check the page again after leaving it.

## Is the port open

```
ss -tlnp | grep 8000
```

Should show `weewxd`. If it shows something else, the driver never got the port and
the log says so:

```
ERROR weewx.listener: Cannot listen on 0.0.0.0:8000: [Errno 98] Address already in use
```
