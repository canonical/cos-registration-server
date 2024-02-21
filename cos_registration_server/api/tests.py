import json
from os import mkdir, path
from pathlib import Path
from shutil import rmtree

from devices.models import (
    Device,
    default_dashboards_json_field,
    default_layouts_json_field,
)
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase


class DevicesViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("api:devices")
        self.grafana_dashboards_path = Path("grafana_dashboards")
        rmtree(self.grafana_dashboards_path, ignore_errors=True)
        mkdir(self.grafana_dashboards_path)

        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

        self.simple_foxglove_layouts = {
            "simple_layout": {
                "configById": {},
                "globalVariables": {},
                "userNodes": {},
                "playbackConfig": {"speed": 1},
            }
        }

    def create_device(self, **fields):
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def test_get_nothing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_device(self):
        uid = "robot-1"
        address = "192.168.0.1"
        custom_grafana_dashboards = default_dashboards_json_field()
        custom_grafana_dashboards.append(self.simple_grafana_dashboard)
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards=custom_grafana_dashboards,
            foxglove_layouts=self.simple_foxglove_layouts,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().uid, uid)
        self.assertEqual(Device.objects.get().address, address)
        self.assertAlmostEqual(
            Device.objects.get().creation_date,
            timezone.now(),
            delta=timezone.timedelta(seconds=10),
        )
        self.assertEqual(
            Device.objects.get().grafana_dashboards, custom_grafana_dashboards
        )
        with open(
            self.grafana_dashboards_path / "robot-1-Production_Overview.json",
            "r",
        ) as file:
            dashboard_data = json.load(file)
            self.simple_grafana_dashboard[
                "title"
            ] = f'{uid}-{self.simple_grafana_dashboard["title"]}'
            self.assertEqual(dashboard_data, self.simple_grafana_dashboard)
        self.assertEqual(
            Device.objects.get().foxglove_layouts, self.simple_foxglove_layouts
        )

    def test_create_multiple_devices(self):
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

    def test_create_already_present_uid(self):
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
            '{"uid": ["This field must be unique."]}',
            status_code=400,
        )

    def test_grafana_dashboard_not_in_a_list(self):
        uid = "robot-1"
        address = "192.168.0.1"
        # we try to create the same one
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards=self.simple_grafana_dashboard,
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards": ["gafana_dashboards is not a supported '
            "format (list).",
            status_code=400,
        )

    def test_grafana_dashboard_illformed_json(self):
        uid = "robot-1"
        address = "192.168.0.1"
        # we try to create the same one
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards='[{"hello"=321}',
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards": ["Failed to load grafana_dashboards '
            "as json.",
            status_code=400,
        )

    def test_foxglove_layouts_not_in_a_dict(self):
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(
            uid=uid,
            address=address,
            foxglove_layouts=[self.simple_foxglove_layouts],
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_layouts": ["foxglove_layouts is not a supported '
            "format (dict).",
            status_code=400,
        )

    def test_foxglove_layouts_illformed_json(self):
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(
            uid=uid,
            address=address,
            foxglove_layouts='{{"hello"=321}',
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_layouts": ["Failed to load foxglove_layouts '
            "as json.",
            status_code=400,
        )

    def test_foxglove_layouts_not_a_layout(self):
        uid = "robot-1"
        address = "192.168.0.1"
        custom_foxglove_layouts = {"layout": "not a layout"}
        response = self.create_device(
            uid=uid,
            address=address,
            foxglove_layouts=custom_foxglove_layouts,
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_layouts": '
            '["foxglove_layouts should be passed with a name. \
                    {\\"my_name\\": {foxglove_layout...} }"]}',
            status_code=400,
        )


class DeviceViewTests(APITestCase):
    def setUp(self):
        self.grafana_dashboards_path = Path("grafana_dashboards")
        rmtree(self.grafana_dashboards_path, ignore_errors=True)
        mkdir(self.grafana_dashboards_path)
        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

        self.simple_foxglove_layouts = {
            "simple_layout": {
                "configById": {},
                "globalVariables": {},
                "userNodes": {},
                "playbackConfig": {"speed": 1},
            }
        }

    def url_device(self, uid):
        return reverse("api:device", args=(uid,))

    def create_device(self, **fields):
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:devices")
        return self.client.post(url, data, format="json")

    def test_get_nonexistent_device(self):
        response = self.client.get(self.url_device("future-robot"))
        self.assertEqual(response.status_code, 404)

    def test_get_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        response = self.client.get(self.url_device(uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
        self.assertAlmostEqual(
            timezone.datetime.fromisoformat(
                content_json["creation_date"].replace("Z", "+00:00")
            ),
            timezone.now(),
            delta=timezone.timedelta(seconds=10),
        )

    def test_patch_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        address = "192.168.1.200"
        data = {"address": address}
        response = self.client.patch(self.url_device(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)

    def test_patch_grafana_dashboards(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        data = {"grafana_dashboards": [self.simple_grafana_dashboard]}
        response = self.client.patch(self.url_device(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        # necessary since patching returns the modified title
        self.simple_grafana_dashboard[
            "title"
        ] = f'{uid}-{self.simple_grafana_dashboard["title"]}'
        self.assertEqual(
            content_json["grafana_dashboards"][0],
            self.simple_grafana_dashboard,
        )
        self.assertEqual(content_json["address"], address)
        with open(
            self.grafana_dashboards_path / "robot-1-Production_Overview.json",
            "r",
        ) as file:
            dashboard_data = json.load(file)
            self.assertEqual(dashboard_data, self.simple_grafana_dashboard)

    def test_patch_foxglove_layouts(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        data = {"foxglove_layouts": self.simple_foxglove_layouts}
        response = self.client.patch(self.url_device(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["foxglove_layouts"],
            self.simple_foxglove_layouts,
        )

    def test_invalid_patch_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        address = "192.168.1"  # invalid IP
        data = {"address": address}
        response = self.client.patch(self.url_device(uid), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards=[self.simple_grafana_dashboard],
        )
        response = self.client.get(self.url_device(uid))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            path.isfile(
                self.grafana_dashboards_path
                / "robot-1-Production_Overview.json"
            )
        )
        response = self.client.delete(self.url_device(uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url_device(uid))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            path.isfile(
                self.grafana_dashboards_path
                / "robot-1-Production_Overview.json"
            )
        )

    def test_get_foxglove_layout(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            foxglove_layouts=self.simple_foxglove_layouts,
        )
        response = self.client.get(
            reverse("api:foxglove_layout", args=(uid, "simple_layout"))
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json, self.simple_foxglove_layouts["simple_layout"]
        )

    def test_get_wrong_foxglove_dashboard(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            foxglove_layouts=self.simple_foxglove_layouts,
        )
        response = self.client.get(
            reverse("api:foxglove_layout", args=(uid, "wrong_layout"))
        )
        self.assertEqual(response.status_code, 404)


class CommandsTestCase(TestCase):
    def setUp(self):
        self.grafana_dashboards_path = Path("grafana_dashboards")
        rmtree(self.grafana_dashboards_path, ignore_errors=True)
        mkdir(self.grafana_dashboards_path)
        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

    def test_update_all_dashboards(self):
        robot_1 = Device(
            uid="robot-1",
            address="127.0.0.1",
            grafana_dashboards=[self.simple_grafana_dashboard],
        )
        robot_1.save()
        robot_2 = Device(
            uid="robot-2",
            address="127.0.0.1",
            grafana_dashboards=[self.simple_grafana_dashboard],
        )
        robot_2.save()
        call_command("update_all_grafana_dashboards")
        self.assertTrue(
            path.isfile(
                self.grafana_dashboards_path
                / "robot-1-Production_Overview.json"
            )
        )
        self.assertTrue(
            path.isfile(
                self.grafana_dashboards_path
                / "robot-2-Production_Overview.json"
            )
        )
