"""Tests for brultech component initialization."""
from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import patch

from custom_components.brultech.config_flow import CONFIG_ENTRY_DATA_SCHEMA
from custom_components.brultech.config_flow import CONFIG_ENTRY_OPTIONS_SCHEMA
from custom_components.brultech.config_flow import yaml_to_config_entry
from custom_components.brultech.const import CONF_MONITORS
from custom_components.brultech.const import DOMAIN
from custom_components.greeneye_monitor import CONFIG_SCHEMA
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import mock_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .common import connect_monitor
from .common import MULTI_MONITOR_CONFIG
from .common import setup_brultech_component_with_config
from .common import SINGLE_MONITOR_CONFIG_POWER_SENSORS
from .common import SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
from .common import SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS
from .common import SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
from .common import SINGLE_MONITOR_SERIAL_NUMBER
from .conftest import assert_current_sensor_registered
from .conftest import assert_energy_sensor_registered
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
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
    )

    normalized_entry_schema = CONFIG_ENTRY_DATA_SCHEMA(
        {CONF_PORT: 7513, CONF_MONITORS: {str(SINGLE_MONITOR_SERIAL_NUMBER): {}}}
    )
    normalized_options_schema = CONFIG_ENTRY_OPTIONS_SCHEMA(
        {CONF_MONITORS: {str(SINGLE_MONITOR_SERIAL_NUMBER): {}}}
    )

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.data == normalized_entry_schema
    assert entry.options == normalized_options_schema


async def test_setup_from_config_entry(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that setting up from a config entry works."""
    normalized_schema = CONFIG_SCHEMA(SINGLE_MONITOR_CONFIG_PULSE_COUNTERS)
    data, options = yaml_to_config_entry(normalized_schema[DOMAIN])
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options=options,
    )

    await hass.config_entries.async_add(config_entry)
    await hass.async_block_till_done()
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)

    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 3 rate",
        "gal",
        "h",
    )


async def test_setup_gets_updates_from_yaml(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup updates the existing config entry when YAML changes."""
    normalized_schema = CONFIG_SCHEMA(SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS)
    data, options = yaml_to_config_entry(normalized_schema[DOMAIN])
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data=data,
        options=options,
    )

    # Patch async_setup so that async_add just adds the config entry
    # This is to simulate the config entry already being present when
    # the component setup is run
    with patch("homeassistant.config_entries.ConfigEntries.async_setup"):
        await hass.config_entries.async_add(config_entry)

    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)

    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 3 rate",
        "gal",
        "h",
    )


async def test_previous_names_remain(hass: HomeAssistant, monitors: AsyncMock) -> None:
    mock_registry(
        hass,
        {
            "sensor.pulse_3": er.RegistryEntry(
                entity_id="sensor.pulse_3",
                unique_id=f"{SINGLE_MONITOR_SERIAL_NUMBER}-pulse-3",
                platform=DOMAIN,
                original_name="pulse_3",
            )
        },
    )

    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)

    pulse_counter = assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        "pulse_3",
        "gal",
        "h",
    )
    assert pulse_counter.name == "pulse_3"


async def test_setup_creates_temperature_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers temperature sensors properly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_TEMPERATURE_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 1",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 2",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 3",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        4,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 4",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        5,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 5",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        6,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 6",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        7,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 7",
    )
    assert_temperature_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        8,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} temperature 8",
    )


async def test_setup_creates_pulse_counter_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers pulse counters properly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_PULSE_COUNTERS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 1 rate",
        "pulses",
        "s",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 2 rate",
        "gal",
        "min",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        3,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 3 rate",
        "gal",
        "h",
    )
    assert_pulse_counter_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        4,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} pulse counter 4 rate",
        "pulses",
        "s",
    )


async def test_setup_creates_power_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers power sensors correctly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_power_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 1",
    )
    assert_power_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 2",
    )


async def test_setup_creates_energy_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers power sensors correctly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_energy_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 1 energy",
    )
    assert_energy_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 2 energy",
    )


async def test_setup_creates_current_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers power sensors correctly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_current_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 1 current",
    )
    assert_current_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        2,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} channel 2 current",
    )


async def test_setup_creates_voltage_sensor_entities(
    hass: HomeAssistant, monitors: AsyncMock
) -> None:
    """Test that component setup registers voltage sensors properly."""
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_VOLTAGE_SENSORS
    )
    await connect_monitor(hass, monitors, SINGLE_MONITOR_SERIAL_NUMBER)
    assert_voltage_sensor_registered(
        hass,
        SINGLE_MONITOR_SERIAL_NUMBER,
        1,
        f"GEM {SINGLE_MONITOR_SERIAL_NUMBER} voltage 1",
    )


async def test_multi_monitor_config(hass: HomeAssistant, monitors: AsyncMock) -> None:
    """Test that component setup registers entities from multiple monitors correctly."""
    assert await setup_brultech_component_with_config(
        hass,
        MULTI_MONITOR_CONFIG,
    )

    await connect_monitor(hass, monitors, 1)
    await connect_monitor(hass, monitors, 2)
    await connect_monitor(hass, monitors, 3)

    assert_temperature_sensor_registered(hass, 1, 1, "GEM 1 temperature 1")
    assert_temperature_sensor_registered(hass, 2, 1, "GEM 2 temperature 1")
    assert_temperature_sensor_registered(hass, 3, 1, "GEM 3 temperature 1")


async def test_setup_and_shutdown(hass: HomeAssistant, monitors: AsyncMock) -> None:
    """Test that the component can set up and shut down cleanly, closing the underlying server on shutdown."""
    monitors.start_server = AsyncMock(return_value=None)
    monitors.close = AsyncMock(return_value=None)
    assert await setup_brultech_component_with_config(
        hass, SINGLE_MONITOR_CONFIG_POWER_SENSORS
    )

    await hass.async_stop()

    assert monitors.close.called
