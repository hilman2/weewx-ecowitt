---
name: A sensor is missing
about: A reading your station sends does not reach WeeWX
title: 'MODEL not recognised'
labels: sensor
---

<!--
The raw upload is what is needed. Get it with one command on the machine running
WeeWX, then point the console at that port for one upload:

    python -m user.ecowitt --port 8001

REPLACE YOUR PASSKEY before posting. It is the first value in the upload and
identifies your station to Ecowitt. The rest is weather data.

The payload already carries the console model and its firmware, so nothing else is
needed for a sensor whose field names follow a known pattern.
-->

## What the station sent

```
paste the upload here, PASSKEY replaced
```

## If this is a kind of sensor nobody has seen before

<!-- Only then. A field name like bgt=75.3 says neither the quantity nor the unit. -->

- What the sensor is:
- What the WS View Plus app shows for it at the same moment:
