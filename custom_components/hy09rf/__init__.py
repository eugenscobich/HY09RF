import httpx
import json
import logging
import time
from datetime import datetime
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CONF_UNIQUE_ID = 'unique_id'
CONF_HOST = 'host'
CONF_APP_ID = 'app_id'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_DID = 'did'

class Hy09rfThermostat:

    def __init__(self, username, password, host="api.gizwits.com", appId="50b40b4e57114e6ba87bd46b9abe71d8", did=None):
        self._host = host
        self._appId = appId
        self._username = username
        self._password = password
        self._did = did
        self._token = None

    async def login(self, hass: HomeAssistant):
        params = {'username': self._username, 'password': self._password}
        headers = {"X-Gizwits-Application-Id": self._appId}
        async with get_async_client(hass) as client:
            try:
                response = await client.post("https://" + self._host + "/app/login", headers=headers, json=params)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    self._uid = responseJson.get("uid")
                    self._token = responseJson.get("token")
                    _LOGGER.warning("Thermostat login result: %s", responseJson)
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def bindings(self, hass: HomeAssistant):
        if self._token is None:
            await self.login(hass)
            await self.bindings(hass)
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        async with get_async_client(hass) as client:
            try:
                response = await client.get("https://" + self._host + "/app/bindings", headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    self._did = responseJson.get("devices")[0].get("did")
                    _LOGGER.warning("Thermostat bindings result: %s", responseJson)
                elif response.status_code == 400:
                    await self.login(hass)
                    await self.bindings(hass)
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def deviceState(self, hass: HomeAssistant):
        if self._token is None:
            await self.login(hass)
            await self.deviceState(hass)
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}

        async with get_async_client(hass) as client:
            try:
                response = await client.get("https://" + self._host + "/app/devices/" + self._did, headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    self._isOnline = responseJson.get("is_online")
                    _LOGGER.warning("Thermostat device state: %s", responseJson)
                elif response.status_code == 400:
                    await self.login(hass)
                    await self.deviceState(hass)
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def deviceAttrs(self, hass: HomeAssistant):
        if self._token is None:
            await self.login(hass)
            return await self.deviceAttrs(hass)

        if self._did is None:
            await self.bindings(hass)
            return await self.deviceAttrs(hass) 

        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}

        async with get_async_client(hass) as client:
            try:
                response = await client.get("https://" + self._host + "/app/devdata/" + self._did + "/latest", headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    _LOGGER.warning("Thermostat device attributes result: %s", responseJson)
                    return responseJson
                elif response.status_code == 400:
                    await self.login(hass)
                    return await self.deviceAttrs(hass)
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def setAttr(self, hass: HomeAssistant, attrs):
        if self._token is None:
            await self.login(hass)
            return await self.setAttr(hass, attrs)
        
        if self._did is None:
            await self.bindings()
            return await self.setAttr(attrs)
        
        params = {"attrs":  attrs}
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        async with get_async_client(hass) as client:
            try:
                response = await client.post("https://" + self._host + "/app/control/" + self._did, headers=headers, json=params)
                if response.status_code == 200:
                    _LOGGER.warning("Thermostat set device attributes result OK")
                elif response.status_code == 400:
                    self.login(hass)
                    self.setAttr(hass, attrs)
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

'''
import asyncio
instance = Hy09rfThermostat("euapi.gizwits.com", "50b40b4e57114e6ba87bd46b9abe71d8", "eugen.scobich@gmail.com", "bendery37")
deviceAttrs = asyncio.run(instance.deviceAttrs())
print(deviceAttrs)
if deviceAttrs.get("attr").get("child_lock") == 1:
    asyncio.run(instance.setAttr({ "child_lock": False }))
else:
    asyncio.run(instance.setAttr({ "child_lock": True }))
time.sleep(10)
asyncio.run(instance.deviceAttrs())
'''