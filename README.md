# UE BOOM for Home Assistant

Power and battery for **Ultimate Ears BOOM / MEGABOOM** speakers over Bluetooth LE.

| Entity | What |
|---|---|
| `switch.<name>_power` | Wake the speaker / put it in standby |
| `sensor.<name>_battery` | Battery % |
| `binary_sensor.<name>_audio_connected` | On while the speaker has an audio (A2DP) connection to some host |

State comes passively from the speaker's advertisements, so the speaker isn't polled and its battery isn't drained.
When you switch it on, the speaker connects its audio to the Bluetooth adapter that HA used. Pair it with that host first.
If the speaker is already on but has lost its audio connection, **turn on** asks the host's BlueZ to reconnect it.

Built on [pyueboom](https://github.com/milliamp/pyueboom). Tested with a BOOM 3 (firmware 1.1.0.24) on a local
BlueZ adapter. ESPHome Bluetooth proxies should work too, through `bleak`, but haven't been tested.

## Install

1. HACS → ⋮ → **Custom repositories** → `https://github.com/milliamp/ha-ueboom`, type **Integration**.
2. Install **UE BOOM**, then restart Home Assistant.
3. The speaker is discovered automatically (Settings → Devices & services). You can also add it with **Add integration → UE BOOM**.

## Requirements

- The speaker must be **paired** with the HA host's Bluetooth adapter (`bluetoothctl pair/trust <MAC>`) for its audio
  to connect there. Power control alone doesn't need pairing.
- With a local adapter, HA needs to be able to open raw Bluetooth sockets. Docker installs with `network_mode: host`
  can, and so can HA OS. For why, see the pyueboom README.

## Not affiliated

Not affiliated with Logitech / Ultimate Ears. The protocol was reverse engineered by the community; see pyueboom for credits.
