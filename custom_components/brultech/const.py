"""Constants for the brultech component."""
from datetime import timedelta
from typing import cast

from greeneye.monitor import Monitor
from greeneye.monitor import MonitorType
from homeassistant.helpers.entity import DeviceInfo

AUX5_TYPE_CT = "ct"
AUX5_TYPE_PULSE_COUNTER = "pulse_counter"

CONF_AUX5_TYPE = "aux5_type"
CONF_CHANNELS = "channels"
CONF_COUNTED_QUANTITY = "counted_quantity"
CONF_COUNTED_QUANTITY_PER_PULSE = "counted_quantity_per_pulse"
CONF_DEVICE_CLASS = "device_class"
CONF_IS_AUX = "is_aux"
CONF_MONITORS = "monitors"
CONF_NET_METERING = "net_metering"
CONF_NUMBER = "number"
CONF_PULSE_COUNTERS = "pulse_counters"
CONF_SEND_PACKET_DELAY = "send_packet_delay"
CONF_SERIAL_NUMBER = "serial_number"
CONF_TEMPERATURE_SENSORS = "temperature_sensors"
CONF_TIME_UNIT = "time_unit"
CONF_VOLTAGE_SENSORS = "voltage"
CONFIG_ENTRY_TITLE = "Brultech"

DEFAULT_UPDATE_INTERVAL = timedelta(minutes=30)
DEVICE_TYPE_AUX = "aux"
DEVICE_TYPE_CURRENT_TRANSFORMER = "channel"
DEVICE_TYPE_PULSE_COUNTER = "pulse counter"
DEVICE_TYPE_TEMPERATURE_SENSOR = "temperature"
DEVICE_TYPE_VOLTAGE_SENSOR = "voltage"
DOMAIN = "brultech"

TEMPERATURE_UNIT_CELSIUS = "C"


def get_monitor_type_short_name(monitor: Monitor) -> str:
    if monitor.type == MonitorType.GEM:
        return "GEM"
    elif monitor.type in [MonitorType.ECM_1220, MonitorType.ECM_1240]:
        return "ECM"
    else:
        assert False


def get_monitor_type_long_name(monitor: Monitor) -> str:
    if monitor.type == MonitorType.GEM:
        return "GreenEye Monitor"
    elif monitor.type == MonitorType.ECM_1240:
        return "ECM-1240"
    elif monitor.type == MonitorType.ECM_1220:
        return "ECM-1220/1240"
    else:
        assert False


def make_device_info(monitor: Monitor, device_type: str, number: int) -> DeviceInfo:
    monitor_type_short_name = get_monitor_type_short_name(monitor)
    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                cast(
                    str,
                    f"{monitor.serial_number}-{device_type}-{number + 1}",
                ),
            )
        },
        name=f"{monitor_type_short_name} {monitor.serial_number} {device_type} {number + 1}",
        via_device=(DOMAIN, f"{monitor.serial_number}"),
    )
