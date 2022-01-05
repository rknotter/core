"""Platform for innova ariconditioner integration."""
from __future__ import annotations

# from configparser import ConfigParser
import logging

import voluptuous as vol

# from homeassistant.components import climate
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
HVAC_MODES = [
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
]
FAN_MODES = ["Auto", SPEED_LOW, "Low", SPEED_MEDIUM, "Medium", SPEED_HIGH, "High"]
SWING_MODES = ["Stop", "Swing"]


_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "Innova Climate"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Assign configuration variables."""
    """The configuration check takes care they are present."""
    host = config[CONF_HOST]
    name = config[CONF_NAME]
    hvac_modes = HVAC_MODES
    fan_modes = FAN_MODES
    swing_modes = SWING_MODES
    unit = hass.config.units.temperature_unit

    _LOGGER.info("Adding Innova climate device")

    """Add devices"""
    add_entities([innova(host, name, unit, hvac_modes, fan_modes, swing_modes)])


class innova(ClimateEntity):
    """Representation of an Innova Climate Device."""

    def __init__(self, host, name, unit, hvac_modes, fan_modes, swing_modes):
        """Initialize an Innova Climate Device."""
        _LOGGER.info("Initialize the Innova climate device")
        self._name = name
        self._host = host
        self._attr_hvac_mode = None
        self._attr_fan_mode = None
        self._attr_swing_mode = None

        self._attr_fan_modes = fan_modes
        self._attr_swing_modes = swing_modes
        self._attr_hvac_modes = hvac_modes
        self._attr_temperature_unit = unit
        self._attr_unique_id = "climate." + name

        self._attr_supported_features = SUPPORT_FLAGS

        _LOGGER.info(host)
        _LOGGER.info(name)

    @property
    def name(self) -> str:
        """Return the display name of this climate device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this climate device."""
        return self._unique_id
