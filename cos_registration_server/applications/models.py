"""Applications DB model."""

from django.db import models

from .fields import YAMLField


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

    def __str__(self) -> str:
        """Str representation of a dashboard."""
        return self.uid


class GrafanaDashboard(Dashboard):  # noqa: DJ08
    """Grafana dashboard.

    This class represent a Grafana dashboard in the DB.

    uid: Unique ID of the dashboard.
    dashboard: Dashboard JSON.
    """


class FoxgloveDashboard(Dashboard):  # noqa: DJ08
    """Foxglove dashboard.

    This class represent a Foxglove dashboard in the DB.

    uid: Unique ID of the dashboard.
    dashboard: Dashboard JSON.
    """


class AlertRule(models.Model):
    """Application alert rule.

    This class represent an application alert rule in the DB.

    uid: Unique ID of the alert rule.
    rules: the rules in YAML format.
    template = boolean stating whether the rule file is \
               a template and must be rendered.

    """

    uid = models.CharField(max_length=200, unique=True)
    rules = YAMLField()
    template = models.BooleanField(
        "Whether this rules file is \
                                   a template and must be rendered",
        default=False,
    )

    class Meta:
        """Model Meta class overwritting."""

        abstract = True

    def __str__(self) -> str:
        """Str representation of an alert rule."""
        return self.uid


class PrometheusAlertRule(AlertRule):  # noqa: DJ08
    """
    This class represent a Prometheus Alert Rule in the DB.

    uid: Unique ID of the alert rule.
    rules: the rules in YAML format.
    template = boolean stating whether the rule file is \
               a template and must be rendered.
    """


class LokiAlertRule(AlertRule):  # noqa: DJ08
    """
    This class represent a Loki Alert Rule in the DB.

    uid: Unique ID of the alert rule.
    rules: the rules in YAML format.
    template = boolean stating whether the rule file is \
               a template and must be rendered.
    """
