"""Diagnostics support for GreenEye Monitor."""
from datetime import datetime
from typing import Any

from greeneye import Monitors
from greeneye.monitor import Aux
from greeneye.monitor import Channel
from greeneye.monitor import GemSettings
from greeneye.monitor import Monitor
from greeneye.monitor import PulseCounter
from greeneye.monitor import TemperatureSensor
from greeneye.monitor import VoltageSensor
from homeassistant.components.sensor import SensorEntity
from homeassistant.config import async_hass_config_yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core import split_entity_id
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import (
    DATA_INSTANCES as DATA_ENTITY_COMPONENTS,
)
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity_registry import RegistryEntry as EntityRegistryEntry
from homeassistant.helpers.issue_registry import async_get as async_get_issue_registry

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    config = await async_hass_config_yaml(hass)
    monitors: Monitors = hass.data[DOMAIN]

    return {
        "current_time": datetime.now().isoformat(),
        "yaml": config.get(DOMAIN),
        "config_entry": entry.as_dict(),
        "monitors": {
            number: monitor_as_dict(monitor)
            for number, monitor in monitors.monitors.items()
        },
        "entities": entities_as_dict(hass),
        "issues": issues_as_list(hass),
        "registries": registries_as_dict(hass),
    }


def entities_as_dict(hass: HomeAssistant) -> dict[str, Any]:
    er = async_get_entity_registry(hass)
    return {
        registry_entry.entity_id: {
            "registry": registry_entry.as_partial_dict,
            "entity": entity_as_dict(_get_entity(hass, registry_entry)),
            "state": hass.states.get(registry_entry.entity_id),
        }
        for registry_entry in er.entities.values()
        if registry_entry.platform == DOMAIN
    }


def _get_entity(
    hass: HomeAssistant, registry_entry: EntityRegistryEntry
) -> Entity | None:
    domain, _ = split_entity_id(registry_entry.entity_id)
    component: EntityComponent = hass.data[DATA_ENTITY_COMPONENTS][domain]
    entity = component.get_entity(registry_entry.entity_id)
    return entity


def entity_as_dict(entity: Entity | None) -> dict[str, Any] | None:
    if not entity:
        return None
    if isinstance(entity, SensorEntity):
        return sensor_entity_as_dict(entity)
    return base_entity_as_dict(entity)


def sensor_entity_as_dict(entity: SensorEntity) -> dict[str, Any]:
    return {
        **base_entity_as_dict(entity),
        "native_unit_of_measurement": entity.native_unit_of_measurement,
        "state_class": entity.state_class,
        "native_value": entity.native_value,
        "last_reset": entity.last_reset,
    }


def base_entity_as_dict(entity: Entity) -> dict[str, Any]:
    return {
        "type": type(entity).__name__,
        "id": entity.entity_id,
        "unique_id": entity.unique_id,
        "name": entity.name,
        "entity_registry_enabled_default": entity.entity_registry_enabled_default,
        "has_entity_name": entity.has_entity_name,
        "should_poll": entity.should_poll,
        "device_class": entity.device_class,
        "extra_state_attributes": entity.extra_state_attributes,
        "icon": entity.icon,
        "use_device_name": entity.use_device_name,
        "platform_domain": entity.platform.domain,  # TODO: Remove
    }


def registries_as_dict(hass: HomeAssistant) -> dict[str, Any]:
    dr = async_get_device_registry(hass)
    er = async_get_entity_registry(hass)
    device_ids = {
        entity.device_id for entity in er.entities.values() if entity.platform == DOMAIN
    }

    return {
        "devices": {
            id: device.dict_repr
            for id, device in dr.devices.items()
            if device.id in device_ids
        },
        "deleted_entities": [
            {
                "entity_id": deleted.entity_id,
                "unique_id": deleted.unique_id,
                "platform": deleted.platform,
                "config_entry_id": deleted.config_entry_id,
                "domain": deleted.domain,
                "id": deleted.id,
                "orphaned_timestamp": deleted.orphaned_timestamp,
            }
            for deleted in er.deleted_entities.values()
            if deleted.platform == DOMAIN
        ],
    }


def issues_as_list(hass: HomeAssistant) -> list[dict[str, Any]]:
    ir = async_get_issue_registry(hass)
    return [
        issue.to_json()
        for (domain, _), issue in ir.issues.items()
        if domain == DOMAIN and issue.active
    ]


def monitor_as_dict(monitor: Monitor) -> dict[str, Any]:
    return {
        "serial_number": monitor.serial_number,
        "packet_format": monitor.packet_format,
        "packet_send_interval": monitor.packet_send_interval,
        "settings": settings_as_dict(monitor.settings),
        "aux": [aux_as_dict(aux) for aux in monitor.aux],
        "channels": [channel_as_dict(channel) for channel in monitor.channels],
        "pulse_counters": [
            pulse_counter_as_dict(pulse_counter)
            for pulse_counter in monitor.pulse_counters
        ],
        "temperature_sensors": [
            temperature_sensor_as_dict(temperature_sensor)
            for temperature_sensor in monitor.temperature_sensors
        ],
        "voltage_sensor": voltage_sensor_as_dict(monitor.voltage_sensor),
        "listeners": len(monitor._listeners),
    }


def aux_as_dict(aux: Channel | Aux) -> dict[str, Any]:
    match aux:
        case Channel():
            return channel_as_dict(aux)
        case Aux():
            return {
                "channel": channel_as_dict(aux.channel),
                "pulse_counter": pulse_counter_as_dict(aux.pulse_counter),
            }


def channel_as_dict(channel: Channel) -> dict[str, Any]:
    return {
        "number": channel.number,
        "ct_type": channel.ct_type,
        "ct_range": channel.ct_range,
        "is_aux": channel.is_aux,
        "net_metering": channel.net_metering,
        "timestamp": channel.timestamp.isoformat() if channel.timestamp else None,
        "seconds": channel.seconds,
        "amps": channel.amps,
        "absolute_watt_seconds": channel.absolute_watt_seconds,
        "polarized_watt_seconds": channel.polarized_watt_seconds,
        "watts": channel.watts,
        "listeners": len(channel._listeners),
    }


def pulse_counter_as_dict(pulse_counter: PulseCounter) -> dict[str, Any]:
    return {
        "number": pulse_counter.number,
        "pulses": pulse_counter.pulses,
        "pulses_per_second": pulse_counter.pulses_per_second,
        "seconds": pulse_counter.seconds,
        "is_aux": pulse_counter.is_aux,
        "listeners": len(pulse_counter._listeners),
    }


def settings_as_dict(settings: GemSettings | None) -> dict[str, Any] | None:
    return (
        {
            "num_channels": settings.num_channels,
            "channel_net_metering": settings.channel_net_metering,
            "ct_ranges": settings.ct_ranges,
            "ct_types": settings.ct_types,
            "packet_format": settings.packet_format,
            "packet_send_interval": settings.packet_send_interval,
            "temperature_unit": settings.temperature_unit,
        }
        if settings
        else None
    )


def temperature_sensor_as_dict(temperature_sensor: TemperatureSensor) -> dict[str, Any]:
    return {
        "number": temperature_sensor.number,
        "temperature": temperature_sensor.temperature,
        "unit": temperature_sensor.unit,
        "listeners": len(temperature_sensor._listeners),
    }


def voltage_sensor_as_dict(voltage_sensor: VoltageSensor) -> dict[str, Any]:
    return {
        "voltage": voltage_sensor.voltage,
        "listeners": len(voltage_sensor._listeners),
    }
