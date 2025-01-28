"""Device DB model."""

from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    PrometheusAlertRule,
)
from django.db import models


class Device(models.Model):
    """Device model.

    This class represent a device in the DB.

    uid: Unique ID of the device.
    creation_date: Creation date of the device.
    address: IP address of the device.
    public_ssh_key: device public SSH key.
    grafana_dashboards: Grafana dashboards relations.
    foxglove_dashboards: Foxglove dashboards relations.
    prometheus_alert_rule: Prometheus alert rules relations.
    """

    uid = models.CharField(max_length=200, unique=True)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")
    public_ssh_key = models.TextField("device public SSH key", default="")
    grafana_dashboards = models.ManyToManyField(
        GrafanaDashboard, related_name="devices"
    )
    foxglove_dashboards = models.ManyToManyField(
        FoxgloveDashboard, related_name="devices"
    )
    prometheus_rules_files = models.ManyToManyField(
        PrometheusAlertRule, related_name="devices"
    )

    def __str__(self) -> str:
        """Str representation of a device."""
        return self.uid
