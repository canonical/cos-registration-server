# COS registration server

COS registration server is responsible for storing devices registered by the
COS registration agent.
The COS registration server is a django server consisting of a database,
an API as well as front end views.
With COS registration server a device can register itself and update
its informations.
A user can also visualize the registered devices as well as discovering
customized device applications.

[![codecov](https://codecov.io/gh/ubuntu-robotics/cos-registration-server/branch/main/graph/badge.svg?token=cos-registration-server_token_here)](https://codecov.io/gh/ubuntu-robotics/cos-registration-server)
[![CI](https://github.com/ubuntu-robotics/cos-registration-server/actions/workflows/main.yml/badge.svg)](https://github.com/ubuntu-robotics/cos-registration-server/actions/workflows/main.yml)


## Features

The COS registration server consist of two applications: Devices and API.

### Devices

This application is describing the database as well as offering views for
the user to visualize the list of devices and the specificities of one device.

#### Device model
The Device model represent a device stored in the database.
It consists of:
- UID: Unique ID per device. Typically, the name of the instance of the serial number.
- Creation date: DateTime of the device creation in the server.
- Address: IP address or hostname of the device.

#### View: `devices/`

It provides a simple list of all the registered devices.
Every device listed provides a link to explore the specificities of a specific
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

### API
The API can be used by the COS registration agent but also by any service
requiring to access the device database.

#### Devices
<details>
 <summary><code>GET</code> <code><b>api/v1/devices</b></code> <code>(Get the list of all the devices)</code></summary>

#### Parameters

> None

#### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | List of devices.                                                         |
</details>

<details>
 <summary><code>POST</code> <code><b>api/v1/devices</b></code> <code>(Add a device to the database)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"uid": "string", "address": "string"}   | Unique ID and IP address of the device  |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string"}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `409`         | `application/json`         | {"error": "Device uid already exists"}                                                                |
</details>

#### Device

<details>
 <summary><code>GET</code> <code><b>api/v1/device/&#60str:uid&#62;</b></code> <code>(Get the details of a device)</code></summary>

#### Parameters

> None

#### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string"}                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>PATCH</code> <code><b>api/v1/device/&#60str:uid&#62;</b></code> <code>(Modify the attribute of a device)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"address": "string"}   | Address to modify.  |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string"}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>DELETE</code> <code><b>api/v1/device/&#60str:uid&#62;</b></code> <code>(Delete a device from the database)</code></summary>

#### Parameters

> None

#### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `204`         | `text/html;charset=utf-8`        | None                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

## Installation

`make install`

`make runserver`

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.
