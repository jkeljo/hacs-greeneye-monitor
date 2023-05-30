# GreenEye Monitor (GEM) Custom Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

The [Brultech](https://brultech.com) integration for Home Assistant allows you to create sensors for the various data channels of Brultech ECM-1220, ECM-1240, and/or GreenEye Monitor (GEM) energy monitors. Each current transformer (CT) channel, pulse counter, and temperature sensor appears in Home Assistant as one or more sensors, and can be used in automations.

## Setup

1. Add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories) for integrations in [HACS](https://hacs.xyz/docs/setup/download) by using this My button:
   [![Add repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jkeljo&repository=hacs-greeneye-monitor&category=Integration)
2. Further documentation is viewable in HACS, or by clicking [here](info.md)

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[commits]: https://github.com/jkeljo/hacs-greeneye-monitor/commits/main
[config]: https://my.home-assistant.io/redirect/config_flow_start?domain=brultech
[config-shield]: https://my.home-assistant.io/badges/config_flow_start.svg
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40jkeljo-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jkeljo/hacs-greeneye-monitor.svg?style=for-the-badge
[releases]: https://github.com/jkeljo/hacs-greeneye-monitor/releases
[user_profile]: https://github.com/jkeljo
