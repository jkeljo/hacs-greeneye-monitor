"""Config flows for brultech."""
from copy import deepcopy
from typing import Any
from typing import Tuple

import greeneye
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.selector as selector
import voluptuous as vol
from greeneye.api import TemperatureUnit
from greeneye.monitor import MonitorType
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
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import AUX5_TYPE_CT
from .const import AUX5_TYPE_PULSE_COUNTER
from .const import CONF_AUX5_TYPE
from .const import CONF_CHANNELS
from .const import CONF_COUNTED_QUANTITY
from .const import CONF_COUNTED_QUANTITY_PER_PULSE
from .const import CONF_DEVICE_CLASS
from .const import CONF_IS_AUX
from .const import CONF_MONITORS
from .const import CONF_NET_METERING
from .const import CONF_NUMBER
from .const import CONF_PULSE_COUNTERS
from .const import CONF_SEND_PACKET_DELAY
from .const import CONF_SERIAL_NUMBER
from .const import CONF_TEMPERATURE_SENSORS
from .const import CONF_TIME_UNIT
from .const import CONFIG_ENTRY_TITLE
from .const import DOMAIN
from .const import get_monitor_type_long_name
from .const import get_monitor_type_short_name

AUX5_TYPE_OPTIONS = [AUX5_TYPE_CT, AUX5_TYPE_PULSE_COUNTER]

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

PULSE_COUNTER_CONFIG_UI_SCHEMA = vol.Schema(
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


PULSE_COUNTER_SCHEMA = vol.Schema(
    PULSE_COUNTER_CONFIG_UI_SCHEMA.extend(
        {
            vol.Required(CONF_NUMBER): cv.positive_int,
            vol.Optional(CONF_IS_AUX, default=False): bool,
        }
    )
)

PULSE_COUNTERS_SCHEMA = vol.All(cv.ensure_list, [PULSE_COUNTER_SCHEMA])


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

    schema = vol.Schema(
        {
            vol.Optional(
                CONF_NET_METERING, default=default_net_metering
            ): cv.multi_select(net_metering_options),
        }
    )
    if not monitor or monitor.type == MonitorType.GEM:
        schema = schema.extend(
            {
                vol.Optional(
                    CONF_TEMPERATURE_UNIT, default=default_temperature_unit
                ): vol.Coerce(UnitOfTemperature),
            }
        )
    if not monitor or monitor.type == MonitorType.ECM_1240:
        schema = schema.extend(
            {
                vol.Optional(CONF_AUX5_TYPE): vol.Maybe(
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=AUX5_TYPE_OPTIONS, translation_key="aux5_type"
                        )
                    )
                )
            }
        )

    return schema


def make_monitor_schema(monitor: greeneye.monitor.Monitor | None = None) -> vol.Schema:
    return make_toplevel_schema(monitor).extend(
        {
            vol.Required(CONF_SERIAL_NUMBER): cv.positive_int,
            vol.Optional(CONF_PULSE_COUNTERS, default=[]): PULSE_COUNTERS_SCHEMA,
        }
    )


MONITOR_SCHEMA = make_monitor_schema()

MONITORS_SCHEMA = vol.All(cv.ensure_list, [MONITOR_SCHEMA])

PORT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, description={"suggested_value": 8000}): cv.port,
    }
)

CONFIG_ENTRY_DATA_SCHEMA = PORT_SCHEMA.extend(
    {vol.Optional(CONF_MONITORS, default=[]): MONITORS_SCHEMA}
)


def make_pulse_counter_options_schema(time_unit: str = UnitOfTime.SECONDS.value):
    return vol.Schema(
        {
            vol.Optional(CONF_TIME_UNIT, default=time_unit): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        UnitOfTime.SECONDS.value,
                        UnitOfTime.MINUTES.value,
                        UnitOfTime.HOURS.value,
                    ],
                    translation_key="time_unit",
                )
            )
        }
    )


PULSE_COUNTER_OPTIONS_UI_SCHEMA = make_pulse_counter_options_schema()

PULSE_COUNTER_OPTIONS_SCHEMA = PULSE_COUNTER_OPTIONS_UI_SCHEMA.extend(
    {vol.Required(CONF_NUMBER): cv.positive_int}
)

PULSE_COUNTERS_OPTIONS_SCHEMA = vol.All(cv.ensure_list, [PULSE_COUNTER_OPTIONS_SCHEMA])

MONITOR_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): cv.positive_int,
        vol.Optional(CONF_PULSE_COUNTERS, default=[]): PULSE_COUNTERS_OPTIONS_SCHEMA,
    }
)

MONITORS_OPTIONS_SCHEMA = vol.All(cv.ensure_list, [MONITOR_OPTIONS_SCHEMA])


def make_global_options_schema(send_packet_delay: bool = False):
    return vol.Schema(
        {
            vol.Optional(CONF_SEND_PACKET_DELAY, default=send_packet_delay): bool,
        }
    )


GLOBAL_OPTIONS_SCHEMA = make_global_options_schema()

CONFIG_ENTRY_OPTIONS_SCHEMA = GLOBAL_OPTIONS_SCHEMA.extend(
    {
        vol.Optional(CONF_MONITORS, default=[]): MONITORS_OPTIONS_SCHEMA,
    }
)


class BrultechConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for brultech."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return BrultechOptionsFlow(config_entry)

    async def async_step_import(
        self, discovery_info: DiscoveryInfoType
    ) -> data_entry_flow.FlowResult:
        """Create a config entry from YAML configuration."""
        data, options = yaml_to_config_entry(discovery_info)

        if entry := await self.async_set_unique_id(DOMAIN):
            yaml_serial_numbers = set(
                [monitor[CONF_SERIAL_NUMBER] for monitor in data[CONF_MONITORS]]
            )

            data[CONF_MONITORS].extend(
                [
                    monitor
                    for monitor in entry.data[CONF_MONITORS]
                    if monitor[CONF_SERIAL_NUMBER] not in yaml_serial_numbers
                ]
            )
            options[CONF_MONITORS].extend(
                [
                    monitor
                    for monitor in entry.options[CONF_MONITORS]
                    if monitor[CONF_SERIAL_NUMBER] not in yaml_serial_numbers
                ]
            )

            self.hass.config_entries.async_update_entry(
                entry, data=data, options=options
            )
            self._abort_if_unique_id_configured()

        # This integration used to name entities based on what the user had put in the YAML.
        # Now it uses standardized entity names. If the user hasn't renamed an entity via the UI,
        # if we do nothing, the entity name will change from something they had specified in the YAML
        # to something generic. To avoid this, we look for entities that weren't renamed and we copy their
        # old integration-defined names to user-defined ones.
        entity_registry = er.async_get(self.hass)
        for entry in entity_registry.entities.values():
            if entry.platform != DOMAIN:
                continue

            if entry.name is None:
                entity_registry.async_update_entity(
                    entry.entity_id, name=entry.original_name
                )

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
            self._temperature_unit = monitor_info.get(CONF_TEMPERATURE_UNIT)
            self._pulse_counters = []
            self._aux5_type = monitor_info.get(CONF_AUX5_TYPE)
            return await self.async_step_pulse_counter()

        serial_number = self.context["serial_number"]
        monitors: greeneye.Monitors = self.hass.data[DOMAIN]
        self._monitor = monitors.monitors[serial_number]
        monitor_type_short_name = get_monitor_type_short_name(self._monitor)
        monitor_type_long_name = get_monitor_type_long_name(self._monitor)

        config_entry = await self.async_set_unique_id(DOMAIN)
        assert config_entry
        if any(
            filter(
                lambda x: x[CONF_SERIAL_NUMBER] == serial_number,
                config_entry.data[CONF_MONITORS],
            ),
        ):
            self._abort_if_unique_id_configured()

        schema = make_toplevel_schema(self._monitor)

        self.context["title_placeholders"] = {
            "device_name": f"{monitor_type_long_name} {serial_number}",
            "serial_number": f"{serial_number}",
        }
        return self.async_show_form(
            step_id="integration_discovery",
            data_schema=schema,
            description_placeholders={
                "serial_number": f"{serial_number}",
                "device_name": f"{monitor_type_short_name} {serial_number}",
            },
        )

    async def async_step_pulse_counter(
        self, pulse_counter_info: DiscoveryInfoType | None = None
    ) -> data_entry_flow.FlowResult:
        has_aux_pulse_counter = self._aux5_type == AUX5_TYPE_PULSE_COUNTER
        num_pulse_counters = (
            1 if has_aux_pulse_counter else len(self._monitor.pulse_counters)
        )
        if pulse_counter_info:
            self._pulse_counters.append(
                PULSE_COUNTER_SCHEMA(
                    {
                        CONF_NUMBER: len(self._pulse_counters)
                        if not has_aux_pulse_counter
                        else 4,
                        CONF_IS_AUX: has_aux_pulse_counter,
                        **pulse_counter_info,
                    }
                )
            )
            if len(self._pulse_counters) < num_pulse_counters:
                return await self.async_step_pulse_counter()

        if pulse_counter_info or num_pulse_counters == 0:
            config_entry = await self.async_set_unique_id(DOMAIN)
            assert config_entry
            new_data = deepcopy(dict(config_entry.data))
            monitor_data = {
                CONF_SERIAL_NUMBER: self._monitor.serial_number,
                CONF_AUX5_TYPE: self._aux5_type,
                CONF_NET_METERING: self._net_metering,
                CONF_PULSE_COUNTERS: self._pulse_counters,
            }
            if self._temperature_unit:
                monitor_data[CONF_TEMPERATURE_UNIT] = self._temperature_unit
            new_data[CONF_MONITORS].append(MONITOR_SCHEMA(monitor_data))
            new_data = CONFIG_ENTRY_DATA_SCHEMA(new_data)

            new_options = deepcopy(dict(config_entry.options))
            new_options[CONF_MONITORS].append(
                MONITOR_OPTIONS_SCHEMA(
                    {
                        CONF_SERIAL_NUMBER: self._monitor.serial_number,
                        CONF_PULSE_COUNTERS: [
                            PULSE_COUNTER_OPTIONS_SCHEMA(
                                {
                                    CONF_NUMBER: 4 if has_aux_pulse_counter else i,
                                }
                            )
                            for i in range(len(self._pulse_counters))
                        ],
                    }
                )
            )
            new_options = CONFIG_ENTRY_OPTIONS_SCHEMA(new_options)

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
            data_schema=PULSE_COUNTER_CONFIG_UI_SCHEMA,
            description_placeholders={
                "pulse_counter_number": f"{(len(self._pulse_counters) + 1) if not has_aux_pulse_counter else 'Aux 5'}"
            },
        )


def yaml_to_config_entry(
    yaml: DiscoveryInfoType,
) -> Tuple[DiscoveryInfoType, DiscoveryInfoType]:
    data = CONFIG_ENTRY_DATA_SCHEMA(
        {
            CONF_PORT: yaml[CONF_PORT],
            CONF_MONITORS: [
                {
                    CONF_SERIAL_NUMBER: monitor[CONF_SERIAL_NUMBER],
                    CONF_TEMPERATURE_UNIT: monitor[CONF_TEMPERATURE_SENSORS][
                        CONF_TEMPERATURE_UNIT
                    ],
                    CONF_NET_METERING: [
                        str(channel[CONF_NUMBER] - 1)
                        for channel in monitor[CONF_CHANNELS]
                        if channel[CONF_NET_METERING]
                    ],
                    CONF_PULSE_COUNTERS: [
                        {
                            CONF_NUMBER: pulse_counter[CONF_NUMBER] - 1,
                            CONF_DEVICE_CLASS: pulse_counter[CONF_DEVICE_CLASS],
                            CONF_COUNTED_QUANTITY: pulse_counter[CONF_COUNTED_QUANTITY],
                            CONF_COUNTED_QUANTITY_PER_PULSE: pulse_counter[
                                CONF_COUNTED_QUANTITY_PER_PULSE
                            ],
                        }
                        for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                    ],
                }
                for monitor in yaml[CONF_MONITORS]
            ],
        }
    )
    options = CONFIG_ENTRY_OPTIONS_SCHEMA(
        {
            CONF_MONITORS: [
                {
                    CONF_SERIAL_NUMBER: monitor[CONF_SERIAL_NUMBER],
                    CONF_PULSE_COUNTERS: [
                        {
                            CONF_NUMBER: pulse_counter[CONF_NUMBER] - 1,
                            CONF_TIME_UNIT: pulse_counter[CONF_TIME_UNIT],
                        }
                        for pulse_counter in monitor[CONF_PULSE_COUNTERS]
                    ],
                }
                for monitor in yaml[CONF_MONITORS]
            ]
        }
    )

    return data, options


class BrultechOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="options_menu",
            menu_options=["global_options", "choose_monitor"],
        )

    async def async_step_global_options(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        if user_input is not None:
            options = deepcopy(dict(self.config_entry.options))
            options[CONF_SEND_PACKET_DELAY] = user_input[CONF_SEND_PACKET_DELAY]
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="global_options",
            data_schema=make_global_options_schema(
                send_packet_delay=self.config_entry.options[CONF_SEND_PACKET_DELAY]
            ),
        )

    async def async_step_choose_monitor(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        if user_input is not None:
            self._serial_number = int(user_input[CONF_SERIAL_NUMBER])
            return await self.async_step_choose_pulse_counter(None)

        serial_numbers = [
            str(monitor[CONF_SERIAL_NUMBER])
            for monitor in self.config_entry.options[CONF_MONITORS]
            if monitor[CONF_PULSE_COUNTERS]
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_NUMBER): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=serial_numbers,
                        multiple=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="choose_monitor",
            data_schema=schema,
        )

    async def async_step_choose_pulse_counter(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        if user_input:
            self._pulse_counter_number = int(user_input[CONF_NUMBER])
            return await self.async_step_pulse_counter_options(None)

        options = next(
            filter(
                lambda option: option[CONF_SERIAL_NUMBER] == self._serial_number,
                self.config_entry.options[CONF_MONITORS],
            )
        )
        numbers = [
            selector.SelectOptionDict(
                label=str(pulse_counter[CONF_NUMBER] + 1),
                value=str(pulse_counter[CONF_NUMBER]),
            )
            for pulse_counter in options[CONF_PULSE_COUNTERS]
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_NUMBER): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=numbers,
                        multiple=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="choose_pulse_counter",
            data_schema=schema,
            description_placeholders={
                CONF_SERIAL_NUMBER: str(self._serial_number),
            },
        )

    async def async_step_pulse_counter_options(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        options = self.config_entry.options
        if user_input:
            options = deepcopy(dict(options))

        monitor_options = next(
            filter(
                lambda monitor: monitor[CONF_SERIAL_NUMBER] == self._serial_number,
                options[CONF_MONITORS],
            )
        )
        pulse_counter_options = next(
            filter(
                lambda pulse_counter: pulse_counter[CONF_NUMBER]
                == self._pulse_counter_number,
                monitor_options[CONF_PULSE_COUNTERS],
            )
        )

        if user_input:
            pulse_counter_options[CONF_TIME_UNIT] = user_input[CONF_TIME_UNIT]
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="pulse_counter_options",
            data_schema=make_pulse_counter_options_schema(
                pulse_counter_options[CONF_TIME_UNIT]
            ),
            description_placeholders={
                "pulse_counter_number": f"{self._pulse_counter_number + 1}"
            },
        )
