import json

from devices.models import Device, default_dashboards_json_field
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

SIMPLE_GRAFANA_DASHBOARD = """{
  "dashboard": {
    "id": null,
    "uid": null,
    "title": "Production Overview",
    "tags": [ "templated" ],
    "timezone": "browser",
    "schemaVersion": 16,
    "refresh": "25s"
  },
  "message": "Made changes to xyz",
  "overwrite": false
}"""


class DevicesViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("api:devices")

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
        custom_grafana_dashboards = eval(default_dashboards_json_field())
        custom_grafana_dashboards.append(SIMPLE_GRAFANA_DASHBOARD)
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards=custom_grafana_dashboards,
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
            grafana_dashboards=SIMPLE_GRAFANA_DASHBOARD,
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


class DeviceViewTests(APITestCase):
    def url(self, uid):
        return reverse("api:device", args=(uid,))

    def create_device(self, uid, address):
        data = {"uid": uid, "address": address}
        url = reverse("api:devices")
        return self.client.post(url, data, format="json")

    def test_get_nonexistent_device(self):
        response = self.client.get(self.url("future-robot"))
        self.assertEqual(response.status_code, 404)

    def test_get_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid, address)
        response = self.client.get(self.url(uid))
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
        self.create_device(uid, address)
        address = "192.168.1.200"
        data = {"address": address}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)

    def test_patch_dashboards(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid, address)
        data = {"grafana_dashboards": [SIMPLE_GRAFANA_DASHBOARD]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["grafana_dashboards"][0],
            SIMPLE_GRAFANA_DASHBOARD,
        )
        self.assertEqual(content_json["address"], address)

    def test_invalid_patch_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid, address)
        address = "192.168.1"  # invalid IP
        data = {"address": address}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete_device(self):
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid, address)
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 404)
