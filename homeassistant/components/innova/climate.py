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
from homeassistant.components.climate.const import (  # HVAC_MODE_DRY,; HVAC_MODE_FAN_ONLY,; HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# from voluptuous.error import Error


SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
HVAC_MODES = [
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    #    HVAC_MODE_DRY,
    #   HVAC_MODE_FAN_ONLY,
    #    HVAC_MODE_HEAT,
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
        self._attr_target_temperature_high = 31
        self._attr_target_temperature_low = 16
        self._attr_target_temperature_step = 1

        self._attr_fan_modes = fan_modes
        self._attr_swing_modes = swing_modes
        self._attr_hvac_modes = hvac_modes
        self._attr_temperature_unit = unit

        self._attr_supported_features = SUPPORT_FLAGS

        self.is_available = False
        self.needToSend = False

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
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return self._attr_hvac_modes

    @property
    def swing_mode(self):
        """Return current swing mode."""
        return self._attr_swing_mode

    @property
    def swing_modes(self):
        """Return possible swing modes."""
        return self._attr_swing_modes

    @property
    def available(self):
        """Return if the device is available for communication."""
        return self.is_available

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def target_temperature_step(self):
        """Return target temperature step."""
        return self._attr_target_temperature_step

    @property
    def current_temperature(self):
        """Return current reported temperature by the device."""
        return self._attr_current_temperature

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._attr_target_temperature_low

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._attr_target_temperature_high

    async def async_update(self):
        """Update HA state from device."""
        _LOGGER.info("Innova update()")
        await self.SyncState()
        # Ensure we update the current operation after running update
        self.schedule_update_ha_state()
        return

    async def SyncState(self):
        """Fetch current settings from climate device."""
        _LOGGER.info("Starting SyncState")

        """Initialize the receivedJsonPayload and r variable."""
        receivedJsonPayload = ""
        r = None

        url = "http://" + self._host + "/api/v/1/status"
        _LOGGER.info("Getting data from: " + url)
        try:
            r = await self.hass.async_add_executor_job(requests.get, url)
            if r is not None:
                receivedJsonPayload = json.loads(r.content)

            # _LOGGER.info(receivedJsonPayload)
            if bool(receivedJsonPayload["success"]):
                if int(receivedJsonPayload["RESULT"]["ps"]) == 0:
                    self._attr_hvac_mode = HVAC_MODE_OFF
                elif int(receivedJsonPayload["RESULT"]["wm"]) == 5:
                    self._attr_hvac_mode = HVAC_MODE_AUTO
                elif int(receivedJsonPayload["RESULT"]["wm"]) == 1:
                    self._attr_hvac_mode = HVAC_MODE_COOL

                self._attr_target_temperature = int(receivedJsonPayload["RESULT"]["sp"])
                self._attr_current_temperature = int(receivedJsonPayload["RESULT"]["t"])

                _LOGGER.info("Current HVAC mode = " + str(self._attr_hvac_mode))
                _LOGGER.info("Target temp = " + str(self._attr_target_temperature))
                _LOGGER.info("Current temp = " + str(self._attr_current_temperature))
                """Confirm that the device is available after receiving data"""
                if not self.is_available:
                    self.is_available = True
        except Exception as err:
            _LOGGER.error(err)
        return

    async def async_send_command(self, command):
        """Send command to device."""
        url = "http://" + self._host + "/api/v/1/" + command
        try:
            _LOGGER.info(f"Send {url} to device.")
            await self.hass.async_add_executor_job(requests.post, url)

        except Exception as err:
            _LOGGER.error(err)
        return

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        """If the HVAC mode differs from the current mode."""
        if not self._attr_hvac_mode == hvac_mode:
            self._attr_hvac_mode = hvac_mode
            _LOGGER.info(f"Switching to mode: {self._attr_hvac_mode}")

            if self._attr_hvac_mode == HVAC_MODE_OFF:
                command = "power/off"
            else:
                command = "power/on"
            await self.async_send_command(command)
            return
        else:
            _LOGGER.info(
                f"Device is already in desired mode: {self._attr_hvac_mode}. This does nothing."
            )
            return

    async def async_set_temperature(self, **kwargs):
        """Set temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = temperature
        _LOGGER.info(f"Desired temperature: {self._attr_target_temperature}")
        command = "set/setpoint?p_temp=" + str(int(self._attr_target_temperature))
        await self.async_send_command(command)
        return

    async def async_set_swing_mode(self, swing_mode: str):
        """Set swing mode."""
        self._attr_swing_mode = swing_mode
        _LOGGER.info(f"Set swing mode to: {self._attr_swing_mode}")
        # self.needToSend = True
        return

    async def async_set_fan_mode(self, fan_mode: str):
        """Set fan mode."""
        self._attr_fan_mode = fan_mode
        _LOGGER.info(f"Set fan mode to: {self._attr_fan_mode}")
        return

    async def async_added_to_hass(self):
        """Device successfully added."""
        _LOGGER.info("Innova climate device added to hass()")
        await self.async_update()
        return
