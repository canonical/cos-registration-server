import json
from datetime import datetime, timedelta
from typing import Any, Dict, Set, Union

from applications.models import FoxgloveDashboard, GrafanaDashboard
from devices.models import Device
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase


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
            grafana_dashboards={grafana_dashboard_uid},
            foxglove_dashboards={foxglove_dashboard_uid},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().uid, uid)
        self.assertEqual(Device.objects.get().address, address)
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
            {"uid": "robot-1", "address": "192.168.0.1"},
            {"uid": "robot-2", "address": "192.168.0.2"},
            {"uid": "robot-3", "address": "192.168.0.3"},
        ]
        for device in devices:
            self.create_device(uid=device["uid"], address=device["address"])
        self.assertEqual(Device.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, device in enumerate(content_json):
            self.assertEqual(devices[i]["uid"], device["uid"])
            self.assertEqual(devices[i]["address"], device["address"])

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
            '{"uid": ["device with this uid already exists."]}',
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
            '{"grafana_dashboards": ["Object with uid=dashboard-1 does not exist."]}',
            status_code=400,
        )

        response = self.create_device(
            uid=uid, address=address, foxglove_dashboards={"dashboard-1"}
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_dashboards": ["Object with uid=dashboard-1 does not exist."]}',
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
            '{"grafana_dashboards": ["Expected a list of items but got type \\"str\\".',
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
            '{"foxglove_dashboards": ["Expected a list of items but got type \\"str\\".',
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
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
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
        self.create_device(uid=uid, address=address)
        address = "192.168.1.200"
        data = {"address": address}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)

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
            '{"uid": ["grafana dashboard with this uid already exists."]}',
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
            '{"dashboard": ["Failed to load dashboard as json."]}',
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
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], self.simple_grafana_dashboard
        )

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
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], self.simple_foxglove_dashboard
        )

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
