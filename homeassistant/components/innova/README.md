# HomeAssistant-innova HVAC component
Custom Innova climate component written in Python3 for Home Assistant. Controls Innova AC's

## Setup

1. Make sure your Innova HVAC has(/have) (a) fixed IP-address(es).

2. In your `configuration.yaml` file, add the following for every Innova device:

```yaml
climate:
  - platform: innova
    name: [The friendly name you want to use]
    host: [The IP-address of the device]

```

3. Done!