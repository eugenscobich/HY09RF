import httpx
import json
import logging
import time
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

CONF_UNIQUE_ID = 'unique_id'
CONF_HOST = 'host'
CONF_APP_ID = 'app_id'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'
CONF_DID = 'did'

class Hy09rfThermostat:

    def __init__(self, host, appId, username, password, did=None):
        self._host = host
        self._appId = appId
        self._username = username
        self._password = password
        self._did = did
        self._token = None

    async def login(self):
        params = {'username': self._username, 'password': self._password}
        headers = {"X-Gizwits-Application-Id": self._appId}
        async with httpx.AsyncClient() as client:
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

    async def bindings(self):
        if self._token is None:
            await self.login()
            await self.bindings()
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://" + self._host + "/app/bindings", headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    self._did = responseJson.get("devices")[0].get("did")
                    _LOGGER.warning("Thermostat login bindings: %s", responseJson)
                elif response.status_code == 400:
                    await self.login()
                    await self.bindings()
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def deviceState(self):
        if self._token is None:
            await self.login()
            await self.deviceState()
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://" + self._host + "/app/devices/" + self._did, headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    self._isOnline = responseJson.get("is_online")
                    _LOGGER.warning("Thermostat login bindings: %s", responseJson)
                elif response.status_code == 400:
                    await self.login()
                    await self.deviceState()
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def deviceAttrs(self):
        if self._token is None:
            await self.login()
            return await self.deviceAttrs()

        if self._did is None:
            await self.bindings()
            return await self.deviceAttrs() 

        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://" + self._host + "/app/devdata/" + self._did + "/latest", headers=headers)
                if response.status_code // 100 == 2:
                    responseJson =  response.json()
                    _LOGGER.warning("Thermostat login bindings: %s", responseJson)
                    return responseJson
                elif response.status_code == 400:
                    await self.login()
                    return await self.deviceAttrs()
                else:
                    raise Exception(f"Error: {response.status_code}, Response: {response.text}")
            except Exception as e:
                _LOGGER.error("Thermostat %s network error: %s", self._host, str(e))

    async def setAttr(self, attrs):
        if self._token is None:
            await self.login()
            return await self.setAttr(attrs)
        
        if self._did is None:
            await self.bindings()
            return await self.setAttr(attrs)
        
        params = {"attrs":  attrs}
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post("https://" + self._host + "/app/control/" + self._did, headers=headers, json=params)
                if response.status_code == 200:
                    _LOGGER.warning("Thermostat set device attributes result OK")
                elif response.status_code == 400:
                    self.login()
                    self.setAttr(attrs)
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