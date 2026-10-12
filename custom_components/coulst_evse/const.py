"""Constants for the Coul Street EVSE integration.

The register map here mirrors components/evse/src/modbus_regs.h, which is the source of
truth. If MAP_VERSION read from the charger doesn't match EXPECTED_MAP_VERSION, the map has
changed incompatibly and this file needs revisiting.
"""

DOMAIN = "coulst_evse"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1

# Telemetry refreshes every 1s on the charger; the STM32 itself is polled every 5s, so
# there's nothing to gain from polling faster than that.
DEFAULT_SCAN_INTERVAL = 5

EXPECTED_MAP_VERSION = 1

# Input registers (FC4), block based at 0.
INPUT_MAP_VERSION = 0
INPUT_CHARGING_STATE = 1
INPUT_PILOT_STATE = 2
INPUT_CABLE_LOCK_STATE = 3
INPUT_STATUS_FLAGS = 4
INPUT_OFFERED_CURRENT_A = 5
INPUT_VOLTAGE_DV = 6
INPUT_CURRENT_CA = 7
INPUT_ACTIVE_POWER_W = 8  # u32, 2 registers
INPUT_SESSION_WH = 10  # u32, 2 registers
INPUT_LIFETIME_WH = 12  # u32, 2 registers
INPUT_SESSION_SECS = 14  # u32, 2 registers
INPUT_RELAY_TEMP_DC = 16
INPUT_BOARD_TEMP_DC = 17
INPUT_SOCKET_TEMP_DC = 18
INPUT_MAX_CIRCUIT_A = 19
INPUT_MAX_USER_SET_A = 20
INPUT_MAX_CABLE_A = 21
INPUT_LIMITING_SOURCE = 22
INPUT_VFLAGS = 23  # u32, 2 registers
INPUT_APPLIED_LIMIT_A = 25
INPUT_CONTROL_STATE = 26
INPUT_SINCE_WRITE_SECS = 27  # u32, 2 registers

INPUT_BLOCK_COUNT = 29  # registers 0-28

# Status flags bitfield, input register 4.
STATUS_VEHICLE_CONNECTED = 0x0001
STATUS_POWER_OFFERED = 0x0002
STATUS_CHARGING = 0x0004
STATUS_ACTIVE = 0x0008
STATUS_ERROR = 0x0010
STATUS_COMM_ERROR = 0x0020
STATUS_BOOT_LOCKED = 0x0040
STATUS_OCPP_CONNECTED = 0x0080

# Temperature sentinel for a sensor that isn't installed (int16 0x8000).
TEMP_NOT_INSTALLED = -32768

# Holding registers (FC3/FC6/FC16), block based at 0.
HOLDING_LIMIT_AMPS = 0
HOLDING_CHARGE_PERMIT = 1
HOLDING_HEARTBEAT = 2

MIN_LIMIT_AMPS = 6
MAX_LIMIT_AMPS_FALLBACK = 80

CHARGING_STATE_NAMES = {
    0: "Unknown",
    1: "Idle",
    2: "EV connected",
    3: "Charging",
    5: "Diode check failed",
    6: "GFCI fault",
    7: "No ground",
    8: "Stuck relay",
    9: "GFCI test failed",
    10: "Over temperature",
    11: "Over current",
    14: "Relay closure fault",
    15: "Fault",
}

PILOT_STATE_NAMES = {
    0: "Unknown",
    1: "A",
    2: "B",
    3: "C",
    4: "D",
}

CABLE_LOCK_STATE_NAMES = {
    0: "Unknown",
    1: "Prepare locking",
    2: "Locking",
    3: "Locked",
    4: "Prepare unlocking",
    5: "Unlocking",
    6: "Unlocked",
    7: "Stuck locking",
    8: "Stuck unlocking",
    9: "Not installed",
}

LIMITING_SOURCE_NAMES = {
    0: "Unknown",
    1: "Hardware rating",
    2: "Circuit",
    3: "User setting",
    4: "Cable",
    5: "Load management",
    6: "Temperature",
    7: "Overcurrent derate",
    8: "Undervoltage derate",
}

CONTROL_STATE_NAMES = {
    0: "Idle",
    1: "Active",
    2: "Failsafe",
}


def unit_kwarg(unit_id: int) -> dict[str, int]:
    """Return the unit-id kwarg for the installed pymodbus.

    pymodbus 3.10 renamed ``slave`` to ``device_id`` and later removed ``slave``.
    """
    import inspect

    from pymodbus.client import AsyncModbusTcpClient

    params = inspect.signature(AsyncModbusTcpClient.read_input_registers).parameters
    return {"device_id" if "device_id" in params else "slave": unit_id}
