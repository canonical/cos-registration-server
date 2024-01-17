import json

from devices.models import Device
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase


class DevicesViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("api:devices")

    def create_device(self, uid, address):
        data = {"uid": uid, "address": address}
        return self.client.post(self.url, data, format="json")

    def test_get_nothing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_device(self):
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(uid, address)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().uid, uid)
        self.assertEqual(Device.objects.get().address, address)
        self.assertAlmostEqual(
            Device.objects.get().creation_date,
            timezone.now(),
            delta=timezone.timedelta(seconds=10),
        )

    def test_create_multiple_devices(self):
        devices = [
            {"uid": "robot-1", "address": "192.168.0.1"},
            {"uid": "robot-2", "address": "192.168.0.2"},
            {"uid": "robot-3", "address": "192.168.0.3"},
        ]
        for device in devices:
            self.create_device(device["uid"], device["address"])
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
        response = self.create_device(uid, address)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        # we try to create the same one
        response = self.create_device(uid, address)
        self.assertEqual(Device.objects.count(), 1)
        self.assertContains(
            response, "Device uid already exists", status_code=409
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
