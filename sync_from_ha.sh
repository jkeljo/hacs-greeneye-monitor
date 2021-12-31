#!/bin/bash -ex

rm -rf custom_components/greeneye_monitor
rm -rf tests
cp -r ../home-assistant/homeassistant/components/greeneye_monitor custom_components/
cp -r ../home-assistant/tests/components/greeneye_monitor tests
sed -i s/homeassistant.components.greeneye_monitor/custom_components.greeneye_monitor/ custom_components/greeneye_monitor/*.py tests/*.py
sed -i 's/{/{\
  "version": "0.1",/' custom_components/greeneye_monitor/manifest.json