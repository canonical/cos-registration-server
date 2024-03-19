"""Applications DB model."""

from django.db import models


class Dashboard(models.Model):
    """Application dashboard.

    This class represent an application dashboard in the DB.

    uid: Unique ID of the dashboard.
    dashboard: Dashboard JSON.
    """

    uid = models.CharField(max_length=200, unique=True)
    dashboard = models.JSONField("Dashboard json field")

    class Meta:
        """Model Meta class overwritting."""

        abstract = True

    def __str__(self):
        """Str representation of a dashboard."""
        return self.uid


class GrafanaDashboard(Dashboard):  # noqa: DJ08
    """Grafana dashboard.

    This class represent a Grafana dashboard in the DB.

    uid: Unique ID of the dashboard.
    dashboard: Dashboard JSON.
    """
