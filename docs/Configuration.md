# Configuration

Everything lives in one section of `weewx.conf`.

## A complete example

```ini
[Station]
    station_type = Ecowitt

[Ecowitt]
    driver = user.ecowitt.driver

    # Where to listen.
    address = 0.0.0.0
    port = 8000

    # Accept this path only. Anything else gets a 404.
    path = /a8f3c1e0/report

    # What to do with a field the driver does not know yet.
    infer_unknown = series

    # How the station is named in reports.
    model = HP2561AE Pro

    [[field_map_extensions]]
        # Fields the driver will not place on its own.
        tf_ch1 = soilTemp5          # WN34S, spike in the raised bed
        tf_ch2 = extraTemp10        # WN34L, silicone lead in the pool
        tf_batt1 = wn34_ch1_batt
        tf_batt2 = wn34_ch2_batt
        soil_ec_temp1 = soilTemp1   # WH52, 10 cm deep
        lightning_time = lightning_time
```

## Options

### The listener

These are passed straight to `weewx.listener`. They behave the same for every driver
that uses it.

| Option | Default | Meaning |
|---|---|---|
| `port` | 80 | Port to listen on. Below 1024 needs root. |
| `address` | every interface | Address to bind to. Use `localhost` behind a reverse proxy. |
| `path` | every path | Accept this path only. Anything else gets a 404. |
| `token` | none | Require this token, as query parameter `token`, header `X-Auth-Token`, or a bearer token in `Authorization`. |
| `allowed_hosts` | anywhere | Comma-separated addresses to accept from. |
| `trust_proxy` | False | Take the client address from `X-Forwarded-For`. Only with a proxy you control. |
| `max_body` | 65536 | Largest upload accepted, in bytes. Bigger gets a 413. |
| `socket_timeout` | 20 | How long an idle client may hold a connection, in seconds. |
| `queue_size` | 10 | How many uploads may wait to be processed. Beyond that the oldest is dropped, with a warning. |
| `log_raw` | False | Log every upload at debug level. Turn this on when a sensor is missing. |

### The driver

| Option | Default | Meaning |
|---|---|---|
| `driver` | | `user.ecowitt.driver` |
| `model` | Ecowitt | What reports call the station. |
| `infer_unknown` | `series` | What happens to fields the catalog does not cover. See [Unknown fields](Unknown-fields). |
| `field_map_extensions` | empty | Raw field to WeeWX field. Wins over everything else. See [Field map](Field-map). |

## Common setups

### On its own, in a local network

The console posts straight to WeeWX. Simplest, and fine where nothing else can reach
the port.

```ini
[Ecowitt]
    driver = user.ecowitt.driver
    port = 8000
```

Console: server is the WeeWX machine's address, port 8000, path `/`.

### Behind a reverse proxy, reachable from outside

The web server keeps 443 and passes one path through. A path nobody can guess is the
only secret most consoles can carry.

```ini
[Ecowitt]
    driver = user.ecowitt.driver
    address = localhost
    port = 8000
    path = /a8f3c1e0/report
    trust_proxy = true
```

nginx:

```nginx
location /a8f3c1e0/report {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Caddy:

```
weather.example.com {
    handle /a8f3c1e0/* {
        reverse_proxy 127.0.0.1:8000
    }
}
```

Console: server is `weather.example.com`, port 443, path `/a8f3c1e0/report`.

### Alongside a web server on the same machine

Nothing special is needed as long as the ports differ. WeeWX writes its reports to
files; the web server serves them; the driver listens on its own port.

### Two stations, one machine

WeeWX runs one driver per instance, so two stations means two instances, each with
its own configuration file, database and port. See the WeeWX wiki article *Run
multiple instances of WeeWX on one computer*.

## Configuring the console

In **WS View Plus**: *Weather Services*, then page through to *Customized*.

| Field | Value |
|---|---|
| Protocol Type | **Ecowitt** |
| Server IP / Hostname | the machine running WeeWX |
| Path | what you set as `path`, or `/` |
| Port | what you set as `port` |
| Upload Interval | 60 seconds is plenty; 16 is the minimum |

The Weather Underground protocol is also read, but it carries fewer fields. Nothing
outside the WU field list reaches WeeWX that way, which on a current station means
most of the sensors. Use Ecowitt unless something forces otherwise.

## Checking it works

```
python -m user.ecowitt --port 8001
```

Point the console at 8001 for one upload. See [Diagnostics](Diagnostics).
