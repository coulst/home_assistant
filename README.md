# Coul Street EVSE - Home Assistant integration

A custom integration for the EVSE's Modbus TCP server. Chargers
with Modbus TCP enabled show up under Settings > Devices & Services > Discovered.
Confirming the discovery (or
adding one manually) creates one Device with all the sensors, switches, the
current-limit number, and a clear-limit button wired up.


## Installing

1. Enable Modbus TCP on the charger under Settings in its web UI (it ships disabled). This
   is also what makes the firmware advertise the `_modbus._tcp` mDNS service that HA
   discovers it by (`WifiManager::advertiseModbusService()` in
   `components/network/src/wifi_manager.cpp`, called from `ModbusTcpServer::startSlave()` /
   `stopSlave()` in `components/evse/src/modbus_tcp.cpp`) - it disappears again if you turn
   Modbus TCP back off.
2. Copy `custom_components/coulst_evse` into your Home Assistant `config/custom_components/`
   directory.
3. Restart Home Assistant.
4. Within a minute or so, the charger should appear under Settings > Devices & Services >
   Discovered - confirm it there. If it doesn't show up (e.g. HA and the charger are on
   different VLANs/subnets that don't pass mDNS), add it manually instead: Add Integration >
   "Coul Street EVSE", host/IP + Modbus unit ID (1, unless you changed it).

## What you get

- One Device per charger, with sensors for every input register in the map (state, live
  measurements, energy, temperatures, current limits).
- A `switch` for charging permitted (register 1).
- A `number` slider for the load-management current limit (register 0), ranged to
  `[MIN_LIMIT_AMPS, max_circuit_current]` to match what the firmware will actually accept.
- A `button` to clear the current limit (write 0), separate from the slider since 0 is a
  special "hand arbitration back to the charger" value, not just the slider's floor.
- An automatic Modbus heartbeat on every poll, so a non-zero failsafe timeout configured on
  the charger doesn't need a separate automation.

## Status / what's not done yet

This is a starting point, not a finished integration:

- No options flow for changing the scan interval or unit ID after setup.
- Not yet packaged for HACS or submitted to HA core.
