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


class AlertRuleFile(models.Model):
    """Application alert rule file.

    This class represent an application alert rule file in the DB.

    uid: Unique ID of the alert rule file.
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


class PrometheusAlertRuleFile(AlertRuleFile):  # noqa: DJ08
    """
    This class represent a Prometheus alert rule file in the DB.

    uid: Unique ID of the alert rule file.
    rules: the rules in YAML format.
    template = boolean stating whether the rule file is \
               a template and must be rendered.
    """


class LokiAlertRuleFile(AlertRuleFile):  # noqa: DJ08
    """
    This class represent a Loki alert rule file in the DB.

    uid: Unique ID of the alert rule file.
    rules: the rules in YAML format.
    template = boolean stating whether the rule file is \
               a template and must be rendered.
    """
