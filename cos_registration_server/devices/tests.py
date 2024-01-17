from html import escape

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Device


class DeviceModelTests(TestCase):
    def test_creation_of_a_device(self):
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        self.assertEqual(device.uid, "hello-123")
        self.assertEqual(str(device.address), "127.0.0.1")
        self.assertLessEqual(device.creation_date, timezone.now())
        self.assertGreater(
            device.creation_date, timezone.now() - timezone.timedelta(hours=1)
        )

    def test_device_str(self):
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        self.assertEqual(str(device), "hello-123")


def create_device(uid, address):
    return Device.objects.create(uid=uid, address=address)


class DevicesViewTests(TestCase):
    def test_no_devices(self):
        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No devices are available.")
        self.assertQuerySetEqual(response.context["devices_list"], [])

    def test_two_devices(self):
        device_1 = create_device("robot-1", "192.168.0.1")
        device_2 = create_device("robot-2", "192.168.0.2")

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Devices list:")
        self.assertContains(response, "robot-1")
        self.assertContains(response, "robot-2")
        self.assertQuerySetEqual(
            list(response.context["devices_list"]), [device_1, device_2]
        )

    def test_one_device_then_two(self):
        device_1 = create_device("robot-1", "192.168.0.1")

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Devices list:")
        self.assertQuerySetEqual(response.context["devices_list"], [device_1])

        device_2 = create_device("robot-2", "192.168.0.2")

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Devices list:")
        self.assertQuerySetEqual(
            list(response.context["devices_list"]), [device_1, device_2]
        )


class DeviceViewTests(TestCase):
    def setUp(self):
        # custom client with META HTTP_HOST specified
        self.base_url = "192.168.1.2:8080"
        self.client = Client(HTTP_HOST=self.base_url)

    def test_unlisted_device(self):
        url = reverse("devices:device", args=("future-robot",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "device future-robot not found")

    def test_listed_device(self):
        device = create_device("robot-1", "192.168.0.23")
        url = reverse("devices:device", args=(device.uid,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"Device {device.uid} with ip {device.address}, was created on the"
            f" {device.creation_date.strftime('%b. %d, %Y, %-I')}",
        )
        self.assertContains(
            response, self.base_url + "/cos-grafana/f/" + device.uid + "/"
        )
        self.assertContains(
            response,
            self.base_url
            + "/cos-foxglove-studio/"
            + escape("?ds=foxglove-websocket&ds.url=ws%3A%2F%2F")
            + device.address
            + "%3A8765/",
        )
