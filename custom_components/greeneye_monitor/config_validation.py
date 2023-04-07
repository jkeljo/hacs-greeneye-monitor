"""Custom config validation helpers."""
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass


serialNumber = vol.All(
    str,
    vol.Length(
        min=8,
        max=8,
        msg=(
            "GEM serial number must be specified as an 8-character "
            "string (including leading zeroes)."
        ),
    ),
    vol.Coerce(int),
)

serialNumberStr = vol.All(
    str, vol.Length(min=1, max=8), vol.Coerce(int), vol.Coerce(str)
)


def temperatureSensorNumber(value: Any) -> int:
    return vol.Range(1, 8)(value)


def pulseCounterNumber(value: Any) -> int:
    return vol.Range(1, 4)(value)


def channelNumber(value: Any) -> int:
    return vol.Range(1, 48)(value)


def deviceClass(value: Any) -> SensorDeviceClass | None:
    if value is None:
        return None
    value = cv.string(value)
    return SensorDeviceClass(value)
