# weewx-ecowitt

A WeeWX driver for Ecowitt hardware that uploads to a custom server.

## Getting going

- **[Installation](Installation)** — install, point the hardware at it, start
- **[Configuration](Configuration)** — every option, with worked examples
- **[Diagnostics](Diagnostics)** — one command that answers most questions

## How readings are placed

- **[Field map](Field-map)** — from raw field to database column
- **[Sensors](Sensors)** — every field this driver knows, by sensor
- **[Unknown fields](Unknown-fields)** — what happens to a field the catalog misses
- **[Database columns](Database-columns)** — which columns a station needs, and how to add them

## When something is missing

- **[Reporting a new sensor](New-sensors)** — exactly what to send
- **[Troubleshooting](Troubleshooting)** — symptoms and what they mean

## Other

- **[Keeping strangers out](Security)** — path, token, addresses, TLS
- **[Development](Development)** — layout, tests, rebuilding the catalog

## What it supports

Anything that offers **Customized** upload in WS View Plus, which is most of the
current range: GW1000, GW1100, GW1200, GW2000, GW3000, HP2551, HP2561, WS3800,
WS3900, WS3910, WN1980 and their relatives.

Both the Ecowitt protocol and the Weather Underground protocol are read. Ecowitt
carries far more fields, so use that unless something forces otherwise.

532 raw fields are mapped, covering the WH31, WN34, WN35, WH40, WH41, WH43, WH45,
WH46, WH51, WH52, WH55, WH57, WH65, WH68, WN20, WN38, WS68, WS80, WS85, WS90 and
LDS01, along with everything the consoles and gateways report about themselves.

## In one paragraph

The console posts its readings. The driver turns each raw field name into a WeeWX
field using a catalog, writes the packet, and tells WeeWX what unit each new field
is in. Fields the catalog does not cover are examined rather than dropped: one that
continues a known series is worked out, one that is merely recognisable by name is
reported. Fields whose placement the hardware does not settle, such as a WN34 that
might be in a bed or in a pool, wait until you say where they go.
