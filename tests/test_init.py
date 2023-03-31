"""Tests for greeneye_monitor component initialization."""
from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

from custom_components.greeneye_monitor import CONF_MONITORS
from custom_components.greeneye_monitor import CONFIG_SCHEMA
from custom_components.greeneye_monitor import DOMAIN
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .common import connect_monitor
from .common import MULTI_MONITOR_CONFIG
from .common import setup_greeneye_monitor_component_with_config
from .common import SINGLE_MONITOR_CONFIG_POWER_SENSORS
from .common import SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
from .common import SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS
from .common import SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
from .common import SINGLE_MONITOR_SERIAL_NUMBER
from .conftest import assert_power_sensor_registered
from .conftest import assert_pulse_counter_registered
from .conftest import assert_temperature_sensor_registered
from .conftest import assert_voltage_sensor_registered


async def test_setup_succeeds_no_config(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup succeeds if there is no config present in the YAML."""
    assert await async_setup_component(hass, DOMAIN, {})


async def test_setup_creates_config_entry(
    hass: HomeAssistant,
    monitors: AsyncMock,
) -> None:
    """Test that component setup copies the YAML configuration into a config entry."""
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
    )

    normalized_schema = CONFIG_SCHEMA(SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.data == {
        CONF_PORT: normalized_schema[DOMAIN][CONF_PORT],
    }
    assert entry.options == {CONF_MONITORS: normalized_schema[DOMAIN][CONF_MONITORS]}


async def test_setup_from_config_entry(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that setting up from a config entry works."""
    normalized_schema = CONFIG_SCHEMA(SINGLE_MONITOR_CONFIG_PULSE_COUNTERS)
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PORT: normalized_schema[DOMAIN][CONF_PORT]},
        options={CONF_MONITORS: normalized_schema[DOMAIN][CONF_MONITORS]},
    )

    await hass.config_entries.async_add(config_entry)
    await hass.async_block_till_done()
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)

    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        "pulse_3",
        "gal",
        "h",
    )


async def test_setup_gets_updates_from_yaml(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup updates the existing config entry when YAML changes."""
    normalized_schema = CONFIG_SCHEMA(SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS)
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={CONF_PORT: normalized_schema[DOMAIN][CONF_PORT]},
        options={CONF_MONITORS: normalized_schema[DOMAIN][CONF_MONITORS]},
    )

    # Patch async_setup so that async_add just adds the config entry
    # This is to simulate the config entry already being present when
    # the component setup is run
    with patch("homeassistant.config_entries.ConfigEntries.async_setup"):
        await hass.config_entries.async_add(config_entry)

    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)

    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        "pulse_3",
        "gal",
        "h",
    )


async def test_setup_creates_temperature_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers temperature sensors properly."""
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-1",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-2",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-3",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        4,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-4",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        5,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-5",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        6,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-6",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        7,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-7",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        8,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-temp-8",
    )


async def test_setup_creates_pulse_counter_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers pulse counters properly."""
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-pulse-1",
        "pulses",
        "s",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-pulse-2",
        "gal",
        "min",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-pulse-3",
        "gal",
        "h",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        4,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-pulse-4",
        "pulses",
        "s",
    )


async def test_setup_creates_power_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers power sensors correctly."""
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_power_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-current-1",
    )
    assert_power_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-current-2",
    )


async def test_setup_creates_voltage_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers voltage sensors properly."""
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_voltage_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"greeneye-{SINGLE_MONITOR_SERIAL_NUMBER}-volts-1",
    )


async def test_multi_monitor_config(hass: HomeAssistant, monitors: AsyncMock) -> None:
    """Test that component setup registers entities from multiple monitors correctly."""
    assert await setup_greeneye_monitor_component_with_config(
        hass,
        MULTI_MONITOR_CONFIG,
    )

    await connect_monitor(hass, monitors, 1)
    await connect_monitor(hass, monitors, 2)
    await connect_monitor(hass, monitors, 3)

    assert_temperature_sensor_registered(hass, 1, 1, "greeneye-1-temp-1")
    assert_temperature_sensor_registered(hass, 2, 1, "greeneye-2-temp-1")
    assert_temperature_sensor_registered(hass, 3, 1, "greeneye-3-temp-1")


async def test_setup_and_shutdown(hass: HomeAssistant, monitors: AsyncMock) -> None:
    """Test that the component can set up and shut down cleanly, closing the underlying server on shutdown."""
    monitors.start_server = AsyncMock(return_value=None)
    monitors.close = AsyncMock(return_value=None)
    assert await setup_greeneye_monitor_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )

    await hass.async_stop()

    assert monitors.close.called
