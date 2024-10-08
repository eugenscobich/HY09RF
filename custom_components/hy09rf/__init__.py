import http.client
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

    def login(self):
        params = {'username': self._username, 'password': self._password}
        headers = {"X-Gizwits-Application-Id": self._appId}
        try:
            body = json.dumps(params)
            connection = http.client.HTTPSConnection(self._host)
            connection.request("POST", "/app/login", body=body, headers=headers)
            response = connection.getresponse()
            response_data = response.read().decode()
            if 200 == response.status:
                response = json.loads(response_data)
                self._uid = response.get("uid")
                self._token = response.get("token")
                return response
            else:
                raise Exception(f"Error: {response.status}, Response: {response_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            connection.close()

    def bindings(self):
        if self._token is None:
            self.login()
            return self.bindings()
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        try:
            connection = http.client.HTTPSConnection(self._host)
            connection.request("GET", "/app/bindings", headers=headers)
            response = connection.getresponse()
            response_data = response.read().decode()
            if 200 <= response.status < 300:
                response = json.loads(response_data)
                self._did = response.get("devices")[0].get("did")
                return response
            elif response.status == 400:
                self.login()
                return self.bindings()
            else:
                raise Exception(f"Error: {response.status}, Response: {response_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            connection.close()

    def deviceState(self):
        if self._token is None:
            self.login()
            return self.deviceState()
        
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        try:
            connection = http.client.HTTPSConnection(self._host)
            connection.request("GET", "/app/devices/" + self._did, headers=headers)
            response = connection.getresponse()
            response_data = response.read().decode()
            if 200 <= response.status < 300:
                response = json.loads(response_data)
                self._isOnline = response.get("is_online")
                return response
            elif response.status == 400:
                self.login()
                return self.deviceState()
            else:
                raise Exception(f"Error: {response.status}, Response: {response_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            connection.close()

    def deviceAttrs(self):
        if self._token is None:
            self.login()
            return self.deviceAttrs()

        if self._did is None:
            self.bindings()
            return self.deviceAttrs() 

        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        try:
            connection = http.client.HTTPSConnection(self._host)
            connection.request("GET", "/app/devdata/" + self._did + "/latest", headers=headers)
            response = connection.getresponse()
            response_data = response.read().decode()
            if 200 <= response.status < 300:
                return json.loads(response_data)
            elif response.status == 400:
                self.login()
                return self.deviceAttrs()
            else:
                raise Exception(f"Error: {response.status}, Response: {response_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            connection.close()

    def setAttr(self, attrs):
        if self._token is None:
            self.login()
            return self.setAttr(attrs)
        
        if self._did is None:
            self.bindings()
            return self.setAttr(attrs)
        
        params = {"attrs":  attrs}
        headers = {"X-Gizwits-Application-Id": self._appId, "X-Gizwits-User-token": self._token}
        try:
            body = json.dumps(params)
            connection = http.client.HTTPSConnection(self._host)
            connection.request("POST", "/app/control/" + self._did, body=body, headers=headers)
            response = connection.getresponse()
            response_data = response.read().decode()
            if 200 <= response.status < 300:
                response = json.loads(response_data)
                return response
            elif response.status == 400:
                self.login()
                return self.setAttr(attrs)
            else:
                raise Exception(f"Error: {response.status}, Response: {response_data}")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            connection.close()

instance = Hy09rfThermostat("euapi.gizwits.com", "50b40b4e57114e6ba87bd46b9abe71d8", "eugen.scobich@gmail.com", "bendery37")
print(instance.login())
print(instance.bindings())
print(instance.deviceState())
deviceAttrs = instance.deviceAttrs()
print(deviceAttrs)
if deviceAttrs.get("attr").get("child_lock") == 1:
    print(instance.setAttr({ "child_lock": False }))
else:
    print(instance.setAttr({ "child_lock": True }))
time.sleep(10)
print(instance.deviceAttrs())