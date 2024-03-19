from devices.models import Device
from django.db.utils import IntegrityError
from django.test import TestCase

from .models import FoxgloveDashboard, GrafanaDashboard

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
