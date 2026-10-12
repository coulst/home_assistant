# Coul Street EVSE - Home Assistant integration

A custom integration for the EVSE's Modbus TCP server, as an easier alternative to hand-
writing the `modbus:` YAML in [examples/home_assistant.yaml](../home_assistant.yaml). Instead
of copy-pasting register addresses, you add the charger from Settings > Devices & Services >
Add Integration, enter its IP, and it creates one Device with all the sensors, switches, the
current-limit number, and a clear-limit button already wired up.

Register addresses, scaling, and enum mappings mirror
`components/evse/src/modbus_regs.h`, which is the source of truth - if that file's
`MODBUS_MAP_VERSION` changes, this integration needs revisiting (it checks the version on
setup and logs a warning if it doesn't match).

## Installing

1. Enable Modbus TCP on the charger under Settings in its web UI (it ships disabled).
2. Copy `custom_components/coulst_evse` into your Home Assistant `config/custom_components/`
   directory (or symlink it, if you're developing against this repo).
3. Restart Home Assistant.
4. Settings > Devices & Services > Add Integration > "Coul Street EVSE", then enter the
   charger's host/IP and Modbus unit ID (1, unless you changed it).

## What you get

- One Device per charger, with sensors for every input register in the map (state, live
  measurements, energy, temperatures, current limits), decoded into the same enum strings as
  the YAML example.
- A `switch` for charging permitted (register 1) that reads back the holding register rather
  than inferring state from telemetry.
- A `number` slider for the load-management current limit (register 0), ranged to
  `[MIN_LIMIT_AMPS, max_circuit_current]` to match what the firmware will actually accept.
- A `button` to clear the current limit (write 0), separate from the slider since 0 is a
  special "hand arbitration back to the charger" value, not just the slider's floor.
- An automatic Modbus heartbeat on every poll, so a non-zero failsafe timeout configured on
  the charger doesn't need a separate automation (unlike the YAML example, which needs one).

## Status / what's not done yet

This is a starting point, not a finished integration:

- No zeroconf auto-discovery, and it can't be added without a firmware change: the charger
  only calls `mdns_hostname_set()` (`CoulSt_<last 3 MAC bytes>` -> `coulst_xxxxxx.local`), not
  `mdns_service_add()`, so there's no `_http._tcp.local.` or custom service type to browse and
  no TXT records - HA's zeroconf integration discovers via service browsing, which this
  device doesn't support. A plain hostname (`coulst_xxxxxx.local`) still works fine as the
  manual host entry in the config flow above.
- No options flow for changing the scan interval or unit ID after setup.
- Multiple chargers already work out of the box (one config entry per charger, one Device
  each) - this is the main advantage over the YAML example, which needs manual suffixing for
  more than one.
- Not yet packaged for HACS or submitted to HA core.
