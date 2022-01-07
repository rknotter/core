"""Platform for innova ariconditioner integration."""
from __future__ import annotations

# import asyncio
import json

# from configparser import ConfigParser
import logging

import requests

# import async_timeout
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
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# from voluptuous.error import Error


SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
HVAC_MODES = [
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
]
FAN_MODES = ["Auto", SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
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
        _LOGGER.info(
            "Initialize the Innova climate device '" + name + "' at address: " + host
        )
        self._name = name
        self._host = host
        self._unique_id = "climate." + name
        self._attr_hvac_mode = None
        self._attr_fan_mode = None
        self._attr_swing_mode = None
        self._attr_target_temperature = None
        self._attr_current_temperature = None
        self._attr_target_temperature_high = 25
        self._attr_target_temperature_low = 18
        self._attr_target_temperature_step = 1

        self._attr_fan_modes = fan_modes
        self._attr_swing_modes = swing_modes
        self._attr_hvac_modes = hvac_modes
        self._attr_temperature_unit = unit

        self._attr_supported_features = SUPPORT_FLAGS

        self.is_available = False
        self.NeedToSend = False

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self) -> str:
        """Return the display name of this climate device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique id of this climate device."""
        return self._unique_id

    @property
    def hvac_mode(self):
        """Return current operation."""
        return self._attr_hvac_mode

    @property
    def swing_mode(self):
        """Return current swing mode."""
        return self._attr_swing_mode

    @property
    def available(self):
        """Return if the device is available for communication."""
        return self.is_available

    async def async_update(self):
        """Update HA state from device."""
        _LOGGER.info("Innova update()")
        await self.SyncState(self.NeedToSend)
        return

    async def SyncState(self, NeedToSend):
        """Fetch current settings from climate device."""
        _LOGGER.info("Starting SyncState")

        """Initialize the receivedJsonPayload variable (for return)"""
        receivedJsonPayload = ""
        if not NeedToSend:
            url = "http://" + self._host + "/api/v/1/status"
            _LOGGER.info("Getting information from: " + url)

            try:
                r = await self.hass.async_add_executor_job(requests.get, url)
                receivedJsonPayload = json.loads(r.content)

                _LOGGER.info(receivedJsonPayload)
                if int(receivedJsonPayload["RESULT"]["ps"]) == 0:
                    self._attr_hvac_mode = HVAC_MODE_OFF

                self._attr_target_temperature = int(receivedJsonPayload["RESULT"]["sp"])
                _LOGGER.info("Target temp = " + str(self._attr_target_temperature))
                self._attr_current_temperature = int(receivedJsonPayload["RESULT"]["t"])
                _LOGGER.info("Current temp = " + str(self._attr_current_temperature))

                self.is_available = True
            except Exception as err:
                _LOGGER.error(err)
            return

        else:
            _LOGGER.info("Send data to device.")
            self.NeedToSend = False
            # Ensure we update the current operation after changing the mode
            self.schedule_update_ha_state()
            return

    def set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        _LOGGER.info(f"Mode moet worden: {self._attr_hvac_mode}")
        self.NeedToSend = True
        return

    def set_temperature(self, **kwargs):
        """Set temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = temperature
        _LOGGER.info(f"Temp moet worden: {self._attr_target_temperature}")
        self.NeedToSend = True
        return

    def set_swing_mode(self, swing_mode: str):
        """Set swing mode."""
        self._attr_swing_mode = swing_mode
        _LOGGER.info(f"Swing mode moet worden: {self._attr_swing_mode}")
        self.NeedToSend = True
        return

    async def async_added_to_hass(self):
        """Device successfully added."""
        _LOGGER.info("Innova climate device added to hass()")
        await self.async_update()
        return
