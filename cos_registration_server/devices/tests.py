import re
from datetime import timedelta
from html import escape

import yaml
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
)
from django.db.utils import IntegrityError
from django.test import Client, TestCase, override_settings
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

PUBLIC_RSA_KEY = """"ssh-rsa \
AAAAB3NzaC1yc2EAAAADAQABAAABAQCr53T3FlR201z70sjGiJqDUvTMiX3AJog3OuiYMUT\
26EnlJ8mA13VaBWb9VCCaY8ZF6pSyMYWcSyMhs2It5KvOUS9qJq8/xxZxhGKmtKRPFYTFjI\
EYn2qdU5C7GsIiwmFpgGCFkBE1bAwjepQar6NTBC3Blc1zjy6dCMdgQHjHhw26UIG3kmKTS\
I0nZLgqhU8dXB+lJS9pd6hljL1rfacJOUSshgXcVvd37kW02WdCs3YidfKkjgaFA5sNmevH\
kK2t2rwLPZmlBZ+P5faO5sDe2gS3jCqCo9Qd/1QagTRliRnnmPa6RpMVw9lF1SWYFSmXEsy\
YkkbhmeJAiNclXL6H"""

SIMPLE_PROMETHEUS_ALERT_RULE_TEMPLATE = """
    groups:
        name: cos-robotics-model_robot_test_%%juju_device_uuid%%
        rules:
        alert: MyRobotTest_{{ $label.instace }}
        expr: (node_memory_MemFree_bytes{device_instance="%%juju_device_uuid%%"})/1e9 < 30
"""

SIMPLE_PROMETHEUS_ALERT_RULE = """
    groups:
        name: cos-robotics-model_robot
        rules:
        alert: MyRobotTest_{{ $label.instance }}
        expr: (node_memory_MemFree_bytes{device_instance="robot"})/1e9 < 30
"""

SIMPLE_LOKI_ALERT_RULE_TEMPLATE = """
    groups:
        name: cos-robotics-model_robot_test_%%juju_device_uuid%%
        rules:
        alert: MyRobotTest_{{ $label.instace }}
        expr: rate({job="loki.source.journal.read", instance="robot-1"}[5m]) > 100
"""

SIMPLE_LOKI_ALERT_RULE = """
    groups:
        name: cos-robotics-model_robot
        rules:
        alert: MyRobotTest_{{ $label.instance }}
        expr: rate({job="loki.source.journal.read", instance="robot-1"}[5m]) > 100
"""


class DeviceModelTests(TestCase):
    def test_creation_of_a_device(self) -> None:
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
            public_ssh_key=PUBLIC_RSA_KEY,
        )
        device.save()
        self.assertEqual(device.uid, "hello-123")
        self.assertEqual(str(device.address), "127.0.0.1")
        self.assertEqual(str(device.public_ssh_key), PUBLIC_RSA_KEY)
        self.assertLessEqual(device.creation_date, timezone.now())
        self.assertGreater(
            device.creation_date, timezone.now() - timedelta(hours=1)
        )
        self.assertEqual(len(device.grafana_dashboards.all()), 0)
        self.assertEqual(len(device.foxglove_dashboards.all()), 0)

    def test_device_str(self) -> None:
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
            public_ssh_key=PUBLIC_RSA_KEY,
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

    def test_device_create_prometheus_alert_rule(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRuleFile(
            uid=alert_name, rules=SIMPLE_PROMETHEUS_ALERT_RULE_TEMPLATE
        )
        prometheus_alert_rule.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.prometheus_alert_rule_files.add(prometheus_alert_rule)
        self.assertEqual(
            device.prometheus_alert_rule_files.all()[0].uid,
            "first_alert",
        )
        self.assertEqual(
            device.prometheus_alert_rule_files.all()[0].rules,
            yaml.safe_load(SIMPLE_PROMETHEUS_ALERT_RULE_TEMPLATE),
        )

    def test_device_relate_prometheus_alert_rules(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRuleFile(
            uid=alert_name, rules=SIMPLE_PROMETHEUS_ALERT_RULE
        )
        prometheus_alert_rule.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.prometheus_alert_rule_files.add(prometheus_alert_rule)
        self.assertEqual(
            device.prometheus_alert_rule_files.all()[0].uid,
            alert_name,
        )
        self.assertEqual(
            device.prometheus_alert_rule_files.all()[0].rules,
            yaml.safe_load(SIMPLE_PROMETHEUS_ALERT_RULE),
        )

    def test_device_create_loki_alert_rule(self) -> None:
        alert_name = "first_alert"
        loki_alert_rule = LokiAlertRuleFile(
            uid=alert_name, rules=SIMPLE_LOKI_ALERT_RULE_TEMPLATE
        )
        loki_alert_rule.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.loki_alert_rule_files.add(loki_alert_rule)
        self.assertEqual(
            device.loki_alert_rule_files.all()[0].uid,
            "first_alert",
        )
        self.assertEqual(
            device.loki_alert_rule_files.all()[0].rules,
            yaml.safe_load(SIMPLE_LOKI_ALERT_RULE_TEMPLATE),
        )

    def test_device_relate_loki_alert_rules(self) -> None:
        alert_name = "first_alert"
        loki_alert_rule = LokiAlertRuleFile(
            uid=alert_name, rules=SIMPLE_LOKI_ALERT_RULE
        )
        loki_alert_rule.save()
        device = Device(
            uid="hello-123", creation_date=timezone.now(), address="127.0.0.1"
        )
        device.save()
        device.loki_alert_rule_files.add(loki_alert_rule)
        self.assertEqual(
            device.loki_alert_rule_files.all()[0].uid,
            alert_name,
        )
        self.assertEqual(
            device.loki_alert_rule_files.all()[0].rules,
            yaml.safe_load(SIMPLE_LOKI_ALERT_RULE),
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
        self.assertContains(response, "2 device(s):")
        self.assertContains(response, "robot-1")
        self.assertContains(response, "robot-2")
        self.assertQuerySetEqual(
            list(response.context["devices_list"]), [device_1, device_2]
        )

    def test_one_device_then_two(self) -> None:
        device_1 = create_device("robot-1", "192.168.0.1")

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 device(s):")
        self.assertQuerySetEqual(response.context["devices_list"], [device_1])

        device_2 = create_device("robot-2", "192.168.0.2")

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 device(s):")
        self.assertQuerySetEqual(
            list(response.context["devices_list"]), [device_1, device_2]
        )

    def test_devices_pagination(self) -> None:
        total_number_of_devices = 40
        max_devices_per_page = 25
        devices = []
        for i in range(0, total_number_of_devices):
            devices.append(create_device(f"robot-{i}", "192.168.0.1"))

        response = self.client.get(reverse("devices:devices"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"] == True)
        self.assertContains(response, f"{total_number_of_devices} device(s):")
        self.assertEqual(
            len(response.context["devices_list"]), max_devices_per_page
        )

        response = self.client.get(reverse("devices:devices") + "?page=2")
        self.assertEqual(response.status_code, 200)
        # The second and last page has less devices
        self.assertEqual(
            len(response.context["devices_list"]),
            total_number_of_devices - max_devices_per_page,
        )


@override_settings(COS_MODEL_NAME="cos")
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
        pattern = re.compile(
            rf"Device {device.uid} with ip {device.address}, was created on the (?:[A-Za-z]+\.?) {device.creation_date.day}, {device.creation_date.year}, \d{{1,2}}:\d{{2}} (?:a\.m\.|am|p\.m\.|pm)"
        )
        self.assertRegex(response.content.decode(), pattern)
        self.assertContains(
            response,
            self.base_url + "/cos-grafana/dashboards/",
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
        grafana_dashboard = GrafanaDashboard(
            uid="dashboard-1", dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        grafana_dashboard.save()
        foxglove_dashboard = FoxgloveDashboard(
            uid="layout-1", dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        foxglove_dashboard.save()
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
        )
        device.save()
        device.grafana_dashboards.add(grafana_dashboard)
        device.foxglove_dashboards.add(foxglove_dashboard)
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
            + "applications%2Ffoxglove%2Fdashboards%2Flayout-1",
        )
        self.assertContains(
            response,
            self.base_url + "/cos-grafana/d/dashboard-1/?var-Host=hello-123",
        )

    def test_listed_device_additional_links_https(self) -> None:
        grafana_dashboard = GrafanaDashboard(
            uid="dashboard-1", dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        grafana_dashboard.save()
        foxglove_dashboard = FoxgloveDashboard(
            uid="layout-1", dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        foxglove_dashboard.save()
        device = Device(
            uid="hello-123",
            creation_date=timezone.now(),
            address="127.0.0.1",
        )
        device.save()
        device.grafana_dashboards.add(grafana_dashboard)
        device.foxglove_dashboards.add(foxglove_dashboard)

        url = reverse("devices:device", args=(device.uid,))

        # Simulate HTTPS request
        response = self.client.get(url, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.base_url
            + "/cos-foxglove-studio/"
            + escape("?ds=foxglove-websocket&ds.url=wss%3A%2F%2F")
            + device.address
            + "%3A8765"
            + escape("&layoutUrl=")
            + f"127.0.0.1%3A8080%2Fcos-cos-registration-server%2Fapi%2Fv1%2F"
            + "applications%2Ffoxglove%2Fdashboards%2Flayout-1",
        )
        self.assertContains(
            response,
            'href="https://127.0.0.1:8080/cos-grafana/d/dashboard-1/?var-Host=hello-123"',
        )
        self.assertContains(
            response,
            'href="https://127.0.0.1:8080/cos-ros2bag-fileserver/hello-123/"',
        )
