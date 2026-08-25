# Installation

## Requirements

- WeeWX 5.0 or later
- Python 3.7 or later
- Ecowitt hardware that offers **Customized** upload: GW1000, GW1100, GW1200,
  GW2000, GW3000, HP2551, HP2561, WS3800, WS3900, WS3910, WN1980 and their relatives

Nothing else. No pip packages, no compiler.

## Install

```
weectl extension install https://github.com/hilman2/weewx-ecowitt/releases/latest/download/weewx-ecowitt.zip
weectl station reconfigure
```

`reconfigure` offers `Ecowitt` in the list of station types. Picking it writes an
`[Ecowitt]` section with starting values.

To install from a clone instead:

```
git clone https://github.com/hilman2/weewx-ecowitt.git
weectl extension install weewx-ecowitt
```

## Point the hardware at it

In **WS View Plus**: *Weather Services*, page through to *Customized*.

| Field | Value |
|---|---|
| Protocol Type | Ecowitt |
| Server IP / Hostname | the machine running WeeWX |
| Path | `/` unless you set `path` |
| Port | 8000 unless you changed it |
| Upload Interval | 60 |

Save. The console uploads on its own schedule from then on.

## Check before starting WeeWX

```
python -m user.ecowitt --port 8001
```

Point the console at port 8001 for one upload, then change it back. The command
prints what arrived, what it could not place, which database columns are missing, and
which of those already hold readings. Running it changes nothing.

## Start

```
sudo systemctl restart weewx
sudo journalctl -u weewx -f
```

Within one upload interval the log shows:

```
INFO user.ecowitt.driver: Driver version is 0.1.0, listening with user.listener, the bundled copy
INFO weewx.listener: Listening for HTTP requests on *:8000
INFO weewx.engine: Starting main packet loop.
```

Followed, on the first upload, by any fields waiting for a decision. See
[Field map](Field-map).

## Upgrade

```
weectl extension install https://github.com/hilman2/weewx-ecowitt/releases/latest/download/weewx-ecowitt.zip
sudo systemctl restart weewx
```

Your `[Ecowitt]` section is left alone. Read the
[changelog](https://github.com/hilman2/weewx-ecowitt/blob/main/CHANGELOG.md) first if
you skipped versions: a field that moves is listed there.

## Uninstall

```
weectl extension uninstall ecowitt
weectl station reconfigure
```

Pick another station type when asked. The database keeps everything it collected.
