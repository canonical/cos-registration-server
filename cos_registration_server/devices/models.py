"""Device DB model."""

from applications.models import FoxgloveDashboard, GrafanaDashboard
from django.db import models


class Device(models.Model):
    """Device model.

    This class represent a device in the DB.

    uid: Unique ID of the device.
    creation_date: Creation date of the device.
    address: IP address of the device.
    grafana_dashboards: Grafana dashboards relations.
    foxglove_dashboards: Foxglove dashboards relations.
    """

    uid = models.CharField(max_length=200, unique=True)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")
    grafana_dashboards = models.ManyToManyField(
        GrafanaDashboard, related_name="devices"
    )
    foxglove_dashboards = models.ManyToManyField(
        FoxgloveDashboard, related_name="devices"
    )

    def __str__(self) -> str:
        """Str representation of a device."""
        return self.uid
