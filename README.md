# Your support
This open-source project is developed in my free time. 

# Intro
Component for controlling HY09RF or other chinese-based WiFi smart thermostat that uses GizWits Open API. The integration uses GizWits cloud open api to login and change the controller settings.

![Termostat][https://github.com/eugenscobich/hass-hy09rf/blob/master/termostat.png]


Climate component will have 3 modes: "auto" (in which will used thermostat's internal schedule), "heat (which is "manual" mode) and "off". Also, while in "heat" mode it is possible to use preset "away". Changing mode to other than "heat" will set preset to "none". 

# Configuration as a Climate

| Name                      |  Type  |               Default              | Description                                                                                                                                                                  |
|---------------------------|--------|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| host ***(required)***     | string |                                    | IP or hostname of GezWits Open API. it can be one of api.gizwits.com, usapi.gizwits.com or api.gizwits.com.                                                                  |
| name ***(required)***     | string |               HY09RF               | Set a custom name which is displayed beside the icon.                                                                                                                        |
| unique_id                 | string |                                    | Set a unique id to allow entity customisation in HA GUI.                                                                                                                     |
| app_id ***(required)***   | string | '50b40b4e57114e6ba87bd46b9abe71d8' | App id extracted from the mobile application (called Smart Heating). The default one is for android application. Use '3bbf9e4b41b24b9ab939c9525dc9c95c' for iOS application. |
| username ***(required)*** | string |                                    | Username registered in application.                                                                                                                                          |
| password ***(required)*** | string |                                    | Password registered in application.                                                                                                                                          |
| did                       | string |                                    | 


#### Example:
```yaml
climate:
  - platform: hy09rf
    unique_id: 1
    host: euapi.gizwits.com
    username: eugen.scobich@gmail.com
    password: ********
```
