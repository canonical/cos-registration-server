"""Device DB model."""

from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
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
    prometheus_alert_rule_files: Prometheus alert rules files relations.
    csr: Certificate Signing Request in PEM format.
    certificate: Signed certificate in PEM format (null until signed).
    certificate_status: Current status of the certificate request.
    certificate_detail: Additional details for denials or errors.
    certificate_created_at: Timestamp when certificate request was created.
    certificate_updated_at: Timestamp when certificate was last updated.
    """

    class CertificateStatus(models.TextChoices):
        """Certificate request status choices."""

        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        DENIED = "denied", "Denied"

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
    prometheus_alert_rule_files = models.ManyToManyField(
        PrometheusAlertRuleFile, related_name="devices"
    )
    loki_alert_rule_files = models.ManyToManyField(
        LokiAlertRuleFile, related_name="devices"
    )
    # TLS Certificate fields
    csr = models.TextField(
        "Certificate Signing Request", blank=True, default=""
    )
    certificate = models.TextField(
        "Signed Certificate", blank=True, default=""
    )
    certificate_status = models.CharField(
        max_length=20,
        choices=CertificateStatus.choices,
        blank=True,
        default="",
    )
    certificate_detail = models.TextField(
        "Certificate details", blank=True, default=""
    )
    certificate_created_at = models.DateTimeField(
        "Certificate request created", null=True, blank=True
    )
    certificate_updated_at = models.DateTimeField(
        "Certificate last updated", null=True, blank=True
    )

    def __str__(self) -> str:
        """Str representation of a device."""
        return self.uid
