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
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SWING_OFF,
    SWING_ON,
)

# from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# from voluptuous.error import Error


SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
HVAC_MODES = [
    HVAC_MODE_AUTO,  # = 5
    HVAC_MODE_COOL,  # = 1
    HVAC_MODE_DRY,  # = 3
    HVAC_MODE_FAN_ONLY,  # = 4
    HVAC_MODE_HEAT,  # = 0
    HVAC_MODE_OFF,
]
FAN_MODES = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]  # fs [0, 1, 2, 3 ]
SWING_MODES = [SWING_OFF, SWING_ON]  # fr = [7, 0]
# NIGHT MODE = nm = 0, 1
# POWER = ps = 0, 1

_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = "Innova Climate"
DOMAIN = "innova"
PLATFORMS = ["climate"]

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
        self.url = "http://" + self._host + "/api/v/1/"

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

        url = self.url + "status"
        _LOGGER.info("Getting data from: " + url)
        try:
            r = await self.hass.async_add_executor_job(requests.get, url)
            if r is not None:
                receivedJsonPayload = json.loads(r.content)

            # _LOGGER.info(receivedJsonPayload)
            if bool(receivedJsonPayload["success"]):
                """Retrieve current working mode from device."""
                if int(receivedJsonPayload["RESULT"]["ps"]) == 0:
                    self._attr_hvac_mode = HVAC_MODE_OFF
                else:
                    if int(receivedJsonPayload["RESULT"]["wm"]) == 0:
                        self._attr_hvac_mode = HVAC_MODE_HEAT
                    elif int(receivedJsonPayload["RESULT"]["wm"]) == 1:
                        self._attr_hvac_mode = HVAC_MODE_COOL
                    # elif int(receivedJsonPayload["RESULT"]["wm"]) == 2:
                    #    self._attr_hvac_mode = HVAC_MODE_
                    elif int(receivedJsonPayload["RESULT"]["wm"]) == 3:
                        self._attr_hvac_mode = HVAC_MODE_DRY
                    elif int(receivedJsonPayload["RESULT"]["wm"]) == 4:
                        self._attr_hvac_mode = HVAC_MODE_FAN_ONLY
                    elif int(receivedJsonPayload["RESULT"]["wm"]) == 5:
                        self._attr_hvac_mode = HVAC_MODE_AUTO

                self._attr_target_temperature = int(receivedJsonPayload["RESULT"]["sp"])
                self._attr_current_temperature = int(receivedJsonPayload["RESULT"]["t"])

                if int(receivedJsonPayload["RESULT"]["fs"]) == 0:
                    self._attr_fan_mode = FAN_AUTO
                elif int(receivedJsonPayload["RESULT"]["fs"]) == 1:
                    self._attr_fan_mode = FAN_LOW
                elif int(receivedJsonPayload["RESULT"]["fs"]) == 2:
                    self._attr_fan_mode = FAN_MEDIUM
                elif int(receivedJsonPayload["RESULT"]["fs"]) == 3:
                    self._attr_fan_mode = FAN_HIGH

                if int(receivedJsonPayload["RESULT"]["fr"]) == 7:
                    self._attr_swing_mode = SWING_OFF
                elif int(receivedJsonPayload["RESULT"]["fr"]) == 0:
                    self._attr_swing_mode = SWING_ON

                _LOGGER.info("Current HVAC mode = " + str(self._attr_hvac_mode))
                _LOGGER.info("Target temp = " + str(self._attr_target_temperature))
                _LOGGER.info("Current temp = " + str(self._attr_current_temperature))
                _LOGGER.info("Current FAN mode = " + str(self._attr_fan_mode))
                _LOGGER.info("Current SWING mode = " + str(self._attr_swing_mode))
                """Confirm that the device is available after receiving data"""
                if not self.is_available:
                    self.is_available = True
        except Exception as err:
            _LOGGER.error(err)
        return

    async def async_send_command(self, command):
        """Send command to device."""
        url = self.url + command
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
            elif self._attr_hvac_mode == HVAC_MODE_HEAT:
                command = "set/mode/heating"
            elif self._attr_hvac_mode == HVAC_MODE_COOL:
                command = "set/mode/cooling"
            elif self._attr_hvac_mode == HVAC_MODE_DRY:
                command = "set/mode/dehumidification"
            elif self._attr_hvac_mode == HVAC_MODE_FAN_ONLY:
                command = "set/mode/fanonly"
            elif self._attr_hvac_mode == HVAC_MODE_AUTO:
                command = "set/mode/auto"

            if command is not None:
                await self.async_send_command(command)
            else:
                _LOGGER.error(f"{hvac_mode} is not a supported HVAC mode.")
            return
        else:
            _LOGGER.info(
                f"HVAC mode is already {self._attr_hvac_mode}. Not sending the command."
            )
            return

    async def async_set_temperature(self, **kwargs):
        """Set temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        if not int(self._attr_target_temperature) == int(temperature):
            self._attr_target_temperature = int(temperature)
            _LOGGER.info(
                f"Setting target temperature to: {self._attr_target_temperature}"
            )
            command = "set/setpoint?p_temp=" + str(self._attr_target_temperature)
            await self.async_send_command(command)
        else:
            _LOGGER.info(
                f"Target temperature is already {temperature}. Not sending the command."
            )
        return

    async def async_set_swing_mode(self, swing_mode):
        """Set swing mode."""
        if not self._attr_swing_mode == swing_mode:
            self._attr_swing_mode = swing_mode
            _LOGGER.info(f"Set swing mode to: {self._attr_swing_mode}")
            if swing_mode == SWING_ON:
                command = "set/feature/rotation?value=0"
            elif swing_mode == SWING_OFF:
                command = "set/feature/rotation?value=7"
            if command is not None:
                await self.async_send_command(command)
            else:
                _LOGGER.error(f"{swing_mode} is not a supported swing mode")
            return
        else:
            _LOGGER.info(
                f"Swing mode is already {swing_mode}. Not sending the command."
            )
        return

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode."""
        if not self._attr_fan_mode == fan_mode:
            self._attr_fan_mode = fan_mode
            _LOGGER.info(f"Set fan mode to: {self._attr_fan_mode}")
            if fan_mode == FAN_AUTO:
                command = "set/fan?value=0"
            elif fan_mode == FAN_LOW:
                command = "set/fan?value=1"
            elif fan_mode == FAN_MEDIUM:
                command = "set/fan?value=2"
            elif fan_mode == FAN_HIGH:
                command = "set/fan?value=3"
            if command is not None:
                await self.async_send_command(command)
            else:
                _LOGGER.error(f"{fan_mode} is not a supported fan mode")
            return
        else:
            _LOGGER.info(f"Fan mode is already {fan_mode}. Not sending the command.")
        return

    async def async_added_to_hass(self):
        """Device successfully added."""
        _LOGGER.info("Innova climate device added to hass()")
        await self.async_update()
        return
