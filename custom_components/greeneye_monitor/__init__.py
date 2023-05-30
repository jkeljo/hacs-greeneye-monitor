"""Support for monitoring a GreenEye Monitor energy monitor."""
from __future__ import annotations

import logging

import greeneye
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_NAME
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_SENSORS
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.const import Platform
from homeassistant.const import UnitOfTime
from homeassistant.core import Event
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.issue_registry import IssueSeverity
from homeassistant.helpers.typing import ConfigType

from . import config_validation as gem_cv
from .const import CONF_CHANNELS
from .const import CONF_COUNTED_QUANTITY
from .const import CONF_COUNTED_QUANTITY_PER_PULSE
from .const import CONF_DEVICE_CLASS
from .const import CONF_MONITORS
from .const import CONF_NET_METERING
from .const import CONF_NUMBER
from .const import CONF_PULSE_COUNTERS
from .const import CONF_SEND_PACKET_DELAY
from .const import CONF_SERIAL_NUMBER
from .const import CONF_TEMPERATURE_SENSORS
from .const import CONF_TIME_UNIT
from .const import CONF_VOLTAGE_SENSORS
from .const import DOMAIN
from .const import TEMPERATURE_UNIT_CELSIUS

_LOGGER = logging.getLogger(__name__)

TEMPERATURE_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): gem_cv.temperatureSensorNumber,
        vol.Required(CONF_NAME): cv.string,
    }
)

TEMPERATURE_SENSORS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TEMPERATURE_UNIT): cv.temperature_unit,
        vol.Required(CONF_SENSORS): vol.All(
            cv.ensure_list, [TEMPERATURE_SENSOR_SCHEMA]
        ),
    }
)

VOLTAGE_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): gem_cv.channelNumber,
        vol.Required(CONF_NAME): cv.string,
    }
)

VOLTAGE_SENSORS_SCHEMA = vol.All(cv.ensure_list, [VOLTAGE_SENSOR_SCHEMA])

PULSE_COUNTER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): gem_cv.pulseCounterNumber,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_COUNTED_QUANTITY): cv.string,
        vol.Optional(CONF_DEVICE_CLASS, default=None): gem_cv.deviceClass,
        vol.Optional(CONF_COUNTED_QUANTITY_PER_PULSE, default=1.0): vol.Coerce(float),
        vol.Optional(CONF_TIME_UNIT, default=UnitOfTime.SECONDS): vol.Any(
            UnitOfTime.SECONDS.value, UnitOfTime.MINUTES.value, UnitOfTime.HOURS.value
        ),
    }
)

PULSE_COUNTERS_SCHEMA = vol.All(cv.ensure_list, [PULSE_COUNTER_SCHEMA])

CHANNEL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): gem_cv.channelNumber,
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_NET_METERING, default=False): cv.boolean,
    }
)

CHANNELS_SCHEMA = vol.All(cv.ensure_list, [CHANNEL_SCHEMA])

MONITOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): gem_cv.serialNumber,
        vol.Optional(CONF_CHANNELS, default=[]): CHANNELS_SCHEMA,
        vol.Optional(
            CONF_TEMPERATURE_SENSORS,
            default={CONF_TEMPERATURE_UNIT: TEMPERATURE_UNIT_CELSIUS, CONF_SENSORS: []},
        ): TEMPERATURE_SENSORS_SCHEMA,
        vol.Optional(CONF_PULSE_COUNTERS, default=[]): PULSE_COUNTERS_SCHEMA,
        vol.Optional(CONF_VOLTAGE_SENSORS, default=[]): VOLTAGE_SENSORS_SCHEMA,
    }
)

MONITORS_SCHEMA = vol.All(cv.ensure_list, [MONITOR_SCHEMA])

COMPONENT_SCHEMA = vol.Schema(
    {vol.Required(CONF_PORT): cv.port, vol.Required(CONF_MONITORS): MONITORS_SCHEMA}
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: COMPONENT_SCHEMA}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Copy the YAML configuration to the config entry."""
    if server_config := config.get(DOMAIN):
        ir.async_create_issue(
            hass,
            DOMAIN,
            "remove_yaml",
            is_fixable=False,
            severity=IssueSeverity.WARNING,
            translation_key="remove_yaml",
        )

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=server_config
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup the GreenEye Monitor component from a config entry."""
    send_packet_delay = config_entry.options[CONF_SEND_PACKET_DELAY]
    monitors = greeneye.Monitors(send_packet_delay=send_packet_delay)
    hass.data[DOMAIN] = monitors

    await monitors.start_server(config_entry.data[CONF_PORT])

    async def close_monitors(event: Event) -> None:
        """Close the Monitors object."""
        monitors = hass.data.pop(DOMAIN, None)
        if monitors:
            await monitors.close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_monitors)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.SENSOR, Platform.NUMBER]
        )
    )

    config_entry.async_on_unload(config_entry.add_update_listener(reload_entry))

    return True


async def reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the GreenEye Monitor config entry."""
    await hass.config_entries.async_unload_platforms(
        config_entry, [Platform.NUMBER, Platform.SENSOR]
    )

    monitors = hass.data.pop(DOMAIN)
    await monitors.close()
    return True
