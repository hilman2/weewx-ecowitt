---
name: A sensor is missing
about: A reading your station sends does not reach WeeWX
title: 'MODEL not recognised'
labels: sensor
---

<!--
Everything below comes from one command, run on the machine that runs WeeWX:

    python -m user.ecowitt --port 8001

Then point the console at port 8001 for one upload (WS View Plus, Weather Services,
Customized), and change it back afterwards.

REPLACE YOUR PASSKEY. It is the first value in the upload and identifies your station
to Ecowitt. Everything else in the payload is weather data.
-->

## The sensor

| | |
|---|---|
| Model | e.g. WN34S |
| Channel | e.g. 3 |
| Where it sits | e.g. 30 cm deep in a raised bed |
| What the app shows | e.g. 18.7 °C at 14:05 |

## The station

| | |
|---|---|
| Console or gateway | e.g. HP2561AE Pro |
| Firmware | e.g. V2.1.4 |
| WeeWX version | `weectl --version` |
| Driver version | from the log at startup |

## What the station sent

```
paste the whole output of python -m user.ecowitt here, PASSKEY replaced
```
