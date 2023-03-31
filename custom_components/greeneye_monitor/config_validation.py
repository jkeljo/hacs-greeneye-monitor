"""Custom config validation helpers."""
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass


def serialNumber(value: Any) -> int:
    return vol.All(
        cv.string,
        vol.Length(
            min=8,
            max=8,
            msg=(
                "GEM serial number must be specified as an 8-character "
                "string (including leading zeroes)."
            ),
        ),
        vol.Coerce(int),
    )(value)


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
