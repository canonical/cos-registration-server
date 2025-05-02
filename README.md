# COS registration server

COS registration server is responsible for storing devices registered by the
COS registration agent.
The COS registration server is a django server consisting of a database,
an API as well as front end views.
With COS registration server a device can register itself and update
its informations.
A user can also visualize the registered devices as well as discovering
customized device applications.

[![codecov](https://codecov.io/gh/canonical/cos-registration-server/branch/main/graph/badge.svg?token=cos-registration-server_token_here)](https://codecov.io/gh/canonical/cos-registration-server)
[![CI](https://github.com/canonical/cos-registration-server/actions/workflows/main.yml/badge.svg)](https://github.com/canonical/cos-registration-server/actions/workflows/main.yml)


## Features

The COS registration server consist of two applications: Devices and API.

### Devices

This application is describing the database as well as offering views for
the user to visualize the list of devices and the specificities of each device.

#### Device model
The Device model represent a device stored in the database.
It consists of:
- UID: Unique ID per device. Typically, the name of the instance or the serial number.
- Creation date: DateTime of the device creation in the server.
- Address: IP address or hostname of the device.
- Public SSH key: public SSH key for the device.
- Grafana dashboards: Grafana dashboards used by this device.
- Foxglove dashboards: Foxglove dashboards used by this device.
- Prometheus alert rule files: Prometheus alert rule files used by this device.

#### View: `devices/`

It provides a simple list of all the registered devices.
Every device listed provides a link to explore the specificities of each
device.

#### View: `devices/<str:uid>`

It provides a view of all the information registered in the database:
UID, creation date and address.
Additionally, this view provides a list of links of COS applications
personalised for the given device.
The COS applications personalised links are:
- Grafana: Pointing to the Grafana dashboard folder of the device.
- Foxglove: Pointing to the Foxglove app with the proper websocket connected.
- Bag files: Pointing to the file server directory storing the bag files of the
device.

### Applications

This application is hosting the various applications configuration that can be associated with a device. The applications and their possible configuration is predefined.

#### GrafanaDashboard model
The GrafanaDashboard model represent a Grafana dashboard stored in the database.
It consists of:
- UID: Unique ID per dashboard. Typically, the name of the data it represents.
- Dashboard: JSON data representing the dashboard.

#### FoxgloveDashboard model
The FoxgloveDashboard model represent a Foxglove dashboard (called layouts in the Foxglove ecosystem) stored in the database.
It consists of:
- UID: Unique ID per dashboard. Typically, the name of the data it represents.
- Dashboard: JSON data representing the dashboard.

#### PrometheusAlertRuleFile model
The PrometheusAlertRuleFile model represents a Prometheus Alert Rule file stored in the database.
It consists of:
- UID: Unique ID of the alert rule file.
- Rules: The rules in YAML format.
- Template: Boolean stating whether the rule file is a template and must be rendered.

### API
The API can be used by the COS registration agent but also by any service
requiring to access the device database.

The details of the API are available in the Open API file: [cos_registration_server/openapi.yaml](cos_registration_server/openapi.yaml) and
as a Swagger view the [robotics documentation](https://canonical-robotics.readthedocs-hosted.com/en/latest/references/observability/cos-registration-server-api/).

## Installation
First we must generate a secret key for our Django to sign data.
The secret key must be a large random value and it must be kept secret.

A secret key can be generated with the following command:

`export SECRET_KEY_DJANGO=$(make secretkey)`

We can expand the allowed hosts list:

`export ALLOWED_HOST_DJANGO="cos-registration-server.com"`

Additionally, we can provide a directory for the database:

`export DATABASE_BASE_DIR_DJANGO="/var/lib"`

`make install`

`make runserver`

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
