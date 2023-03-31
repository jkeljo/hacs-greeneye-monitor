"""Config flows for greeneye_monitor."""
from typing import Tuple

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant import data_entry_flow
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.const import UnitOfTime
from homeassistant.helpers.typing import DiscoveryInfoType

from . import config_validation as gem_cv
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
from .const import TEMPERATURE_UNIT_CELSIUS


TEMPERATURE_SENSORS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TEMPERATURE_UNIT): cv.temperature_unit,
    }
)

PULSE_COUNTER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COUNTED_QUANTITY): cv.string,
        vol.Optional(CONF_DEVICE_CLASS, default=None): gem_cv.deviceClass,
        vol.Optional(CONF_COUNTED_QUANTITY_PER_PULSE, default=1.0): vol.Coerce(float),
    }
)

PULSE_COUNTERS_SCHEMA = vol.Schema(
    {
        vol.Optional(gem_cv.pulseCounterNumber): PULSE_COUNTER_SCHEMA,
    }
)

CHANNEL_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NET_METERING, default=False): cv.boolean,
    }
)

CHANNELS_SCHEMA = vol.Schema(
    {
        vol.Optional(gem_cv.channelNumber): CHANNEL_SCHEMA,
    }
)

MONITOR_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_TEMPERATURE_SENSORS,
            default={CONF_TEMPERATURE_UNIT: TEMPERATURE_UNIT_CELSIUS},
        ): TEMPERATURE_SENSORS_SCHEMA,
        vol.Optional(CONF_CHANNELS, default={}): CHANNELS_SCHEMA,
        vol.Optional(CONF_PULSE_COUNTERS, default={}): PULSE_COUNTERS_SCHEMA,
    }
)

MONITORS_SCHEMA = vol.Schema(
    {
        vol.Optional(cv.positive_int): MONITOR_SCHEMA,
    }
)

CONFIG_ENTRY_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_PORT): cv.port, vol.Required(CONF_MONITORS): MONITORS_SCHEMA}
)

PULSE_COUNTER_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TIME_UNIT, default=UnitOfTime.SECONDS): vol.Any(
            UnitOfTime.SECONDS.value, UnitOfTime.MINUTES.value, UnitOfTime.HOURS.value
        )
    }
)

PULSE_COUNTERS_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(gem_cv.pulseCounterNumber): PULSE_COUNTER_OPTIONS_SCHEMA,
    }
)

MONITOR_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PULSE_COUNTERS, default={}): PULSE_COUNTERS_OPTIONS_SCHEMA,
    }
)

MONITORS_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(cv.positive_int): MONITOR_OPTIONS_SCHEMA,
    }
)

CONFIG_ENTRY_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MONITORS): MONITORS_OPTIONS_SCHEMA,
    }
)


class GreeneyeMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for greeneye_monitor."""

    async def async_step_import(
        self, discovery_info: DiscoveryInfoType
    ) -> data_entry_flow.FlowResult:
        """Create a config entry from YAML configuration."""
        data, options = yaml_to_config_entry(discovery_info)

        if entry := await self.async_set_unique_id(DOMAIN):
            self.hass.config_entries.async_update_entry(
                entry, data=data, options=options
            )
            self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="GreenEye Monitor", data=data, options=options
        )


def yaml_to_config_entry(
    yaml: DiscoveryInfoType,
) -> Tuple[DiscoveryInfoType, DiscoveryInfoType]:
    data = {
        CONF_PORT: yaml[CONF_PORT],
        CONF_MONITORS: {
            monitor[CONF_SERIAL_NUMBER]: {
                CONF_TEMPERATURE_SENSORS: {
                    CONF_TEMPERATURE_UNIT: monitor[CONF_TEMPERATURE_SENSORS][
                        CONF_TEMPERATURE_UNIT
                    ],
                },
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
            for monitor in yaml[CONF_MONITORS]
        },
    }
    options = {
        CONF_MONITORS: {
            monitor[CONF_SERIAL_NUMBER]: {
                CONF_PULSE_COUNTERS: {
                    pulse_counter[CONF_NUMBER]: {
                        CONF_TIME_UNIT: pulse_counter[CONF_TIME_UNIT],
                    }
                    for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                },
            }
            for monitor in yaml[CONF_MONITORS]
        }
    }
    return data, options
