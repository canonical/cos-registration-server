from datetime import timedelta
from html import escape

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Device,
    default_dashboards_json_field,
    default_layouts_json_field,
)

SIMPLE_GRAFANA_DASHBOARD = {
    "id": None,
    "uid": None,
    "title": "Production Overview",
    "tags": ["templated"],
    "timezone": "browser",
    "schemaVersion": 16,
    "refresh": "25s",
}

SIMPLE_FOXGLOVE_LAYOUTS = {
    "simple_layout": {
        "configById": {},
        "globalVariables": {},
        "userNodes": {},
        "playbackConfig": {"speed": 1},
    }
}


class DeviceModelTests(TestCase):
    def test_creation_of_a_device(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        self.assertEqual(device.uid, "hello-123")
        self.assertEqual(str(device.address), "127.0.0.1")
        self.assertLessEqual(device.creation_date, timezone.now())
        self.assertGreater(
            device.creation_date, timezone.now() - timedelta(hours=1)
        )
        self.assertEquals(
            device.grafana_dashboards, default_dashboards_json_field()
        )
        self.assertEquals(
            device.foxglove_layouts, default_layouts_json_field()
        )

    def test_device_str(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        self.assertEqual(str(device), "hello-123")

    def test_device_grafana_dashboards(self) -> None:
        custom_grafana_dashboards = default_dashboards_json_field()
        custom_grafana_dashboards.append(SIMPLE_GRAFANA_DASHBOARD)
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
            grafana_dashboards=custom_grafana_dashboards,
        )
        self.assertEqual(
            device.grafana_dashboards[0],
            SIMPLE_GRAFANA_DASHBOARD,
        )

    def test_device_foxglove_layouts(self) -> None:
        custom_foxglove_layouts = SIMPLE_FOXGLOVE_LAYOUTS
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
            foxglove_layouts=custom_foxglove_layouts,
        )
        self.assertEqual(
            device.foxglove_layouts,
            SIMPLE_FOXGLOVE_LAYOUTS,
        )


def create_device(uid: str, address: str) -> Device:
    return Device.objects.create(uid=uid, address=address)


class DevicesViewTests(TestCase):
    def test_no_devices(self) -> None:
        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No devices are available.")
        self.assertQuerySetEqual(response.context["devices_list"], [])

    def test_two_devices(self) -> None:
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

    def test_one_device_then_two(self) -> None:
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
    def setUp(self) -> None:
        # custom client with META HTTP_HOST specified
        self.base_url = "127.0.0.1:8080"
        self.client = Client(HTTP_HOST=self.base_url)

    def test_unlisted_device(self) -> None:
        url = reverse("devices:device", args=("future-robot",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "device future-robot not found")

    def test_listed_device(self) -> None:
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
            response,
            self.base_url + "/cos-grafana/dashboards/?query=" + device.uid,
        )
        self.assertContains(
            response,
            self.base_url
            + "/cos-foxglove-studio/"
            + escape("?ds=foxglove-websocket&ds.url=ws%3A%2F%2F")
            + device.address
            + "%3A8765",
        )

        self.assertContains(
            response, self.base_url + "/cos-ros2bag-fileserver/" + device.uid
        )

    def test_listed_device_additional_links(self) -> None:
        custom_grafana_dashboards = default_dashboards_json_field()
        custom_grafana_dashboards.append(SIMPLE_GRAFANA_DASHBOARD)
        custom_grafana_dashboards[0]["uid"] = "123"
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
            grafana_dashboards=custom_grafana_dashboards,
            foxglove_layouts=SIMPLE_FOXGLOVE_LAYOUTS,
        )
        device.save()
        url = reverse("devices:device", args=(device.uid,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.base_url
            + "/cos-foxglove-studio/"
            + escape("?ds=foxglove-websocket&ds.url=ws%3A%2F%2F")
            + device.address
            + "%3A8765"
            + escape("&layoutUrl=")
            + f"127.0.0.1%3A8080%2Fcos-cos-registration-server%2Fapi%2Fv1%2F"
            + "devices%2Fhello-123%2Ffoxglove_layouts%2Fsimple_layout",
        )

        self.assertContains(
            response,
            self.base_url + "/cos-grafana/dashboards/123",
        )
