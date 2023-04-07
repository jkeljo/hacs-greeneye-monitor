"""Config flows for greeneye_monitor."""
from copy import deepcopy
from typing import Tuple

import greeneye
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.selector as selector
import voluptuous as vol
from greeneye.api import TemperatureUnit
from homeassistant import config_entries
from homeassistant import data_entry_flow
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_PORT
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfInformation
from homeassistant.const import UnitOfLength
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.const import UnitOfTemperature
from homeassistant.const import UnitOfTime
from homeassistant.const import UnitOfVolume
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
from .const import CONFIG_ENTRY_TITLE
from .const import DOMAIN

COUNTED_QUANTITY_OPTIONS = list(
    sorted(
        set(
            [
                *[i.value for i in UnitOfVolume],
                *[i.value for i in UnitOfEnergy],
                *[i.value for i in UnitOfTime],
                *[i.value for i in UnitOfLength],
                *[i.value for i in UnitOfPrecipitationDepth],
                *[i.value for i in UnitOfInformation],
                "pulses",
            ]
        )
    )
)


PULSE_COUNTER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COUNTED_QUANTITY, default="pulses"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=COUNTED_QUANTITY_OPTIONS,
            )
        ),
        vol.Required(CONF_COUNTED_QUANTITY_PER_PULSE, default=1.0): vol.Coerce(float),
        vol.Optional(CONF_DEVICE_CLASS, default=None): vol.Maybe(
            vol.Coerce(SensorDeviceClass)
        ),
    }
)


def make_pulse_counters_schema(
    monitor: greeneye.monitor.Monitor | None = None,
) -> vol.Schema:
    num_pulse_counters = 4
    if monitor and monitor.pulse_counters is not None:
        num_pulse_counters = len(monitor.pulse_counters)

    return vol.Schema(
        {
            vol.Optional(vol.Range(0, num_pulse_counters - 1)): PULSE_COUNTER_SCHEMA,
        }
    )


def make_toplevel_schema(monitor: greeneye.monitor.Monitor | None = None) -> vol.Schema:
    default_temperature_unit = UnitOfTemperature.CELSIUS
    if monitor and monitor.temperature_sensors:
        if monitor.temperature_sensors[0].unit == TemperatureUnit.CELSIUS:
            default_temperature_unit = UnitOfTemperature.CELSIUS
        else:
            default_temperature_unit = UnitOfTemperature.FAHRENHEIT

    default_net_metering = []
    num_channels = 48
    if monitor and monitor.channels is not None:
        num_channels = len(monitor.channels)
        default_net_metering = [
            str(channel.number) for channel in monitor.channels if channel.net_metering
        ]

    net_metering_options = {str(i): i + 1 for i in range(0, num_channels)}

    return vol.Schema(
        {
            vol.Optional(
                CONF_TEMPERATURE_UNIT, default=default_temperature_unit
            ): vol.Coerce(UnitOfTemperature),
            vol.Optional(
                CONF_NET_METERING, default=default_net_metering
            ): cv.multi_select(net_metering_options),
        }
    )


def make_monitor_schema(monitor: greeneye.monitor.Monitor | None = None) -> vol.Schema:
    return make_toplevel_schema(monitor).extend(
        {
            vol.Optional(CONF_PULSE_COUNTERS, default={}): make_pulse_counters_schema(
                monitor
            ),
        }
    )


MONITOR_SCHEMA = make_monitor_schema()

MONITORS_SCHEMA = vol.Schema(
    {
        vol.Optional(cv.positive_int): MONITOR_SCHEMA,
    }
)

PORT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, description={"suggested_value": 8000}): cv.port,
    }
)

CONFIG_ENTRY_DATA_SCHEMA = PORT_SCHEMA.extend(
    {vol.Optional(CONF_MONITORS, default={}): MONITORS_SCHEMA}
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
        vol.Optional(CONF_MONITORS, default={}): MONITORS_OPTIONS_SCHEMA,
    }
)


class GreeneyeMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for greeneye_monitor."""

    VERSION = 1

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
            title=CONFIG_ENTRY_TITLE, data=data, options=options
        )

    async def async_step_user(
        self, user_input: DiscoveryInfoType
    ) -> data_entry_flow.FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=CONFIG_ENTRY_TITLE,
                data=CONFIG_ENTRY_DATA_SCHEMA(user_input),
                options=CONFIG_ENTRY_OPTIONS_SCHEMA({}),
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_show_form(step_id="user", data_schema=PORT_SCHEMA)

    async def async_step_integration_discovery(
        self,
        monitor_info: DiscoveryInfoType,
    ) -> data_entry_flow.FlowResult:
        if monitor_info:
            self._net_metering = monitor_info[CONF_NET_METERING]
            self._temperature_unit = monitor_info[CONF_TEMPERATURE_UNIT]
            self._pulse_counters = []
            return await self.async_step_pulse_counter()

        serial_number = self.context["serial_number"]
        monitors: greeneye.Monitors = self.hass.data[DOMAIN]
        self._monitor = monitors.monitors[serial_number]
        schema = make_toplevel_schema(self._monitor)
        self.context["title_placeholders"] = {
            "device_name": f"GreenEye Monitor {serial_number}",
            "serial_number": f"{serial_number}",
        }
        return self.async_show_form(
            step_id="integration_discovery",
            data_schema=schema,
            description_placeholders={
                "serial_number": f"{serial_number}",
                "device_name": f"GEM {serial_number}",
            },
        )

    async def async_step_pulse_counter(
        self, pulse_counter_info: DiscoveryInfoType | None = None
    ) -> data_entry_flow.FlowResult:
        if pulse_counter_info:
            self._pulse_counters.append(pulse_counter_info)
            if len(self._pulse_counters) < len(self._monitor.pulse_counters):
                return await self.async_step_pulse_counter()

        if pulse_counter_info or not self._monitor.pulse_counters:
            config_entry = await self.async_set_unique_id(DOMAIN)
            assert config_entry
            new_data = deepcopy(dict(config_entry.data))
            new_data[CONF_MONITORS][self._monitor.serial_number] = MONITOR_SCHEMA(
                {
                    CONF_TEMPERATURE_UNIT: self._temperature_unit,
                    CONF_NET_METERING: self._net_metering,
                    CONF_PULSE_COUNTERS: {
                        i: pulse_counter
                        for i, pulse_counter in enumerate(self._pulse_counters)
                    },
                }
            )
            new_options = deepcopy(dict(config_entry.options))
            new_options[CONF_MONITORS][self._monitor.serial_number] = {
                CONF_PULSE_COUNTERS: {
                    i: PULSE_COUNTER_OPTIONS_SCHEMA({})
                    for i, _ in enumerate(self._pulse_counters)
                }
            }

            self.hass.config_entries.async_update_entry(
                config_entry, data=new_data, options=new_options
            )
            await self.hass.config_entries.async_reload(config_entry.entry_id)
            return self.async_abort(
                reason="success",
                description_placeholders={
                    "serial_number": f"{self._monitor.serial_number}"
                },
            )

        return self.async_show_form(
            step_id="pulse_counter",
            data_schema=PULSE_COUNTER_SCHEMA,
            description_placeholders={
                "pulse_counter_number": f"{len(self._pulse_counters) + 1}"
            },
        )


def yaml_to_config_entry(
    yaml: DiscoveryInfoType,
) -> Tuple[DiscoveryInfoType, DiscoveryInfoType]:
    data = {
        CONF_PORT: yaml[CONF_PORT],
        CONF_MONITORS: {
            monitor[CONF_SERIAL_NUMBER]: {
                CONF_TEMPERATURE_UNIT: monitor[CONF_TEMPERATURE_SENSORS][
                    CONF_TEMPERATURE_UNIT
                ],
                CONF_NET_METERING: [
                    channel[CONF_NUMBER] - 1
                    for channel in monitor[CONF_CHANNELS]
                    if channel[CONF_NET_METERING]
                ],
                CONF_PULSE_COUNTERS: {
                    pulse_counter[CONF_NUMBER]
                    - 1: {
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
                    pulse_counter[CONF_NUMBER]
                    - 1: {
                        CONF_TIME_UNIT: pulse_counter[CONF_TIME_UNIT],
                    }
                    for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                },
            }
            for monitor in yaml[CONF_MONITORS]
        }
    }
    return data, options
