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
    prometheus_alert_rule_files = models.ManyToManyField(
        PrometheusAlertRuleFile, related_name="devices"
    )
    loki_alert_rule_files = models.ManyToManyField(
        LokiAlertRuleFile, related_name="devices"
    )

    def __str__(self) -> str:
        """Str representation of a device."""
        return self.uid


class DeviceCertificate(models.Model):
    """Device Certificate model.

    This class represents a device certificate in the DB.

    device: OneToOne relationship to Device.
    csr: Certificate Signing Request in PEM format.
    certificate: Signed certificate in PEM format (null until signed).
    ca: CA that signed the certificate.
    chain: Certificate chain in PEM format.
    status: Current status of the certificate request.
    created_at: Timestamp when certificate request was created.
    updated_at: Timestamp when certificate was last updated.
    """

    class CertificateStatus(models.TextChoices):
        """Certificate request status choices."""

        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        DENIED = "denied", "Denied"

    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name="certificate",
        primary_key=True,
    )
    csr = models.TextField("Device Certificate Signing Request")
    certificate = models.TextField(
        "Signed Device Certificate", blank=True, default=""
    )
    ca = models.TextField(
        "Device Certificate Authority", blank=True, default=""
    )
    chain = models.TextField(
        "Device Certificate Chain", blank=True, default=""
    )
    status = models.CharField(
        max_length=20,
        choices=CertificateStatus.choices,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(
        "Device Certificate request created", auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Device Certificate last updated", auto_now=True
    )

    def __str__(self) -> str:
        """Str representation of a certificate."""
        return f"Device Certificate for {self.device.uid}"
