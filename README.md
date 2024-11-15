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

### API
The API can be used by the COS registration agent but also by any service
requiring to access the device database.

#### Health
<details>
 <summary><code>GET</code> <code><b>api/v1/health/</b></code> <code>(Get wether or not the app is alive)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | | |
</details>

#### Devices
<details>
 <summary><code>GET</code> <code><b>api/v1/devices/</b></code> <code>(Get the list of all the devices)</code></summary>

##### Parameters

> fields: comma seperated fields selection to get. Default to all.

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | List of devices.                                                         |
</details>

<details>
 <summary><code>POST</code> <code><b>api/v1/devices/</b></code> <code>(Add a device to the database)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"uid": "string", "address": "string", "public_ssh_key": "string", "grafana_dashboards"(optional): list(grafana_dashboards_uid), "foxglove_dashboards"(optional): list(foxglove_dashboard_uid)}   | Unique ID and IP address of the device. Grafana dashboards and Foxglove are optional list of applications specific dashboards UID. |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string", "public_ssh_key": "string", "grafana_dashboards"(optional): list(grafana_dashboards_uid), "foxglove_dashboards"(optional): list(foxglove_dashboard_uid)}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `409`         | `application/json`         | {"error": "Device uid already exists"}                                                                |
</details>

<details>
 <summary><code>GET</code> <code><b>api/v1/device/&#60str:uid&#62;/</b></code> <code>(Get the details of a device)</code></summary>

##### Parameters

> fields: comma seperated fields selection to get. Default to all.

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string", "public_ssh_key": "string", "grafana_dashboards": "list(grafana_dashboards_uid)" , "foxglove_dashboards": "list(foxglove_dashboards_uid)}                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>PATCH</code> <code><b>api/v1/device/&#60str:uid&#62;/</b></code> <code>(Modify the attribute of a device)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"field: "value"}   | Field to modify. Can be: address, grafana_dashboards, foxglove_dashboards |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "creation_date": "string", "address": "string", "public_ssh_key": "string", "grafana_dashboards"(optional): list(grafana_dashboards_uid), "foxglove_dashboards"(optional): list(foxglove_dashboard_uid)}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>DELETE</code> <code><b>api/v1/device/&#60str:uid&#62;/</b></code> <code>(Delete a device from the database)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `204`         | `text/html;charset=utf-8`        | None                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

#### Applications

<details>
 <summary><code>GET</code> <code><b>api/v1/applications/grafana/dashboards/</b></code> <code>(Get the details of a Grafana dashboards)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | list({"uid": string, "dashboard": JSON})                                                        |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>POST</code> <code><b>api/v1/applications/grafana/dashboards/</b></code> <code>(Add a Grafana dashboard to the database)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"uid": "string", "dashboard": JSON} | Unique ID and Grafana dashboards JSON content. |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "dashboard": JSON}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `409`         | `application/json`         | {"error": "GrafanaDashboard uid already exists"} |
</details>

<details>
 <summary><code>GET</code> <code><b>api/v1/applications/grafana/dashboards/&#60str:uid&#62;/</b></code> <code>(Get the details of a Grafana dashboard)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json; Content-Disposition attachment; filename=dashboard_uid.json`        | JSON file |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>PATCH</code> <code><b>api/v1/applications/grafana/dashboards/&#60str:uid&#62;/</b></code> <code>(Modify the attribute of a GrafanaDashboard)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"field: "value"}   | Field to modify. Can be: dasboard. |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "dashboard": JSON |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>DELETE</code> <code><b>api/v1/applications/grafana/dashboards/&#60str:uid&#62;/</b></code> <code>(Delete a Grafana dashboard from the database)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `204`         | `text/html;charset=utf-8`        | None                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>GET</code> <code><b>api/v1/applications/foxglove/dashboards/</b></code> <code>(Get the details of a Foxglove dashboards)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json`        | list({"uid": string, "dashboard": JSON})                                                        |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>POST</code> <code><b>api/v1/applications/foxglove/dashboards/</b></code> <code>(Add a Foxglove dashboard to the database)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"uid": "string", "dashboard": JSON} | Unique ID and Foxglove dashboards JSON content. |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "dashboard": JSON}                                |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `409`         | `application/json`         | {"error": "FoxgloveDashboard uid already exists"} |
</details>

<details>
 <summary><code>GET</code> <code><b>api/v1/applications/foxglove/dashboards/&#60str:uid&#62;/</b></code> <code>(Get the details of a Foxglove dashboard)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `200`         | `application/json; Content-Disposition attachment; filename=dashboard_uid.json`        | JSON file |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>PATCH</code> <code><b>api/v1/applications/foxglove/dashboards/&#60str:uid&#62;/</b></code> <code>(Modify the attribute of a FoxgloveDashboard)</code></summary>

##### Parameters

> | name      |  type     | data type               | description                                                           |
> |-----------|-----------|-------------------------|-----------------------------------------------------------------------|
> | None      |  required | {"field: "value"}   | Field to modify. Can be: dasboard. |


##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `201`         | `application/json`        | {"uid": "string", "dashboard": JSON |
> | `400`         | `application/json`                | {"field": "error details"}                            |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>

<details>
 <summary><code>DELETE</code> <code><b>api/v1/applications/foxglove/dashboards/&#60str:uid&#62;/</b></code> <code>(Delete a Foxglove dashboard from the database)</code></summary>

##### Parameters

> None

##### Responses

> | http code     | content-type                      | response                                                            |
> |---------------|-----------------------------------|---------------------------------------------------------------------|
> | `204`         | `text/html;charset=utf-8`        | None                                                         |
> | `404`         | `text/html;charset=utf-8`        | None                                                         |
</details>


## Installation
First we must generate a secret key for our django to sign data.
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
