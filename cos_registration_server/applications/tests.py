from devices.models import Device
from django.db.utils import IntegrityError
from django.test import TestCase

from .models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRule,
    PrometheusAlertRule,
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

SIMPLE_FOXGLOVE_DASHBOARD = {
    "configById": {},
    "globalVariables": {},
    "userNodes": {},
    "playbackConfig": {"speed": 1},
}

SIMPLE_ALERT_RULE = """
    groups:
        - name: cos-robotics-model_robot_test_{{ $cos.device.uid }} # robot specific alert
        rules:
            - alert: MyRobotTest_{{ $cos.instance }}
            annotations:
            description: "The very custom description"
            summary: Not enough memory alert (instance {{ $labels.instance }})
            expr: (node_memory_MemFree_bytes{device_instance="${{ $cos.instance }}"})/1e9 < 30
            for: 5m
            severity: critical
"""


class GrafanaDashboardModelTests(TestCase):
    def test_creation_of_a_dashboard(self) -> None:
        dashboard_name = "first_dashboard"
        grafana_dashboard = GrafanaDashboard(
            uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        self.assertEqual(grafana_dashboard.uid, dashboard_name)
        self.assertEqual(grafana_dashboard.dashboard, SIMPLE_GRAFANA_DASHBOARD)

    def test_dashboard_str(self) -> None:
        dashboard_name = "first_dashboard"
        grafana_dashboard = GrafanaDashboard(
            uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        self.assertEqual(str(grafana_dashboard), dashboard_name)

    def test_dashboard_uid_uniqueness(self) -> None:
        dashboard_name = "first_dashboard"
        GrafanaDashboard(
            uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD
        ).save()

        self.assertRaises(
            IntegrityError,
            GrafanaDashboard(
                uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD
            ).save,
        )

    def test_device_from_a_dashboard(self) -> None:
        dashboard_name = "first_dashboard"
        grafana_dashboard = GrafanaDashboard(
            uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD
        )
        grafana_dashboard.save()
        device = Device(uid="robot", address="127.0.0.1")
        device.save()
        device.grafana_dashboards.add(grafana_dashboard)

        self.assertEqual(grafana_dashboard.devices.all()[0].uid, "robot")


class FoxgloveDashboardModelTests(TestCase):
    def test_creation_of_a_dashboard(self) -> None:
        dashboard_name = "first_dashboard"
        foxglove_dashboard = FoxgloveDashboard(
            uid=dashboard_name, dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        self.assertEqual(foxglove_dashboard.uid, dashboard_name)
        self.assertEqual(
            foxglove_dashboard.dashboard, SIMPLE_FOXGLOVE_DASHBOARD
        )

    def test_device_from_a_dashboard(self) -> None:
        dashboard_name = "first_dashboard"
        foxglove_dashboard = FoxgloveDashboard(
            uid=dashboard_name, dashboard=SIMPLE_FOXGLOVE_DASHBOARD
        )
        foxglove_dashboard.save()
        device = Device(uid="robot", address="127.0.0.1")
        device.save()
        device.foxglove_dashboards.add(foxglove_dashboard)

        self.assertEqual(foxglove_dashboard.devices.all()[0].uid, "robot")


class PrometheusAlertRuleModelTests(TestCase):
    def test_creation_of_alert_rule(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRule(
            uid=alert_name, rules=SIMPLE_ALERT_RULE
        )
        self.assertEqual(prometheus_alert_rule.uid, alert_name)
        self.assertEqual(prometheus_alert_rule.rules, SIMPLE_ALERT_RULE)

    def test_alert_rule_from_a_dashboard(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRule(
            uid=alert_name, rules=SIMPLE_ALERT_RULE
        )
        prometheus_alert_rule.save()
        device = Device(uid="robot", address="127.0.0.1")
        device.save()
        device.prometheus_rules_files.add(prometheus_alert_rule)

        self.assertEqual(prometheus_alert_rule.devices.all()[0].uid, "robot")


class LokiAlertRuleModelTests(TestCase):
    def test_creation_of_alert_rule(self) -> None:
        alert_name = "first_alert"
        loki_alert_rule = LokiAlertRule(
            uid=alert_name, rules=SIMPLE_ALERT_RULE
        )
        self.assertEqual(loki_alert_rule.uid, alert_name)
        self.assertEqual(loki_alert_rule.rules, SIMPLE_ALERT_RULE)
