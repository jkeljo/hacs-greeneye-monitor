"""Support for configuration entities that are numbers."""
import logging

import greeneye
from homeassistant.components.number import NumberEntity
from homeassistant.components.number import NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MONITORS
from .const import CONF_SERIAL_NUMBER
from .const import DEVICE_TYPE_CURRENT_TRANSFORMER
from .const import DOMAIN
from .const import make_device_info


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up Brultech energy monitor sensors from the config entry"""
    entry_id = config_entry.entry_id

    async def on_new_monitor(monitor: greeneye.monitor.Monitor) -> None:
        config_entry = hass.config_entries.async_get_entry(entry_id)
        monitor_configs = config_entry.data[CONF_MONITORS]

        serial_number = monitor.serial_number
        monitor_config = next(
            filter(
                lambda config: config[CONF_SERIAL_NUMBER] == serial_number,
                monitor_configs,
            ),
            None,
        )

        if monitor_config is not None:
            entities: list[Entity] = []

            for channel in monitor.channels:
                if channel.ct_type is not None:
                    entities.append(ChannelTypeEntity(monitor, channel))
                if channel.ct_range is not None:
                    entities.append(ChannelRangeEntity(monitor, channel))

            if monitor.control is not None:
                entities.append(PacketIntervalEntity(monitor))

            async_add_entities(entities)

            _LOGGER.info(
                "Added configuration entities for new monitor %d", monitor.serial_number
            )

    monitors: greeneye.Monitors = hass.data[DOMAIN]
    monitors.add_listener(on_new_monitor)
    for monitor in monitors.monitors.values():
        await on_new_monitor(monitor)

    return True


class ChannelTypeEntity(NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_name = "CT type"
    _attr_native_step = 1.0
    _attr_native_min_value = 0
    _attr_native_max_value = 255
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, monitor: greeneye.monitor.Monitor, channel: greeneye.monitor.Channel
    ) -> None:
        super().__init__()
        self._monitor = monitor
        self._channel = channel
        self._attr_unique_id = (
            f"{self._monitor.serial_number}-ct_type-{self._channel.number + 1}"
        )
        assert self._channel.ct_type is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        return make_device_info(
            self._monitor, DEVICE_TYPE_CURRENT_TRANSFORMER, self._channel.number
        )

    @property
    def native_value(self) -> float | None:
        return self._channel.ct_type

    async def async_set_native_value(self, value: float) -> None:
        await self._channel.set_ct_type(int(value))

    async def async_added_to_hass(self) -> None:
        """Wait for and connect to the sensor."""
        self._channel.add_listener(self._update)

    async def async_will_remove_from_hass(self) -> None:
        """Remove listener from the sensor."""
        if self._channel:
            self._channel.remove_listener(self._update)

    def _update(self) -> None:
        self.async_write_ha_state()


class ChannelRangeEntity(NumberEntity):
    _attr_mode = NumberMode.BOX
    _attr_name = "CT range"
    _attr_native_step = 1.0
    _attr_native_min_value = 0
    _attr_native_max_value = 15
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, monitor: greeneye.monitor.Monitor, channel: greeneye.monitor.Channel
    ) -> None:
        super().__init__()
        self._monitor = monitor
        self._channel = channel
        self._attr_unique_id = (
            f"{self._monitor.serial_number}-ct_range-{self._channel.number + 1}"
        )
        assert self._channel.ct_range is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        return make_device_info(
            self._monitor, DEVICE_TYPE_CURRENT_TRANSFORMER, self._channel.number
        )

    @property
    def native_value(self) -> float | None:
        return self._channel.ct_range

    async def async_set_native_value(self, value: float) -> None:
        await self._channel.set_ct_range(int(value))

    async def async_added_to_hass(self) -> None:
        """Wait for and connect to the sensor."""
        self._channel.add_listener(self._update)

    async def async_will_remove_from_hass(self) -> None:
        """Remove listener from the sensor."""
        if self._channel:
            self._channel.remove_listener(self._update)

    def _update(self) -> None:
        self.async_write_ha_state()


class PacketIntervalEntity(NumberEntity):
    _attr_mode = NumberMode.SLIDER
    _attr_name = "packet interval"
    _attr_native_step = 1.0
    _attr_native_min_value = 1
    _attr_native_max_value = 255
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = True
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, monitor: greeneye.monitor.Monitor) -> None:
        super().__init__()
        self._monitor = monitor
        self._attr_unique_id = f"{monitor.serial_number}-packet_send_interval"
        assert self._monitor.control is not None

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(identifiers={(DOMAIN, f"{self._monitor.serial_number}")})

    @property
    def native_value(self) -> float | None:
        return self._monitor.packet_send_interval.total_seconds()

    async def async_set_native_value(self, value: float) -> None:
        await self._monitor.set_packet_send_interval(seconds=int(value))

    async def async_added_to_hass(self) -> None:
        """Wait for and connect to the sensor."""
        self._monitor.add_listener(self._update)

    async def async_will_remove_from_hass(self) -> None:
        """Remove listener from the sensor."""
        if self._monitor:
            self._monitor.remove_listener(self._update)

    def _update(self) -> None:
        self.async_write_ha_state()
