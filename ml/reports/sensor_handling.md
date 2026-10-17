# T09 — Sensor handling decisions (generated from data_cleaning.py)

Rows: 220320 | Sensor columns kept: 51

## Dropped
- `sensor_15`: 100% missing

## Gap handling (deviates from docs where long gaps were found — see module docstring)

| Sensor | Action | Missing (min) | Longest gap (min) |
|---|---|---:|---:|
| `sensor_50` | flagged_not_imputed | 77017 | 76996 |
| `sensor_51` | flagged_not_imputed | 15383 | 15356 |
| `sensor_00` | flagged_not_imputed | 10208 | 6076 |
| `sensor_07` | flagged_not_imputed | 5451 | 4668 |
| `sensor_06` | flagged_not_imputed | 4798 | 4299 |
| `sensor_08` | flagged_not_imputed | 5107 | 4227 |
| `sensor_09` | flagged_not_imputed | 4595 | 4212 |
| `sensor_30` | flagged_not_imputed | 261 | 239 |
| `sensor_01` | flagged_not_imputed | 369 | 200 |
| `sensor_29` | flagged_not_imputed | 72 | 41 |
| `sensor_32` | flagged_not_imputed | 68 | 35 |
| `sensor_16` | linear_interpolated | 31 | 15 |
| `sensor_17` | linear_interpolated | 46 | 15 |
| `sensor_18` | linear_interpolated | 46 | 15 |
| `sensor_22` | linear_interpolated | 41 | 15 |
| `sensor_25` | linear_interpolated | 36 | 14 |
| `sensor_02` | linear_interpolated | 19 | 8 |
| `sensor_03` | linear_interpolated | 19 | 8 |
| `sensor_04` | linear_interpolated | 19 | 8 |
| `sensor_05` | linear_interpolated | 19 | 8 |
| `sensor_10` | linear_interpolated | 19 | 8 |
| `sensor_11` | linear_interpolated | 19 | 8 |
| `sensor_12` | linear_interpolated | 19 | 8 |
| `sensor_13` | linear_interpolated | 19 | 8 |
| `sensor_14` | linear_interpolated | 21 | 8 |
| `sensor_19` | linear_interpolated | 16 | 8 |
| `sensor_20` | linear_interpolated | 16 | 8 |
| `sensor_21` | linear_interpolated | 16 | 8 |
| `sensor_23` | linear_interpolated | 16 | 8 |
| `sensor_24` | linear_interpolated | 16 | 8 |
| `sensor_26` | linear_interpolated | 20 | 8 |
| `sensor_27` | linear_interpolated | 16 | 8 |
| `sensor_28` | linear_interpolated | 16 | 8 |
| `sensor_31` | linear_interpolated | 16 | 8 |
| `sensor_33` | linear_interpolated | 16 | 8 |
| `sensor_34` | linear_interpolated | 16 | 8 |
| `sensor_35` | linear_interpolated | 16 | 8 |
| `sensor_36` | linear_interpolated | 16 | 8 |
| `sensor_37` | linear_interpolated | 16 | 8 |
| `sensor_38` | linear_interpolated | 27 | 8 |
| `sensor_39` | linear_interpolated | 27 | 8 |
| `sensor_40` | linear_interpolated | 27 | 8 |
| `sensor_41` | linear_interpolated | 27 | 8 |
| `sensor_42` | linear_interpolated | 27 | 8 |
| `sensor_43` | linear_interpolated | 27 | 8 |
| `sensor_44` | linear_interpolated | 27 | 8 |
| `sensor_45` | linear_interpolated | 27 | 8 |
| `sensor_46` | linear_interpolated | 27 | 8 |
| `sensor_47` | linear_interpolated | 27 | 8 |
| `sensor_48` | linear_interpolated | 27 | 8 |
| `sensor_49` | linear_interpolated | 27 | 8 |

Short-gap interpolation threshold: 30 min. Sensors whose longest gap exceeds this get a `_was_missing` indicator column instead of a filled value.

Missingness indicator columns added: ['sensor_00_was_missing', 'sensor_01_was_missing', 'sensor_06_was_missing', 'sensor_07_was_missing', 'sensor_08_was_missing', 'sensor_09_was_missing', 'sensor_29_was_missing', 'sensor_30_was_missing', 'sensor_32_was_missing', 'sensor_50_was_missing', 'sensor_51_was_missing']