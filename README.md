# Note
This project is under development, do not try it until this statment will disapear. 

# Your support
This open-source project is developed in my free time. 
Your donation would help me dedicate more time and resources to improve project, add new features, fix bugs, 
as well as improve motivation and helps me understand, that this project is useful not only for me, but for more users.

# Intro
Component for controlling HY09RF or other chinese-based WiFi smart thermostat that uses GizWits API.
Climate component will have 3 modes: "auto" (in which will used thermostat's internal schedule), "heat (which is "manual" mode) and "off". Also, while in "heat" mode it is possible to use preset "away". Changing mode to other than "heat" will set preset to "none". 

If you want to use custom or more advanced control, you should use switch component and generic thermostat in Home Assistant instead. See below for configuration.

# Configuration as a Climate

| Name                  |  Type   | Default | Description                                                                                             |
|-----------------------|:-------:|:-------:|---------------------------------------------------------------------------------------------------------|
| host ***(required)*** | string  |         | IP or hostname of thermostat.                                                                           |
| name ***(required)*** | string  |         | Set a custom name which is displayed beside the icon.                                                   |
| unique_id             | string  |         | Set a unique id to allow entity customisation in HA GUI.                                                |
| schedule              | integer |   `0`   | Set which schedule to use (`0` - `12345,67`, `1` - `123456,7`, `2` - `1234567`).                        |
| use_external_temp     | boolean | `true`  | Set to `false` if you want to use thermostat`s internal temperature sensor for temperature calculation. |
| precision             |  float  |   0.5   | Set temperature precision `1.0` or `0.5`.                                                               |
| use_cooling           | boolean | `false` | Set to `true` if your thermostat has cooling function.                                                  |

#### Example:
```yaml
climate:
  platform: hy09rf
  name: livingroom_floor
  host: 192.168.0.1
  use_external_temp: false
```
