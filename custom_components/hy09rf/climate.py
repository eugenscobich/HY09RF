
import logging
from typing import List, Optional

import voluptuous as vol

from custom_components.hy09rf import (
    Hy09rfThermostat,
    CONF_UNIQUE_ID,
    CONF_HOST,
    CONF_APP_ID,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_DID
)

from homeassistant.components.climate import (
    ClimateEntity,
    HVACMode,
    HVACAction,
    ClimateEntityFeature,
    PLATFORM_SCHEMA
)

from homeassistant.helpers.restore_state import RestoreEntity
# Unused until HA 2023.4
# from homeassistant.util.unit_conversion import TemperatureConverter
from homeassistant.components.climate.const import (
    PRESET_NONE,
    PRESET_AWAY,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP
)

from homeassistant.const import (
    PRECISION_HALVES,
    ATTR_TEMPERATURE,
    UnitOfTemperature,
    CONF_NAME
)

import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_APP_ID): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_DID): cv.string
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the generic thermostat platform."""
    async_add_entities([Hy09rfClimate(hass, config)])


class Hy09rfClimate(ClimateEntity, RestoreEntity):
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, hass, config):
        self._hass = hass

        if config.get(CONF_HOST) is None:
            self._host = "api.gizwits.com"
        else:
            self._host = config.get(CONF_HOST)

        if config.get(CONF_APP_ID) is None:
            self._app_id = "50b40b4e57114e6ba87bd46b9abe71d8"
        else:
            self._app_id = config.get(CONF_APP_ID)

        self._thermostat = Hy09rfThermostat(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), self._host, self._app_id, config.get(CONF_DID))

        if config.get(CONF_NAME) is None:
            self._name = "HY09RF"
        else:
            self._name = config.get(CONF_NAME)

        self._thermostat_set_temperature = None
        self._thermostat_set_temperature_min = DEFAULT_MIN_TEMP
        self._thermostat_set_temperature_max = DEFAULT_MAX_TEMP
        self._thermostat_room_temperature = None
        self._thermostat_temperature_compensate = None
        self._external_temp = None

        self._away_set_point = DEFAULT_MIN_TEMP
        self._manual_set_point = DEFAULT_MAX_TEMP

        self._preset_mode = None

        self._thermostat_current_action = None
        self._thermostat_current_mode = None

        self._thermostat_C_F = None

    @property
    def name(self):
        """Return thermostat name"""
        return self._name

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_HALVES

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # todo consult argument C_F
        if self._thermostat_C_F is True:
            return UnitOfTemperature.FAHRENHEIT
        else:
            return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self):
        """Return hvac operation i.e. heat, cool mode.
        Need to be one of HVACMode.
        """
        return self._thermostat_current_mode

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.
        Need to be a subset of HVACMode.
        """
        return [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of HVACAction.
        """
        return self._thermostat_current_action

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp.
        Requires ClimateEntityFeature.PRESET_MODE.
        """
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return a list of available preset modes.
        Requires ClimateEntityFeature.PRESET_MODE.
        """
        return [PRESET_NONE, PRESET_AWAY]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._thermostat_room_temperature is None:
            return None
        else:
            return self._thermostat_room_temperature + self._thermostat_temperature_compensate

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._thermostat_set_temperature

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._thermostat_set_temperature_min

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._thermostat_set_temperature_max

    async def async_added_to_hass(self):
        """Run when entity about to added."""
        await super().async_added_to_hass()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            target_temp = float(kwargs.get(ATTR_TEMPERATURE))
            await self._thermostat.setAttr(self._hass, { "set_temperature": target_temp, "work_mode": 0 })
        self._thermostat_set_temperature = target_temp
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self._thermostat.setAttr(self._hass, { "power": 0 })
        else:
            await self._thermostat.setAttr(self._hass, { "power": 1 })
            if hvac_mode == HVACMode.AUTO:
                await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 1 })
            elif hvac_mode == HVACMode.HEAT:
                await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 0 })
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        self._preset_mode = preset_mode
        if preset_mode == PRESET_AWAY:
            await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 3 })
        elif self._thermostat_current_mode == HVACMode.AUTO:
            await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 1 })
        else:
            await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 0 })
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn thermostat off"""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self):
        """Turn thermostat on"""
        await self.async_set_hvac_mode(HVACMode.AUTO)

    async def async_update(self):
        """Get thermostat info"""
        data = await self._thermostat.deviceAttrs(self._hass)

        if not data:
            return

        attr = data.get("attr")
        # Temperatures
        self._thermostat_room_temperature = float(attr.get("room_temperature"))
        self._thermostat_set_temperature = float(attr.get("set_temperature"))
        self._thermostat_set_temperature_min = float(attr.get("set_temperature_min"))
        self._thermostat_set_temperature_max = float(attr.get("set_temperature_max"))
        self._thermostat_temperature_compensate = float(attr.get("room_temperature_compensate"))
        self._thermostat_C_F = bool(attr.get("C_F"))

        # Thermostat modes & status
        if attr.get("power") == 0:
            # Unset away mode
            self._preset_mode = PRESET_NONE
            self._thermostat_current_mode = HVACMode.OFF
            self._thermostat_current_action = HVACAction.OFF
        else:
            # Set mode to manual when overridden auto mode or thermostat is in manual mode
            if attr.get("work_mode") == 0 or attr.get("work_mode") == 3:
                self._thermostat_current_mode = HVACMode.HEAT
                if attr.get("heating_state") == 1:
                    self._thermostat_current_action = HVACAction.HEATING
                else:
                    self._thermostat_current_action = HVACAction.IDLE
            elif attr.get("work_mode") == 2:
                # away
                self._thermostat_current_mode = HVACMode.HEAT
                self._preset_mode = PRESET_AWAY
                if attr.get("heating_state") == 1:
                    self._thermostat_current_action = HVACAction.HEATING
                else:
                    self._thermostat_current_action = HVACAction.IDLE
            else:
                # Unset auto mode
                self._preset_mode = PRESET_NONE
                self._thermostat_current_mode = HVACMode.AUTO
                if attr.get("heating_state") == 1:
                    self._thermostat_current_action = HVACAction.HEATING
                else:
                    self._thermostat_current_action = HVACAction.IDLE
        _LOGGER.debug(
            "Thermostat %s action=%s mode=%s",
            self._name, self._thermostat_current_action, self._thermostat_current_mode
        )
        
