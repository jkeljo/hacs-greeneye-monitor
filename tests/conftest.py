"""Common fixtures for testing greeneye_monitor."""
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from custom_components.greeneye_monitor import DOMAIN
from custom_components.greeneye_monitor.sensor import GEMSensor
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.const import UnitOfElectricPotential
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_registry import async_get as get_entity_registry
from homeassistant.helpers.entity_registry import RegistryEntry
from homeassistant.util import slugify

from .common import add_listeners


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass, enable_custom_integrations):
    """Allow custom integrations to load"""
    yield


@pytest.fixture(autouse=True)
def enable_all_entities(monkeypatch):
    monkeypatch.setattr(GEMSensor, "_attr_entity_registry_enabled_default", True)


def assert_sensor_state(
    hass: HomeAssistant,
    entity_id: str,
    expected_state: str,
    attributes: dict[str, Any] = {},
) -> None:
    """Assert that the given entity has the expected state and at least the provided attributes."""
    state = hass.states.get(entity_id)
    assert state
    actual_state = state.state
    assert actual_state == expected_state
    for key, value in attributes.items():
        assert key in state.attributes
        assert state.attributes[key] == value


def assert_temperature_sensor_registered(
    hass: HomeAssistant,
    serial_number: int,
    number: int,
    name: str,
):
    """Assert that a temperature sensor entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "temperature", "temp", number, name
    )
    assert sensor.original_device_class is SensorDeviceClass.TEMPERATURE


def assert_pulse_counter_registered(
    hass: HomeAssistant,
    serial_number: int,
    number: int,
    name: str,
    quantity: str,
    per_time: str,
):
    """Assert that a pulse counter entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "pulse counter", "pulse", number, name
    )
    assert sensor.unit_of_measurement == f"{quantity}/{per_time}"


def assert_power_sensor_registered(
    hass: HomeAssistant, serial_number: int, number: int, name: str
) -> None:
    """Assert that a power sensor entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "channel", "current", number, name
    )
    assert sensor.unit_of_measurement == UnitOfPower.WATT
    assert sensor.original_device_class is SensorDeviceClass.POWER


def assert_energy_sensor_registered(
    hass: HomeAssistant, serial_number: int, number: int, name: str
) -> None:
    """Assert that a power sensor entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "channel", "energy", number, name
    )
    assert sensor.unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert sensor.original_device_class is SensorDeviceClass.ENERGY


def assert_current_sensor_registered(
    hass: HomeAssistant, serial_number: int, number: int, name: str
) -> None:
    """Assert that a power sensor entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "channel", "amps", number, name
    )
    assert sensor.unit_of_measurement == UnitOfElectricCurrent.AMPERE
    assert sensor.original_device_class is SensorDeviceClass.CURRENT


def assert_voltage_sensor_registered(
    hass: HomeAssistant, serial_number: int, number: int, name: str
) -> None:
    """Assert that a voltage sensor entity was registered properly."""
    sensor = assert_sensor_registered(
        hass, serial_number, "voltage", "volts", number, name
    )
    assert sensor.unit_of_measurement == UnitOfElectricPotential.VOLT
    assert sensor.original_device_class is SensorDeviceClass.VOLTAGE


def assert_sensor_registered(
    hass: HomeAssistant,
    serial_number: int,
    device_type: str,
    sensor_type: str,
    number: int,
    name: str,
) -> RegistryEntry:
    """Assert that a sensor entity of a given type was registered properly."""
    registry = get_entity_registry(hass)
    unique_id = f"{serial_number}-{sensor_type}-{number}"

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None

    sensor = registry.async_get(entity_id)
    assert sensor
    assert sensor.unique_id == unique_id
    assert sensor.entity_id == f"sensor.{slugify(name)}"

    device_registry = dr.async_get(hass)
    assert sensor.device_id is not None
    device = device_registry.async_get(sensor.device_id)
    assert device is not None
    assert device.name == f"GEM {serial_number} {device_type} {number}"

    assert device.via_device_id is not None
    via_device = device_registry.async_get(device.via_device_id)
    assert via_device is not None
    assert via_device.name == f"GEM {serial_number}"
    assert via_device.manufacturer == "Brultech"

    return sensor


@pytest.fixture
def monitors() -> AsyncMock:
    """Provide a mock greeneye.Monitors object that has listeners and can add new monitors."""
    with patch("greeneye.Monitors", new=AsyncMock) as mock_monitors:
        add_listeners(mock_monitors)
        mock_monitors.monitors = {}

        def add_monitor(monitor: MagicMock) -> None:
            """Add the given mock monitor as a monitor with the given serial number, notifying any listeners on the Monitors object."""
            serial_number = monitor.serial_number
            mock_monitors.monitors[serial_number] = monitor
            mock_monitors.notify_all_listeners(monitor)

        mock_monitors.add_monitor = add_monitor
        yield mock_monitors
