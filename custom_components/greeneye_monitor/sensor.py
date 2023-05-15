"""Support for the sensors in a GreenEye Monitor."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from typing import cast

import greeneye
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.const import CONF_TEMPERATURE_UNIT
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.const import UnitOfElectricPotential
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import CONF_COUNTED_QUANTITY
from .const import CONF_COUNTED_QUANTITY_PER_PULSE
from .const import CONF_DEVICE_CLASS
from .const import CONF_MONITORS
from .const import CONF_NET_METERING
from .const import CONF_NUMBER
from .const import CONF_PULSE_COUNTERS
from .const import CONF_SERIAL_NUMBER
from .const import CONF_TIME_UNIT
from .const import DATA_GREENEYE_MONITOR
from .const import DEFAULT_UPDATE_INTERVAL
from .const import DEVICE_TYPE_CURRENT_TRANSFORMER
from .const import DEVICE_TYPE_PULSE_COUNTER
from .const import DEVICE_TYPE_TEMPERATURE_SENSOR
from .const import DEVICE_TYPE_VOLTAGE_SENSOR
from .const import DOMAIN
from .const import get_monitor_type_long_name
from .const import get_monitor_type_short_name

DATA_PULSES = "pulses"
DATA_WATT_SECONDS = "watt_seconds"

COUNTER_ICON = "mdi:counter"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up GEM sensors from the config entry"""
    entry_id = config_entry.entry_id

    async def on_new_monitor(monitor: greeneye.monitor.Monitor) -> None:
        config_entry = hass.config_entries.async_get_entry(entry_id)
        monitor_configs = config_entry.data[CONF_MONITORS]
        monitor_options = config_entry.options[CONF_MONITORS]

        serial_number = monitor.serial_number
        monitor_config = next(
            filter(
                lambda config: config[CONF_SERIAL_NUMBER] == serial_number,
                monitor_configs,
            ),
            None,
        )
        monitor_option = next(
            filter(
                lambda option: option[CONF_SERIAL_NUMBER] == serial_number,
                monitor_options,
            ),
            None,
        )

        if monitor_config is not None and monitor_option is not None:
            entities: list[GEMSensor] = []

            device_registry = dr.async_get(hass)
            monitor_type_short_name = get_monitor_type_short_name(monitor)
            monitor_type_long_name = get_monitor_type_long_name(monitor)
            device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={(DOMAIN, f"{monitor.serial_number}")},
                manufacturer="Brultech",
                name=f"{monitor_type_short_name} {monitor.serial_number}",
                model=monitor_type_long_name,
            )

            net_metering = set(monitor_config[CONF_NET_METERING])
            for channel in monitor.channels:
                channel_net_metered = str(channel.number) in net_metering
                entities.append(
                    PowerSensor(
                        monitor,
                        channel,
                        channel_net_metered,
                    )
                )
                entities.append(
                    CurrentSensor(
                        monitor,
                        channel,
                    )
                )
                entities.append(
                    EnergySensor(
                        monitor,
                        channel,
                        channel_net_metered,
                    )
                )

            pulse_counter_configs = monitor_config[CONF_PULSE_COUNTERS]
            pulse_counter_options = monitor_option[CONF_PULSE_COUNTERS]
            for pulse_counter in monitor.pulse_counters:
                config = next(
                    filter(
                        lambda config: config[CONF_NUMBER] == pulse_counter.number,
                        pulse_counter_configs,
                    ),
                    None,
                )
                options = next(
                    filter(
                        lambda option: option[CONF_NUMBER] == pulse_counter.number,
                        pulse_counter_options,
                    ),
                    None,
                )
                if config and options:
                    entities.append(
                        PulseRateSensor(
                            monitor,
                            pulse_counter,
                            config[CONF_COUNTED_QUANTITY],
                            options[CONF_TIME_UNIT],
                            config[CONF_COUNTED_QUANTITY_PER_PULSE],
                        )
                    )
                    entities.append(
                        PulseCountSensor(
                            monitor,
                            pulse_counter,
                            config[CONF_DEVICE_CLASS],
                            config[CONF_COUNTED_QUANTITY],
                            config[CONF_COUNTED_QUANTITY_PER_PULSE],
                        )
                    )

            temperature_unit = monitor_config.get(CONF_TEMPERATURE_UNIT)
            for temperature_sensor in monitor.temperature_sensors:
                if temperature_unit:
                    entities.append(
                        TemperatureSensor(
                            monitor,
                            temperature_sensor,
                            temperature_unit,
                        )
                    )

            if monitor.voltage_sensor:
                entities.append(VoltageSensor(monitor))

            async_add_entities(entities)

            _LOGGER.info("Set up new monitor %d", monitor.serial_number)
        else:
            _LOGGER.info("Triggering config flow for %d", monitor.serial_number)
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={
                    "source": SOURCE_INTEGRATION_DISCOVERY,
                    "serial_number": monitor.serial_number,
                },
            )

    monitors: greeneye.Monitors = hass.data[DATA_GREENEYE_MONITOR]
    monitors.add_listener(on_new_monitor)
    for monitor in monitors.monitors.values():
        await on_new_monitor(monitor)

    return True


UnderlyingSensorType = (
    greeneye.monitor.Channel
    | greeneye.monitor.PulseCounter
    | greeneye.monitor.TemperatureSensor
    | greeneye.monitor.VoltageSensor
)


class GEMSensor(SensorEntity):
    """Base class for GreenEye Monitor sensors."""

    _attr_entity_registry_enabled_default = False
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        device_type: str,
        sensor_type: str,
        sensor: UnderlyingSensorType,
        number: int,
        update_interval: timedelta | None = None,
    ) -> None:
        """Construct the entity."""
        self._monitor = monitor
        self._monitor_serial_number = self._monitor.serial_number
        self._device_type = device_type
        self._sensor_type = sensor_type
        self._sensor: UnderlyingSensorType = sensor
        self._number = number
        self._attr_unique_id = (
            f"{self._monitor_serial_number}-{self._sensor_type}-{self._number + 1}"
        )
        if update_interval:
            self._update = Throttle(update_interval)(self.async_write_ha_state)
        else:
            self._update = self.async_write_ha_state

    @property
    def device_info(self) -> DeviceInfo | None:
        monitor_type_short_name = get_monitor_type_short_name(self._monitor)
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    cast(
                        str,
                        f"{self._monitor_serial_number}-{self._device_type}-{self._number + 1}",
                    ),
                )
            },
            name=f"{monitor_type_short_name} {self._monitor_serial_number} {self._device_type} {self._number + 1}",
            via_device=(DOMAIN, f"{self._monitor.serial_number}"),
        )

    async def async_added_to_hass(self) -> None:
        """Wait for and connect to the sensor."""
        self._sensor.add_listener(self._update)

    async def async_will_remove_from_hass(self) -> None:
        """Remove listener from the sensor."""
        if self._sensor:
            self._sensor.remove_listener(self._update)


class PowerSensor(GEMSensor):
    """Entity showing power usage on one channel of the monitor."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.Channel,
        net_metering: bool,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor, DEVICE_TYPE_CURRENT_TRANSFORMER, "current", sensor, sensor.number
        )
        self._sensor: greeneye.monitor.Channel = self._sensor
        self._net_metering = net_metering

    @property
    def native_value(self) -> float | None:
        """Return the current number of watts being used by the channel."""
        return self._sensor.watts

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return total wattseconds in the state dictionary."""
        if self._net_metering:
            watt_seconds = self._sensor.polarized_watt_seconds
        else:
            watt_seconds = self._sensor.absolute_watt_seconds

        return {DATA_WATT_SECONDS: watt_seconds}


class CurrentSensor(GEMSensor):
    """Entity showing current on one channel of the monitor."""

    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_name = "current"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.Channel,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor, DEVICE_TYPE_CURRENT_TRANSFORMER, "amps", sensor, sensor.number
        )
        self._sensor: greeneye.monitor.Channel = self._sensor

    @property
    def native_value(self) -> float | None:
        """Return the current number of watts being used by the channel."""
        return self._sensor.amps


class EnergySensor(GEMSensor):
    """Entity showing energy usage on one channel of the monitor."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_name = "energy"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.Channel,
        net_metering: bool,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor,
            DEVICE_TYPE_CURRENT_TRANSFORMER,
            "energy",
            sensor,
            sensor.number,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self._sensor: greeneye.monitor.Channel = self._sensor
        self._net_metering = net_metering

    @property
    def native_value(self) -> float | None:
        """Return the total number of kilowatt hours measured by this channel."""
        if self._net_metering:
            return self._sensor.polarized_kilowatt_hours
        else:
            return self._sensor.absolute_kilowatt_hours


class PulseRateSensor(GEMSensor):
    """Entity showing rate of change in one pulse counter of the monitor."""

    _attr_icon = COUNTER_ICON
    _attr_name = "rate"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.PulseCounter,
        counted_quantity: str,
        time_unit: str,
        counted_quantity_per_pulse: float,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor, DEVICE_TYPE_PULSE_COUNTER, "pulse", sensor, sensor.number
        )
        self._sensor: greeneye.monitor.PulseCounter = self._sensor
        self._counted_quantity_per_pulse = counted_quantity_per_pulse
        self._time_unit = time_unit
        self._attr_native_unit_of_measurement = f"{counted_quantity}/{self._time_unit}"

    @property
    def native_value(self) -> float | None:
        """Return the current rate of change for the given pulse counter."""
        if self._sensor.pulses_per_second is None:
            return None

        result = (
            self._sensor.pulses_per_second
            * self._counted_quantity_per_pulse
            * self._seconds_per_time_unit
        )
        return result

    @property
    def _seconds_per_time_unit(self) -> int:
        """Return the number of seconds in the given display time unit."""
        if self._time_unit == UnitOfTime.SECONDS:
            return 1
        if self._time_unit == UnitOfTime.MINUTES:
            return 60
        if self._time_unit == UnitOfTime.HOURS:
            return 3600

        # Config schema should have ensured it is one of the above values
        raise RuntimeError(
            f"Invalid value for time unit: {self._time_unit}. Expected one of"
            f" {UnitOfTime.SECONDS}, {UnitOfTime.MINUTES}, or {UnitOfTime.HOURS}"
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return total pulses in the data dictionary."""
        return {DATA_PULSES: self._sensor.pulses}


class PulseCountSensor(GEMSensor):
    """Entity showing pulse counts."""

    _attr_entity_registry_enabled_default = True
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.PulseCounter,
        device_class: SensorDeviceClass | None,
        counted_quantity: str,
        counted_quantity_per_pulse: float,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor,
            DEVICE_TYPE_PULSE_COUNTER,
            "count",
            sensor,
            sensor.number,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self._sensor: greeneye.monitor.PulseCounter = self._sensor
        self._counted_quantity_per_pulse = counted_quantity_per_pulse
        self._attr_native_unit_of_measurement = counted_quantity
        self._attr_device_class = device_class

    @property
    def native_value(self) -> float | None:
        if self._sensor.pulses is None:
            return None

        return self._sensor.pulses * self._counted_quantity_per_pulse


class TemperatureSensor(GEMSensor):
    """Entity showing temperature from one temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        monitor: greeneye.monitor.Monitor,
        sensor: greeneye.monitor.TemperatureSensor,
        unit: str,
    ) -> None:
        """Construct the entity."""
        super().__init__(
            monitor, DEVICE_TYPE_TEMPERATURE_SENSOR, "temp", sensor, sensor.number
        )
        self._sensor: greeneye.monitor.TemperatureSensor = self._sensor
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float | None:
        """Return the current temperature being reported by this sensor."""
        return self._sensor.temperature


class VoltageSensor(GEMSensor):
    """Entity showing voltage."""

    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, monitor: greeneye.monitor.Monitor) -> None:
        """Construct the entity."""
        super().__init__(
            monitor, DEVICE_TYPE_VOLTAGE_SENSOR, "volts", monitor.voltage_sensor, 0
        )
        self._sensor: greeneye.monitor.VoltageSensor = self._sensor

    @property
    def native_value(self) -> float | None:
        """Return the current voltage being reported by this sensor."""
        return self._sensor.voltage
