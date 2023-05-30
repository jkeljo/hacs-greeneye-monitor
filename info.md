[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

{% if not installed %}

## Installation

1. Click Download.
2. Restart Home Assistant
3. In the Home Assistant UI go to "Configuration" -> "Integrations" click "+" and search for "GreenEye Monitor (GEM)", or click the below My button:
   [![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=greeneye_monitor)

## Migration from the built-in integration

This integration was derived from the built-in `greeneye_monitor` integration by its developer, [@jkeljo](https://github.com/jkeljo). This version of `greeneye_monitor` has a number of changes and enhancements relative to the built-in one, and is configured via the Home Assistant UI. The first time you launch Home Assistant, this integration will import your existing YAML configuration and entities, and you may then delete the YAML.

{% endif %}

## Entities

This integration creates entities as follows.

### Current transformer channels

Each current transformer channel will appear as a device with associated sensors for three different values:

- Energy (kWh) - this sensor is updated only once every 30 minutes and is usable with the Energy Dashboard
- Power (kW) - disabled by default
- Current (amps) - disabled by default, not created for ECM-1240 Aux channels

### Pulse counter channels

Each pulse counter channel will appear as a device with associated sensors for two different values:

- Pulse count - this sensor is updated only once every 30 minutes. The units and device type of this sensor are configured during setup of the integration. If a device type is set, this sensor may be used with the Energy Dashboard.
- Pulse rate - disabled by default. This sensor is updated as fast as the monitor sends new packets, and by default reports a rate as units per second. Units per minute or per hour may be selected after setup by clicking the Configure button in the integration.

### Temperature channels

Each temperature channel will appear as a device with a single a temperature sensor, disabled by default.

### Voltage channels

Each monitor's voltage sensor will appear as a device with a single voltage sensor entity, disabled by default.

### Configuration entities

If the GEM or ECM responds to API calls (that is, it is connected directly to your network and not a DashBox or other aggregator), a number of configuration entities will be created.

- The monitor itself will have a configuration entity for controlling the packet send rate.
- Each current channel device (except ECM-1240 Aux channels) will have configuration entities for setting the CT type and range.

### ECM-1240 Aux 5

During integration setup, you may select whether Aux 5 is used as a current channel or pulse counter channel.

## Handling chatty entities

Entities that report instantaneous values like power, current, temperature, voltage, and pulse rate will be updated as fast as the monitor sends data, which is typically every few seconds. That's a lot of data, and the databases used by the [`recorder`](https://www.home-assistant.io/integrations/recorder) integration for history don't do well with that much data, so these entities are disabled by default. Before enabling any of them, it is recommended to configure the [`influxdb`](https://www.home-assistant.io/integrations/influxdb) integration and exclude the chatty entities from `recorder`.

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[commits]: https://github.com/jkeljo/hacs-greeneye-monitor/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/jkeljo/hacs-greeneye-monitor/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40jkeljo-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[releases]: https://github.com/jkeljo/hacs-greeneye-monitor/releases
[user_profile]: https://github.com/jkeljo
