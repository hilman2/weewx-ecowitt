# Keeping strangers out

The driver opens a port that accepts weather readings. Anyone who can reach it can
post readings, and the console has no way to prove it is the console. Ecowitt
hardware sends a `PASSKEY`, but that is a fixed value visible in every upload, so it
is an identifier rather than a secret.

Four settings narrow the exposure. Use as many as fit.

## Bind to one address

```ini
[Ecowitt]
    address = 192.168.1.10
```

Only that interface accepts anything. Behind a reverse proxy, `localhost` means the
port cannot be reached from the network at all:

```ini
    address = localhost
    trust_proxy = true
```

`trust_proxy` makes the driver take the client address from `X-Forwarded-For`, which
is right only when a proxy you control sets that header. Without a proxy, leave it
off: anyone can send that header themselves.

## A path nobody can guess

```ini
    path = /a8f3c1e0-4b2d/report
```

Anything else gets a 404. Most consoles can be given a path but not a header or a
query parameter, which makes this the practical secret for hardware.

Generate one:

```
python -c "import secrets; print('/%s/report' % secrets.token_hex(8))"
```

## A token

For anything that can send a header or a query parameter:

```ini
    token = 4f8a2c1e9b7d3a5f
```

Accepted as query parameter `token`, header `X-Auth-Token`, or a bearer token in
`Authorization`. Compared in constant time. Anything else gets a 403.

## Only from known addresses

```ini
    allowed_hosts = 192.168.1.42, 192.168.1.43
```

Anything else gets a 403. Behind a proxy this sees the proxy unless `trust_proxy` is
set, so set both together or neither.

## What none of this does

**Encryption.** The Ecowitt protocol is plain HTTP, and consoles do not offer TLS. On
a local network that is usually acceptable. Across the internet, put a reverse proxy
with a certificate in front and let it terminate TLS. The path and the readings are
then encrypted between the console and the proxy, and the proxy talks to the driver
on localhost.

**Authentication of the sensor.** Nothing stops somebody who knows your path from
posting a plausible temperature. The defence is that they have to know it.

## A limit worth keeping

```ini
    max_body = 65536
```

The default. An upload is a few hundred bytes, so anything near this is not a weather
station. Requests above it get a 413 without being read into memory.

## After changing any of it

Restart WeeWX and change the console to match. A console pointed at the old path will
be answered with a 404 and its readings dropped, silently as far as it is concerned.
The log says so:

```
WARNING weewx.listener: Rejected a request from 192.168.1.42: bad or missing token
```
