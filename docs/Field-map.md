# Field map

How a reading gets from the console to a column.

```
console  ──►  raw field   ──►  WeeWX field  ──►  database column
              tf_ch1           extraTemp9        extraTemp9
```

Three things decide the middle step, in this order.

## 1. Your own mapping

`field_map_extensions` wins over everything. Whatever you write there is where the
reading goes.

```ini
[Ecowitt]
    [[field_map_extensions]]
        tf_ch1 = soilTemp5
        soilmoisture1 = soilMoist1
```

The left side is the raw name as the console sends it. The right side is any WeeWX
field name. Nothing checks whether the field makes sense, which is deliberate: you
know where your sensors are.

## 2. The catalog

532 raw fields with a place to go. See [Sensors](Sensors) for the full list, or ask
the driver:

```
python -c "import sys; sys.path.insert(0, '/etc/weewx/bin/user'); \
from ecowitt import catalog; print(catalog.FIELDS['tf_ch1'])"
```

## 3. Inference

A field in neither of the above is examined rather than dropped. See
[Unknown fields](Unknown-fields).

## Fields that wait for you

Some readings have no natural home. Putting them in the wrong one cannot be undone:
two sensors in one column can never be told apart again. Those fields are not written
until you name them.

There are two kinds.

**Multi-channel sensors.** A WN34 reports on `tf_ch1` whether it is a spike in a bed,
a silicone lead in a pool or a probe on a north wall. Ecowitt lists the three as one
row, `WN34 S/L/D`, and nothing in an upload distinguishes them.

**Fields other drivers place elsewhere.** Where two placements are both defensible,
neither is assumed.

The log names both candidates, once per field:

```
WARNING user.ecowitt.mapping: 'tf_ch1' is not being written, because drivers
disagree about where it goes. The wrong choice mixes two sensors into one column,
and afterwards they cannot be separated. Add one of these under
[[field_map_extensions]]: 'tf_ch1 = extraTemp9' for this driver's placement, or
'tf_ch1 = soilTemp1' if your history came from ecowittcustom.
```

`python -m user.ecowitt` prints the whole block ready to paste.

On a station with two WN34 probes, a WH52 and a lightning sensor, six fields wait and
twenty-nine arrive without a word. An outdoor temperature is an outdoor temperature
whatever wrote it last, so nothing is asked about that.

## Where the default placements are

| Sensor | Raw | Goes to |
|---|---|---|
| WH31 and relatives | `temp1f`, `humidity1` | `extraTemp1..8`, `extraHumid1..8` |
| WN34 S/L/D | `tf_ch1..8` | `extraTemp9..16` (waits) |
| WN35 | `leafwetness_ch1..8` | `leafWet1..8` |
| WH51 | `soilmoisture1..16` | `soilMoist1..16` |
| WH52 | `soil_ec_hum1..16` | `soilMoist1..16` |
| WH52 temperature | `soil_ec_temp1..16` | `soilTemp1..16` (waits) |
| WH52 conductivity | `soil_ec1..16` | `soilEC1..16` |
| WH41, WH43 | `pm25_ch1..4` | `pm25_1..4` |
| WH55 | `leak_ch1..4` | `leak_1..4` |
| WH57 | `lightning`, `lightning_num` | `lightning_distance`, `lightning_num` |
| WH54 / LDS01 | `air_ch1..4`, `depth_ch1..4` | same names |

The WH51 and the WH52 share one pool of 16 channels, so `soilmoisture3` and
`soil_ec_hum3` are the same channel with a different probe in it. If both ever arrive
for the same number, the driver says so once:

```
WARNING user.ecowitt.mapping: Both 'soilmoisture3' and 'soil_ec_hum3' arrived, and
they map to the same field. One will overwrite the other. Give one of them a field
of its own in field_map_extensions.
```

## Units

A field's unit group comes with its place in the catalog, and the driver registers it
with WeeWX at startup. Fields WeeWX already knows keep their own group; nothing here
overrides those.

Readings arrive in US units, because that is what the Ecowitt protocol carries: °F,
inHg, inches, mph. WeeWX converts for display according to your report settings. The
database stores whatever unit system the driver reports, which for this driver is US.

## Checking a mapping

```
python -m user.ecowitt --port 8001
```

Prints every reading with the field it went to. See [Diagnostics](Diagnostics).
