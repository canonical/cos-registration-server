import pytest
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
)
from devices.models import Device
from django.db.utils import IntegrityError
from django.test import TestCase

pytestmark = pytest.mark.django_db

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

SIMPLE_PROMETHEUS_ALERT_RULE = """
    groups:
        - name: cos-robotics-model_robot_test_%%juju_device_uuid%%
          rules:
            - alert: MyRobotTest_%%juju_device_uuid%%
              annotations:
              description: "The very custom description"
              summary: Not enough memory alert (instance {{ $labels.instance }})
              expr: (node_memory_MemFree_bytes{device_instance="%%juju_device_uuid%%"})/1e9 < 30
              for: 5m
              severity: critical
"""

SIMPLE_LOKI_ALERT_RULE = """
    groups:
        - name: cos-robotics-model_high_log_rate_per_instance
	      rules:
  	        - alert: HighLogRatePerInstance
              expr: rate({job="loki.source.journal.read", instance="robot-1"}[5m]) > 100
              for: 10m
              labels:
                severity: warning
              annotations:
              summary: High log rate detected for instance {{ $labels.instance }}
"""


class TestFarmApp:
    def test_plot_detail_create(self):
        assert 1 == 1


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
        GrafanaDashboard(uid=dashboard_name, dashboard=SIMPLE_GRAFANA_DASHBOARD).save()

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
        self.assertEqual(foxglove_dashboard.dashboard, SIMPLE_FOXGLOVE_DASHBOARD)

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


class PrometheusAlertRuleFileModelTests(TestCase):
    def test_creation_of_alert_rule(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRuleFile(
            uid=alert_name, rules=SIMPLE_PROMETHEUS_ALERT_RULE
        )
        self.assertEqual(prometheus_alert_rule.uid, alert_name)
        self.assertEqual(prometheus_alert_rule.rules, SIMPLE_PROMETHEUS_ALERT_RULE)

    def test_device_from_an_alert_rule(self) -> None:
        alert_name = "first_alert"
        prometheus_alert_rule = PrometheusAlertRuleFile(
            uid=alert_name, rules=SIMPLE_PROMETHEUS_ALERT_RULE
        )
        prometheus_alert_rule.save()
        device = Device(uid="robot", address="127.0.0.1")
        device.save()
        device.prometheus_alert_rule_files.add(prometheus_alert_rule)

        self.assertEqual(prometheus_alert_rule.devices.all()[0].uid, "robot")


class LokiAlertRuleFileModelTests(TestCase):
    def test_creation_of_alert_rule(self) -> None:
        alert_name = "first_alert"
        loki_alert_rule = LokiAlertRuleFile(
            uid=alert_name, rules=SIMPLE_LOKI_ALERT_RULE
        )
        self.assertEqual(loki_alert_rule.uid, alert_name)
        self.assertEqual(loki_alert_rule.rules, SIMPLE_LOKI_ALERT_RULE)

    def test_device_from_an_alert_rule(self) -> None:
        alert_name = "first_alert"
        loki_alert_rule = LokiAlertRuleFile(
            uid=alert_name, rules=SIMPLE_LOKI_ALERT_RULE
        )
        loki_alert_rule.save()
        device = Device(uid="robot", address="127.0.0.1")
        device.save()
        device.loki_alert_rule_files.add(loki_alert_rule)

        self.assertEqual(loki_alert_rule.devices.all()[0].uid, "robot")
