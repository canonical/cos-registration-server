import json
from datetime import datetime, timedelta
from typing import Any, Dict, Set, Union

import yaml
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRule,
    PrometheusAlertRule,
)
from devices.models import Device
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase


class HealthViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:health")

    def test_health_ok(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class DevicesViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:devices")

        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

        self.public_ssh_key = "ssh-rsa AaBbCc/+=098765431"

    def create_device(self, **fields: Union[str, Set[str]]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_grafana_dashboard(
        self, uid: str, dashboard: Dict[str, Any]
    ) -> GrafanaDashboard:
        grafana_dashboard = GrafanaDashboard(uid=uid, dashboard=dashboard)
        grafana_dashboard.save()
        return grafana_dashboard

    def add_foxglove_dashboard(
        self, uid: str, dashboard: Dict[str, Any]
    ) -> FoxgloveDashboard:
        foxglove_dashboard = FoxgloveDashboard(uid=uid, dashboard=dashboard)
        foxglove_dashboard.save()
        return foxglove_dashboard

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_device(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        grafana_dashboard_uid = "dashboard-1"
        foxglove_dashboard_uid = "layout-1"
        self.add_grafana_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.add_foxglove_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.create_device(
            uid=uid,
            address=address,
            public_ssh_key=self.public_ssh_key,
            grafana_dashboards={grafana_dashboard_uid},
            foxglove_dashboards={foxglove_dashboard_uid},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().uid, uid)
        self.assertEqual(Device.objects.get().address, address)
        self.assertEqual(
            Device.objects.get().public_ssh_key, self.public_ssh_key
        )
        self.assertAlmostEqual(
            Device.objects.get().creation_date,
            timezone.now(),
            delta=timedelta(seconds=10),
        )
        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().uid,
            grafana_dashboard_uid,
        )
        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().dashboard,
            self.simple_grafana_dashboard,
        )
        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().uid,
            foxglove_dashboard_uid,
        )
        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().dashboard,
            self.simple_foxglove_dashboard,
        )

    def test_create_multiple_devices(self) -> None:
        devices = [
            {
                "uid": "robot-1",
                "address": "192.168.0.1",
                "public_ssh_key": "ssh-add ABC-1",
            },
            {
                "uid": "robot-2",
                "address": "192.168.0.2",
                "public_ssh_key": "ssh-add ABC-2",
            },
            {
                "uid": "robot-3",
                "address": "192.168.0.3",
                "public_ssh_key": "ssh-add ABC-3",
            },
        ]
        for device in devices:
            self.client.post(self.url, device, format="json")
        self.assertEqual(Device.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, device in enumerate(content_json):
            self.assertEqual(devices[i]["uid"], device["uid"])
            self.assertEqual(devices[i]["address"], device["address"])
            self.assertEqual(
                devices[i]["public_ssh_key"], device["public_ssh_key"]
            )
            self.assertIsNotNone(device.get("creation_date"))
            self.assertEqual(device.get("grafana_dashboards"), [])
            self.assertEqual(device.get("foxglove_dashboards"), [])

    def test_get_devices_with_filtered_fields(self) -> None:
        devices = [
            {
                "uid": "robot-1",
                "address": "192.168.0.1",
                "public_ssh_key": "ssh-add ABC-1",
            },
            {
                "uid": "robot-2",
                "address": "192.168.0.2",
                "public_ssh_key": "ssh-add ABC-2",
            },
            {
                "uid": "robot-3",
                "address": "192.168.0.3",
                "public_ssh_key": "ssh-add ABC-3",
            },
        ]
        for device in devices:
            self.client.post(self.url, device, format="json")
        self.assertEqual(Device.objects.count(), 3)

        params = {"fields": "creation_date,address"}
        response = self.client.get(self.url, data=params)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, device in enumerate(content_json):
            self.assertIsNone(device.get("uid"))
            self.assertEqual(devices[i]["address"], device["address"])
            self.assertIsNotNone(device.get("creation_date"))

    def test_create_already_present_uid(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(uid=uid, address=address)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        # we try to create the same one
        response = self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.count(), 1)
        self.assertContains(
            response,
            '{"uid":["device with this uid already exists."]}',
            status_code=400,
        )

    def test_associate_device_with_non_existant_dashboards(
        self,
    ) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(
            uid=uid, address=address, grafana_dashboards={"dashboard-1"}
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards":["Object with uid=dashboard-1 does not exist."]}',
            status_code=400,
        )

        response = self.create_device(
            uid=uid, address=address, foxglove_dashboards={"dashboard-1"}
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_dashboards":["Object with uid=dashboard-1 does not exist."]}',
            status_code=400,
        )

    def test_dashboards_not_in_a_list(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        # we try to create the same one
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards="dashboard-1",
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards":["Expected a list of items but got type \\"str\\".',
            status_code=400,
        )

        response = self.create_device(
            uid=uid,
            address=address,
            foxglove_dashboards="dashboard-1",
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_dashboards":["Expected a list of items but got type \\"str\\".',
            status_code=400,
        )


class DeviceViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_grafana_dashboard_json = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }
        self.simple_foxglove_dashboard_json = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }
        self.grafana_dashboard = GrafanaDashboard(
            uid="dashboard-1", dashboard=self.simple_grafana_dashboard_json
        )
        self.grafana_dashboard.save()
        self.foxglove_dashboard = FoxgloveDashboard(
            uid="dashboard-1", dashboard=self.simple_foxglove_dashboard_json
        )
        self.foxglove_dashboard.save()

        self.public_ssh_key = "ssh-rsa AaBbCc/+=098765431"

    def url(self, uid: str) -> str:
        return reverse("api:device", args=(uid,))

    def create_device(self, **fields: Union[str, Set[str]]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:devices")
        return self.client.post(url, data, format="json")

    def test_get_nonexistent_device(self) -> None:
        response = self.client.get(self.url("future-robot"))
        self.assertEqual(response.status_code, 404)

    def test_get_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            public_ssh_key=self.public_ssh_key,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
        self.assertEqual(content_json["public_ssh_key"], self.public_ssh_key)
        self.assertAlmostEqual(
            datetime.fromisoformat(
                content_json["creation_date"].replace("Z", "+00:00")
            ),
            timezone.now(),
            delta=timedelta(seconds=10),
        )
        self.assertEqual(
            content_json["grafana_dashboards"], [self.grafana_dashboard.uid]
        )

        self.assertEqual(
            content_json["foxglove_dashboards"], [self.foxglove_dashboard.uid]
        )

    def test_patch_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        response = self.create_device(uid=uid, address=address)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["public_ssh_key"], "")
        address = "192.168.1.200"
        data = {"address": address, "public_ssh_key": self.public_ssh_key}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
        self.assertEqual(content_json["public_ssh_key"], self.public_ssh_key)

    def test_patch_grafana_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 0)
        data = {"grafana_dashboards": [self.grafana_dashboard.uid]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["grafana_dashboards"][0],
            self.grafana_dashboard.uid,
        )

        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().uid,
            self.grafana_dashboard.uid,
        )

    def test_patch_foxglove_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 0)
        data = {"foxglove_dashboards": [self.foxglove_dashboard.uid]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["foxglove_dashboards"][0],
            self.foxglove_dashboard.uid,
        )

        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().uid,
            self.foxglove_dashboard.uid,
        )

    def test_partial_patch_with_existing_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 1)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 1)
        data = {"address": "192.168.1.3"}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["address"],
            data["address"],
        )
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 1)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 1)

    def test_invalid_patch_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        address = "192.168.1"  # invalid IP
        data = {"address": address}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 404)


class GrafanaDashboardsViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:grafana_dashboards")

        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_dashboard(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        self.assertEqual(
            GrafanaDashboard.objects.get().uid, grafana_dashboard_uid
        )
        self.assertEqual(
            GrafanaDashboard.objects.get().dashboard,
            self.simple_grafana_dashboard,
        )

    def test_create_multiple_dashboards(self) -> None:
        dashboards = [
            {"uid": "d-1", "dashboard": '{"test1": "value"}'},
            {"uid": "d-2", "dashboard": '{"test2": "value"}'},
            {"uid": "d-3", "dashboard": '{"test3": "value"}'},
        ]
        for dashboard in dashboards:
            self.create_dashboard(
                uid=dashboard["uid"], dashboard=dashboard["dashboard"]
            )

        self.assertEqual(GrafanaDashboard.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, dashboard in enumerate(content_json):
            self.assertEqual(dashboards[i]["uid"], dashboard["uid"])
            self.assertEqual(
                json.loads(dashboards[i]["dashboard"]), dashboard["dashboard"]
            )

    def test_create_already_present_uid(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        # we try to create the same one
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        self.assertContains(
            response,
            '{"uid":["grafana dashboard with this uid already exists."]}',
            status_code=400,
        )

    def test_create_dashboard_with_illformed_json(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard='{"hello": {"test"sdsa"}}'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GrafanaDashboard.objects.count(), 0)
        self.assertContains(
            response,
            '{"dashboard":["Failed to load dashboard as json."]}',
            status_code=400,
        )

    def test_get_dashboards_associated_with_device(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.add_device(uid="robot-1").grafana_dashboards.add(
            GrafanaDashboard.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json,
            [
                {
                    "uid": grafana_dashboard_uid,
                    "dashboard": self.simple_grafana_dashboard,
                }
            ],
        )


class GrafanaDashboardViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

    def url(self, uid: str) -> str:
        return reverse("api:grafana_dashboard", args=(uid,))

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:grafana_dashboards")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_dashboard(self) -> None:
        response = self.client.get(self.url("future-dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_get_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json, self.simple_grafana_dashboard)

    def test_patch_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        data = {"dashboard": '{"test": "dash"}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], json.loads(data["dashboard"])
        )

    def test_invalid_patch_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        data = {"dashboard": '{"test": "das}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 404)


class FoxgloveDashboardsViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:foxglove_dashboards")

        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_dashboard(self) -> None:
        foxglove_dashboard_uid = "layout-1"
        response = self.create_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FoxgloveDashboard.objects.count(), 1)
        self.assertEqual(
            FoxgloveDashboard.objects.get().uid, foxglove_dashboard_uid
        )
        self.assertEqual(
            FoxgloveDashboard.objects.get().dashboard,
            self.simple_foxglove_dashboard,
        )

    def test_create_multiple_dashboards(self) -> None:
        dashboards = [
            {"uid": "l-1", "dashboard": '{"test1": "value"}'},
            {"uid": "l-2", "dashboard": '{"test2": "value"}'},
            {"uid": "l-3", "dashboard": '{"test3": "value"}'},
        ]
        for dashboard in dashboards:
            self.create_dashboard(
                uid=dashboard["uid"], dashboard=dashboard["dashboard"]
            )

        self.assertEqual(FoxgloveDashboard.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, dashboard in enumerate(content_json):
            self.assertEqual(dashboards[i]["uid"], dashboard["uid"])
            self.assertEqual(
                json.loads(dashboards[i]["dashboard"]), dashboard["dashboard"]
            )

    def test_get_dashboards_associated_with_device(self) -> None:
        foxglove_dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        self.add_device(uid="robot-1").foxglove_dashboards.add(
            FoxgloveDashboard.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json,
            [
                {
                    "uid": foxglove_dashboard_uid,
                    "dashboard": self.simple_foxglove_dashboard,
                }
            ],
        )


class FoxgloveDashboardViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

    def url(self, uid: str) -> str:
        return reverse("api:foxglove_dashboard", args=(uid,))

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:foxglove_dashboards")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_dashboard(self) -> None:
        response = self.client.get(self.url("future-dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_get_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json, self.simple_foxglove_dashboard)

    def test_patch_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        data = {"dashboard": '{"test": "dash"}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], json.loads(data["dashboard"])
        )

    def test_delete_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 404)


class PrometheusAlertRulesViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:prometheus_alert_rules")

        self.simple_prometheus_alert_rule_template = """
            groups:
              name: cos-robotics-model_robot_test_%%juju_device_uuid%%
              rules:
              alert: MyRobotTest_{{ $label.instace }}
        """

        self.simple_prometheus_alert_rule = """
            groups:
              name: cos-robotics-model_robot_NO_TEMPLATE
              rules:
              alert: MyRobotTest_{{ $label.instance }}
        """

    def create_alert_rule(self, **fields: Union[str, str]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_alert_rule_template(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(PrometheusAlertRule.objects.count(), 1)
        self.assertEqual(
            PrometheusAlertRule.objects.get().uid, prometheus_alert_rule_uid
        )
        self.assertEqual(
            PrometheusAlertRule.objects.get().rules,
            yaml.safe_load(self.simple_prometheus_alert_rule_template),
        )
        self.assertEqual(PrometheusAlertRule.objects.get().template, True)

    def test_create_alert_rule(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PrometheusAlertRule.objects.count(), 1)
        self.assertEqual(
            PrometheusAlertRule.objects.get().uid, prometheus_alert_rule_uid
        )
        self.assertEqual(
            PrometheusAlertRule.objects.get().rules,
            yaml.safe_load(self.simple_prometheus_alert_rule),
        )
        self.assertEqual(PrometheusAlertRule.objects.get().template, False)

    def test_create_multiple_alert_rules(self) -> None:
        alert_rules = [
            {"uid": "ar-1", "rules": "{'name': 'test1'}"},
            {"uid": "ar-2", "rules": "{'name': 'test2'}"},
            {"uid": "ar-3", "rules": "{'name': 'test3'}"},
        ]
        for alert_rule in alert_rules:
            self.create_alert_rule(
                uid=alert_rule["uid"], rules=alert_rule["rules"]
            )

        self.assertEqual(PrometheusAlertRule.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, alert_rule in enumerate(content_json):
            self.assertEqual(alert_rules[i]["uid"], alert_rule["uid"])
            self.assertEqual(alert_rules[i]["rules"], alert_rule["rules"])

    def test_get_alert_rule_associated_with_device(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        self.add_device(uid="robot-1").prometheus_rules_files.add(
            PrometheusAlertRule.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        ## check that it returns both rendered rule and template
        self.assertEqual(len(content_json), 2)


class PrometheusAlertRuleViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_prometheus_alert_rule_template = """
            groups:
              name: cos-robotics-model_robot_test_%%juju_device_uuid%%
              rules:
                alert: MyRobotTest_{{ $label.instace }}
        """

    def url(self, uid: str) -> str:
        return reverse("api:prometheus_alert_rule", args=(uid,))

    def create_alert_rule(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:prometheus_alert_rules")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_alert_rule(self) -> None:
        response = self.client.get(self.url("future-alert-rule"))
        self.assertEqual(response.status_code, 404)

    def test_get_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        content_yaml = yaml.safe_load(response.content)
        self.assertEqual(
            content_yaml,
            yaml.safe_load(self.simple_prometheus_alert_rule_template),
        )

    def test_patch_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        data = {"rules": "{'name': 'test'}"}
        response = self.client.patch(
            self.url(alert_rule_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_yaml = yaml.safe_load(response.content)
        self.assertEqual(content_yaml["uid"], alert_rule_uid)
        self.assertEqual(content_yaml["rules"], data["rules"])

    def test_delete_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 404)
