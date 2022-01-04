"""Platform for innova ariconditioner integration."""
from __future__ import annotations

# from configparser import ConfigParser
import logging

import voluptuous as vol

# from homeassistant.components import climate
from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# from homeassistant.core import HomeAssistant

""" from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
) """
# from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM

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

    _LOGGER.info("Adding Innova climate device")
    _LOGGER.info(host)
    _LOGGER.info(name)
    """Add devices"""
    add_entities([innova(host, name)])


class innova(ClimateEntity):
    """Representation of an Innova Climate Entity."""

    def __init__(
        self,
        name,
        host,
    ):
        """Initialize an Innova Climate Entity."""
        _LOGGER.info("Initialize the GREE climate device")
        self._name = name
        self._host = host

    @property
    def name(self) -> str:
        """Return the display name of this climate device."""
        return self._name
