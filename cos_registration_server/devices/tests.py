from datetime import timedelta
from html import escape

from applications.models import FoxgloveDashboard, GrafanaDashboard
from django.db.utils import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Device

SIMPLE_GRAFANA_DASHBOARD = {
    "id": None,
    "uid": None,
    "title": "Production Overview",
    "tags": ["templated"],
    "timezone": "browser",
    "schemaVersion": 16,
    "refresh": "25s",
}

SIMPLE_FOXGLOVE_DASHBOARD = {
    "configById": {},
    "globalVariables": {},
    "userNodes": {},
    "playbackConfig": {"speed": 1},
}


class DeviceModelTests(TestCase):
    def test_creation_of_a_device(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        self.assertEqual(device.uid, "hello-123")
        self.assertEqual(str(device.address), "127.0.0.1")
        self.assertLessEqual(device.creation_date, timezone.now())
        self.assertGreater(
            device.creation_date, timezone.now() - timedelta(hours=1)
        )
        self.assertEqual(len(device.grafana_dashboards.all()), 0)
        self.assertEqual(len(device.foxglove_dashboards.all()), 0)

    def test_device_str(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        self.assertEqual(str(device), "hello-123")

    def test_device_create_grafana_dashboards(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.grafana_dashboards.create(
            uid="first_dashboard", dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        self.assertEqual(
            device.grafana_dashboards.all()[0].uid,
            "first_dashboard",
        )
        self.assertEqual(
            device.grafana_dashboards.all()[0].dashboard,
            SIMPLE_GRAFANA_DASHBOARD,
        )

    def test_device_create_foxglove_dashboards(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.foxglove_dashboards.create(
            uid="first_dashboard", dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        self.assertEqual(
            device.foxglove_dashboards.all()[0].uid,
            "first_dashboard",
        )
        self.assertEqual(
            device.foxglove_dashboards.all()[0].dashboard,
            SIMPLE_FOXGLOVE_DASHBOARD,
        )

    def test_device_create_grafana_dashboards_then_delete_device(self) -> None:
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.grafana_dashboards.create(
            uid="first_dashboard", dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        device.delete()
        self.assertEqual(
            GrafanaDashboard.objects.all()[0].uid,
            "first_dashboard",
        )

    def test_device_relate_grafana_dashboards(self) -> None:
        grafana_dashboard = GrafanaDashboard(
            uid="first_dashboard", dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        grafana_dashboard.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.grafana_dashboards.add(grafana_dashboard)
        self.assertEqual(
            device.grafana_dashboards.all()[0].uid,
            "first_dashboard",
        )
        self.assertEqual(
            device.grafana_dashboards.all()[0].dashboard,
            SIMPLE_GRAFANA_DASHBOARD,
        )

    def test_device_relate_foxglove_dashboards(self) -> None:
        foxglove_dashboard = FoxgloveDashboard(
            uid="first_dashboard", dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        foxglove_dashboard.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.foxglove_dashboards.add(foxglove_dashboard)
        self.assertEqual(
            device.foxglove_dashboards.all()[0].uid,
            "first_dashboard",
        )
        self.assertEqual(
            device.foxglove_dashboards.all()[0].dashboard,
            SIMPLE_FOXGLOVE_DASHBOARD,
        )

    def test_device_uid_uniqueness(self) -> None:
        uid = "123"
        Device(uid=uid, address="127.0.0.1").save()

        self.assertRaises(
            IntegrityError,
            Device(uid=uid, address="192.168.0.1").save,
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
            f" {device.creation_date.strftime('%B %d, %Y, %-I')}",
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
