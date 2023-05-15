"""Support for monitoring a Brultech energy monitor."""
from __future__ import annotations

import logging

import greeneye
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.const import Platform
from homeassistant.core import Event
from homeassistant.core import HomeAssistant

from .const import CONF_SEND_PACKET_DELAY
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Setup the Brultech component from a config entry."""
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
        hass.config_entries.async_forward_entry_setups(config_entry, [Platform.SENSOR])
    )

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the Brultech config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, Platform.SENSOR)

    monitors = hass.data.pop(DOMAIN)
    await monitors.close()
    return True
