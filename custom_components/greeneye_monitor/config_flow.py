"""Config flows for greeneye_monitor."""
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant import data_entry_flow
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import CONF_CHANNELS
from .const import CONF_COUNTED_QUANTITY
from .const import CONF_COUNTED_QUANTITY_PER_PULSE
from .const import CONF_DEVICE_CLASS
from .const import CONF_MONITORS
from .const import CONF_NET_METERING
from .const import CONF_NUMBER
from .const import CONF_PULSE_COUNTERS
from .const import CONF_SERIAL_NUMBER
from .const import CONF_TEMPERATURE_SENSORS
from .const import CONF_TIME_UNIT
from .const import DOMAIN


def deviceClass(value: Any) -> SensorDeviceClass | None:
    if value is None:
        return None
    value = cv.string(value)
    return SensorDeviceClass(value)


PULSE_COUNTER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COUNTED_QUANTITY): cv.string,
        vol.Optional(CONF_DEVICE_CLASS, default=None): deviceClass,
        vol.Optional(CONF_COUNTED_QUANTITY_PER_PULSE, default=1.0): vol.Coerce(float),
    }
)

PULSE_COUNTERS_SCHEMA = vol.All(cv.ensure_list, [PULSE_COUNTER_SCHEMA])

CHANNEL_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NET_METERING, default=False): cv.boolean,
    }
)

CHANNELS_SCHEMA = vol.All(cv.ensure_list, [CHANNEL_SCHEMA])

MONITOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): vol.All(
            cv.string,
            vol.Length(
                min=8,
                max=8,
                msg=(
                    "GEM serial number must be specified as an 8-character "
                    "string (including leading zeroes)."
                ),
            ),
            vol.Coerce(int),
        ),
        vol.Required(CONF_TEMPERATURE_UNIT): cv.temperature_unit,
        vol.Optional(CONF_CHANNELS, default=[]): CHANNELS_SCHEMA,
        vol.Optional(CONF_PULSE_COUNTERS, default=[]): PULSE_COUNTERS_SCHEMA,
    }
)

MONITORS_SCHEMA = vol.All(cv.ensure_list, [MONITOR_SCHEMA])

COMPONENT_SCHEMA = vol.Schema(
    {vol.Required(CONF_PORT): cv.port, vol.Required(CONF_MONITORS): MONITORS_SCHEMA}
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: COMPONENT_SCHEMA}, extra=vol.ALLOW_EXTRA)


class GreeneyeMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for greeneye_monitor."""

    async def async_step_import(
        self, discovery_info: DiscoveryInfoType
    ) -> data_entry_flow.FlowResult:
        """Create a config entry from YAML configuration."""
        data = {
            CONF_PORT: discovery_info[CONF_PORT],
            CONF_MONITORS: {
                monitor[CONF_SERIAL_NUMBER]: {
                    CONF_TEMPERATURE_UNIT: monitor[CONF_TEMPERATURE_SENSORS][
                        CONF_TEMPERATURE_UNIT
                    ],
                    CONF_CHANNELS: {
                        channel[CONF_NUMBER]: {
                            CONF_NET_METERING: channel[CONF_NET_METERING]
                        }
                        for channel in monitor[CONF_CHANNELS]
                    },
                    CONF_PULSE_COUNTERS: {
                        pulse_counter[CONF_NUMBER]: {
                            CONF_DEVICE_CLASS: pulse_counter[CONF_DEVICE_CLASS],
                            CONF_COUNTED_QUANTITY: pulse_counter[CONF_COUNTED_QUANTITY],
                            CONF_COUNTED_QUANTITY_PER_PULSE: pulse_counter[
                                CONF_COUNTED_QUANTITY_PER_PULSE
                            ],
                        }
                        for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                    },
                }
                for monitor in discovery_info[CONF_MONITORS]
            },
        }
        options = {
            CONF_MONITORS: {
                monitor[CONF_SERIAL_NUMBER]: {},
                CONF_PULSE_COUNTERS: {
                    pulse_counter[CONF_NUMBER]: {
                        CONF_TIME_UNIT: pulse_counter[CONF_TIME_UNIT],
                    }
                    for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                },
            }
            for monitor in discovery_info[CONF_MONITORS]
        }

        if entry := await self.async_set_unique_id(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data=data, options=options
            )
            self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="GreenEye Monitor", data=data, options=options
        )
