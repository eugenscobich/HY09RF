
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
    PRECISION_WHOLE,
    PRECISION_TENTHS,
    ATTR_TEMPERATURE,
    UnitOfTemperature,
    CONF_NAME
)

import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Required(CONF_APP_ID): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_DID): cv.string
    #vol.Optional(CONF_USE_EXTERNAL_TEMP, default=DEFAULT_USE_EXTERNAL_TEMP): cv.boolean,
    #vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): vol.In([PRECISION_HALVES, PRECISION_WHOLE, PRECISION_TENTHS]),
    #vol.Optional(CONF_USE_COOLING, default=DEFAULT_USE_COOLING): cv.boolean
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the generic thermostat platform."""
    async_add_entities([Hy09rfClimate(hass, config)])


class Hy09rfClimate(ClimateEntity, RestoreEntity):
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, hass, config):
        self._hass = hass
        self._thermostat = Hy09rfThermostat(config.get(CONF_HOST), config.get(CONF_APP_ID), config.get(CONF_USERNAME), config.get(CONF_PASSWORD), config.get(CONF_DID))

        self._name = config.get(CONF_NAME)
        self._min_temp = DEFAULT_MIN_TEMP
        self._max_temp = DEFAULT_MAX_TEMP
        self._hysteresis = None
        self._room_temp = None
        self._external_temp = None

        self._away_set_point = DEFAULT_MIN_TEMP
        self._manual_set_point = DEFAULT_MIN_TEMP

        self._preset_mode = None

        self._thermostat_current_action = None
        self._thermostat_current_mode = None
        self._thermostat_current_temp = None
        self._thermostat_target_temp = None

        self._attr_name = self._name
        self._attr_unique_id = config.get(CONF_UNIQUE_ID)

    @property
    def name(self):
        """Return thermostat name"""
        return "Eugen bla bla bla" #self._name

    @property
    def precision(self):
        """Return the precision of the system."""
        return PRECISION_HALVES

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        # todo consult argument C_F
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
        return self._thermostat_current_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._thermostat_target_temp

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

    # Backward compatibility until 2023.4
    def get_converter(self):
        try:
            from homeassistant.util.unit_conversion import TemperatureConverter
            convert = TemperatureConverter.convert
        except ModuleNotFoundError or ImportError as ee:
            from homeassistant.util.temperature import convert
        return convert

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def extra_state_attributes(self):
        """Return the attribute(s) of the sensor"""
        return {
            'away_set_point': self._away_set_point,
            'manual_set_point': self._manual_set_point,
            'external_temp': self._external_temp,
            'room_temp': self._room_temp,
            'current_temp': self._thermostat_current_temp,
            'target_temp': self._thermostat_target_temp
        }

    async def async_added_to_hass(self):
        """Run when entity about to added."""
        await super().async_added_to_hass()

        # Restore
        last_state = await self.async_get_last_state()

        if last_state is not None:
            for param in ['away_set_point', 'manual_set_point']:
                if param in last_state.attributes:
                    setattr(self, '_{0}'.format(param), last_state.attributes[param])

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            target_temp = float(kwargs.get(ATTR_TEMPERATURE))

            await self._thermostat.setAttr(self._hass, { "set_temperature": target_temp, "work_mode": 0 })

            # Save temperatures for future use
            if self._preset_mode == PRESET_AWAY:
                self._away_set_point = target_temp
            elif self._preset_mode == PRESET_NONE:
                self._manual_set_point = target_temp

        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set operation mode."""
        if hvac_mode == HVACMode.OFF:
            await self._thermostat.setAttr(self._hass, { "power": 0 })
        else:
            await self._thermostat.setAttr(self._hass, { "power": 1 })
            if hvac_mode == HVACMode.AUTO:
                await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 1 })
            elif hvac_mode == HVACMode.HEAT or hvac_mode == HVACMode.HEAT_COOL:
                await self._thermostat.setAttr(self._hass, { "power": 1, "work_mode": 0 })
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        self._preset_mode = preset_mode

#        device = self._thermostat.device()
#        if device.auth():
#            device.set_power(BROADLINK_POWER_ON)
#            device.set_mode(BROADLINK_MODE_MANUAL, self._thermostat_loop_mode, self.thermostat_get_sensor())
#            if self._preset_mode == PRESET_AWAY:
#                device.set_temp(self._away_set_point)
#            elif self._preset_mode == PRESET_NONE:
#                device.set_temp(self._manual_set_point)

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

        # Temperatures
        self._room_temp = data.get("room_temperature")
        self._thermostat_current_temp = data.get("room_temperature")
        self._hysteresis = data.get("room_temperature_compensate")
        self._min_temp = data.get("set_temperature_min")
        self._max_temp = data.get("set_temperature_max")

        self._thermostat_target_temp = data.get("set_temperature")

        # Thermostat modes & status
        if data.get("power") == 0:
            # Unset away mode
            self._preset_mode = PRESET_NONE
            self._thermostat_current_mode = HVACMode.OFF
            self._thermostat_current_action = HVACAction.OFF
        else:
            # Set mode to manual when overridden auto mode or thermostat is in manual mode
            if data.get("work_mode") == 0:
                self._thermostat_current_mode = HVACMode.HEAT
                if data.get("heating_state") == 1:
                    self._thermostat_current_action = HVACAction.HEATING
                else:
                    self._thermostat_current_action = HVACAction.IDLE
            else:
                # Unset away mode
                self._preset_mode = PRESET_NONE
                self._thermostat_current_mode = HVACMode.AUTO
                if data.get("heating_state") == 1:
                    self._thermostat_current_action = HVACAction.HEATING
                else:
                    self._thermostat_current_action = HVACAction.IDLE
        _LOGGER.debug(
            "Thermostat %s action=%s mode=%s",
            self._name, self._thermostat_current_action, self._thermostat_current_mode
        )
        _LOGGER.warning("Climate %s", self)
