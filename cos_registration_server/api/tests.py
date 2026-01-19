import json
from datetime import datetime, timedelta
from typing import Any, Dict, Set, Union
from unittest.mock import Mock, patch

import yaml
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
)
from devices.models import Certificate, CertificateStatus, Device
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase


class HealthViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:health")

    def test_health_ok(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class DevicesViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:devices")

        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

        self.public_ssh_key = "ssh-rsa AaBbCc/+=098765431"

    def create_device(self, **fields: Union[str, Set[str]]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_grafana_dashboard(
        self, uid: str, dashboard: Dict[str, Any]
    ) -> GrafanaDashboard:
        grafana_dashboard = GrafanaDashboard(uid=uid, dashboard=dashboard)
        grafana_dashboard.save()
        return grafana_dashboard

    def add_foxglove_dashboard(
        self, uid: str, dashboard: Dict[str, Any]
    ) -> FoxgloveDashboard:
        foxglove_dashboard = FoxgloveDashboard(uid=uid, dashboard=dashboard)
        foxglove_dashboard.save()
        return foxglove_dashboard

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_device(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        grafana_dashboard_uid = "dashboard-1"
        foxglove_dashboard_uid = "layout-1"
        self.add_grafana_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.add_foxglove_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.create_device(
            uid=uid,
            address=address,
            public_ssh_key=self.public_ssh_key,
            grafana_dashboards={grafana_dashboard_uid},
            foxglove_dashboards={foxglove_dashboard_uid},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        self.assertEqual(Device.objects.get().uid, uid)
        self.assertEqual(Device.objects.get().address, address)
        self.assertEqual(
            Device.objects.get().public_ssh_key, self.public_ssh_key
        )
        self.assertAlmostEqual(
            Device.objects.get().creation_date,
            timezone.now(),
            delta=timedelta(seconds=10),
        )
        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().uid,
            grafana_dashboard_uid,
        )
        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().dashboard,
            self.simple_grafana_dashboard,
        )
        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().uid,
            foxglove_dashboard_uid,
        )
        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().dashboard,
            self.simple_foxglove_dashboard,
        )

    def test_create_multiple_devices(self) -> None:
        devices = [
            {
                "uid": "robot-1",
                "address": "192.168.0.1",
                "public_ssh_key": "ssh-add ABC-1",
            },
            {
                "uid": "robot-2",
                "address": "192.168.0.2",
                "public_ssh_key": "ssh-add ABC-2",
            },
            {
                "uid": "robot-3",
                "address": "192.168.0.3",
                "public_ssh_key": "ssh-add ABC-3",
            },
        ]
        for device in devices:
            self.client.post(self.url, device, format="json")
        self.assertEqual(Device.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, device in enumerate(content_json):
            self.assertEqual(devices[i]["uid"], device["uid"])
            self.assertEqual(devices[i]["address"], device["address"])
            self.assertEqual(
                devices[i]["public_ssh_key"], device["public_ssh_key"]
            )
            self.assertIsNotNone(device.get("creation_date"))
            self.assertEqual(device.get("grafana_dashboards"), [])
            self.assertEqual(device.get("foxglove_dashboards"), [])

    def test_get_devices_with_filtered_fields(self) -> None:
        devices = [
            {
                "uid": "robot-1",
                "address": "192.168.0.1",
                "public_ssh_key": "ssh-add ABC-1",
            },
            {
                "uid": "robot-2",
                "address": "192.168.0.2",
                "public_ssh_key": "ssh-add ABC-2",
            },
            {
                "uid": "robot-3",
                "address": "192.168.0.3",
                "public_ssh_key": "ssh-add ABC-3",
            },
        ]
        for device in devices:
            self.client.post(self.url, device, format="json")
        self.assertEqual(Device.objects.count(), 3)

        params = {"fields": "creation_date,address"}
        response = self.client.get(self.url, data=params)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, device in enumerate(content_json):
            self.assertIsNone(device.get("uid"))
            self.assertEqual(devices[i]["address"], device["address"])
            self.assertIsNotNone(device.get("creation_date"))

    def test_create_already_present_uid(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(uid=uid, address=address)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Device.objects.count(), 1)
        # we try to create the same one
        response = self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.count(), 1)
        self.assertContains(
            response,
            '{"uid":["device with this uid already exists."]}',
            status_code=400,
        )

    def test_associate_device_with_non_existant_dashboards(
        self,
    ) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        response = self.create_device(
            uid=uid, address=address, grafana_dashboards={"dashboard-1"}
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards":["Object with uid=dashboard-1 does not exist."]}',
            status_code=400,
        )

        response = self.create_device(
            uid=uid, address=address, foxglove_dashboards={"dashboard-1"}
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_dashboards":["Object with uid=dashboard-1 does not exist."]}',
            status_code=400,
        )

    def test_dashboards_not_in_a_list(self) -> None:
        uid = "robot-1"
        address = "192.168.0.1"
        # we try to create the same one
        response = self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards="dashboard-1",
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"grafana_dashboards":["Expected a list of items but got type \\"str\\".',
            status_code=400,
        )

        response = self.create_device(
            uid=uid,
            address=address,
            foxglove_dashboards="dashboard-1",
        )
        self.assertEqual(Device.objects.count(), 0)
        self.assertContains(
            response,
            '{"foxglove_dashboards":["Expected a list of items but got type \\"str\\".',
            status_code=400,
        )


class DeviceViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_grafana_dashboard_json = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }
        self.simple_foxglove_dashboard_json = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }
        self.simple_prometheus_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: MyRobotTest_{{ $label.instace }}"""
        self.simple_loki_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: HighLogRatePerInstance"""
        self.grafana_dashboard = GrafanaDashboard(
            uid="dashboard-1", dashboard=self.simple_grafana_dashboard_json
        )
        self.grafana_dashboard.save()
        self.foxglove_dashboard = FoxgloveDashboard(
            uid="dashboard-1", dashboard=self.simple_foxglove_dashboard_json
        )
        self.foxglove_dashboard.save()

        self.loki_alert_rule_file = LokiAlertRuleFile(
            uid="alert-rule-1", rules=self.simple_loki_alert_rule
        )

        self.loki_alert_rule_file.save()

        self.prometheus_alert_rule_file = PrometheusAlertRuleFile(
            uid="alert-rule-1", rules=self.simple_prometheus_alert_rule
        )

        self.prometheus_alert_rule_file.save()

        self.public_ssh_key = "ssh-rsa AaBbCc/+=098765431"

    def url(self, uid: str) -> str:
        return reverse("api:device", args=(uid,))

    def create_device(self, **fields: Union[str, Set[str]]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:devices")
        return self.client.post(url, data, format="json")

    def test_get_nonexistent_device(self) -> None:
        response = self.client.get(self.url("future-robot"))
        self.assertEqual(response.status_code, 404)

    def test_get_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            public_ssh_key=self.public_ssh_key,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
        self.assertEqual(content_json["public_ssh_key"], self.public_ssh_key)
        self.assertAlmostEqual(
            datetime.fromisoformat(
                content_json["creation_date"].replace("Z", "+00:00")
            ),
            timezone.now(),
            delta=timedelta(seconds=10),
        )
        self.assertEqual(
            content_json["grafana_dashboards"], [self.grafana_dashboard.uid]
        )

        self.assertEqual(
            content_json["foxglove_dashboards"], [self.foxglove_dashboard.uid]
        )

    def test_patch_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        response = self.create_device(uid=uid, address=address)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["public_ssh_key"], "")
        address = "192.168.1.200"
        data = {"address": address, "public_ssh_key": self.public_ssh_key}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], uid)
        self.assertEqual(content_json["address"], address)
        self.assertEqual(content_json["public_ssh_key"], self.public_ssh_key)

    def test_patch_grafana_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 0)
        data = {"grafana_dashboards": [self.grafana_dashboard.uid]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["grafana_dashboards"][0],
            self.grafana_dashboard.uid,
        )

        self.assertEqual(
            Device.objects.get().grafana_dashboards.get().uid,
            self.grafana_dashboard.uid,
        )

    def test_patch_foxglove_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 0)
        data = {"foxglove_dashboards": [self.foxglove_dashboard.uid]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["foxglove_dashboards"][0],
            self.foxglove_dashboard.uid,
        )

        self.assertEqual(
            Device.objects.get().foxglove_dashboards.get().uid,
            self.foxglove_dashboard.uid,
        )

    def test_partial_patch_with_existing_dashboards(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 1)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 1)
        data = {"address": "192.168.1.3"}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["address"],
            data["address"],
        )
        self.assertEqual(Device.objects.get().grafana_dashboards.count(), 1)
        self.assertEqual(Device.objects.get().foxglove_dashboards.count(), 1)

    def test_patch_prometheus_alert_rule_files(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(
            Device.objects.get().prometheus_alert_rule_files.count(), 0
        )
        data = {
            "prometheus_alert_rule_files": [
                self.prometheus_alert_rule_file.uid
            ]
        }
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["prometheus_alert_rule_files"][0],
            self.prometheus_alert_rule_file.uid,
        )

        self.assertEqual(
            Device.objects.get().prometheus_alert_rule_files.get().uid,
            self.prometheus_alert_rule_file.uid,
        )

    def test_patch_loki_alert_rule_files(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        self.assertEqual(Device.objects.get().loki_alert_rule_files.count(), 0)
        data = {"loki_alert_rule_files": [self.loki_alert_rule_file.uid]}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["loki_alert_rule_files"][0],
            self.loki_alert_rule_file.uid,
        )

        self.assertEqual(
            Device.objects.get().loki_alert_rule_files.get().uid,
            self.loki_alert_rule_file.uid,
        )

    def test_partial_patch_with_existing_alert_rule_files(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            prometheus_alert_rule_files={self.prometheus_alert_rule_file.uid},
            loki_alert_rule_files={self.loki_alert_rule_file.uid},
        )
        self.assertEqual(
            Device.objects.get().prometheus_alert_rule_files.count(), 1
        )
        self.assertEqual(Device.objects.get().loki_alert_rule_files.count(), 1)
        data = {"address": "192.168.1.3"}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json["address"],
            data["address"],
        )
        self.assertEqual(
            Device.objects.get().prometheus_alert_rule_files.count(), 1
        )
        self.assertEqual(Device.objects.get().loki_alert_rule_files.count(), 1)

    def test_invalid_patch_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(uid=uid, address=address)
        address = "192.168.1"  # invalid IP
        data = {"address": address}
        response = self.client.patch(self.url(uid), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_delete_device(self) -> None:
        uid = "robot-1"
        address = "192.168.1.2"
        self.create_device(
            uid=uid,
            address=address,
            grafana_dashboards={self.grafana_dashboard.uid},
            foxglove_dashboards={self.foxglove_dashboard.uid},
        )
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(uid))
        self.assertEqual(response.status_code, 404)


class DeviceCertificateViewTests(APITestCase):
    def setUp(self) -> None:
        self.device_uid = "robot-123"
        self.device_address = "192.168.0.10"
        self.url = reverse(
            "api:device_certificate", kwargs={"uid": self.device_uid}
        )
        self.valid_csr = """-----BEGIN CERTIFICATE REQUEST-----
MIICujCCAaICAQAwdTELMAkGA1UEBhMCVVMxDTALBgNVBAgMBFRlc3QxDTALBgNV
BAcMBFRlc3QxDTALBgNVBAoMBFRlc3QxDTALBgNVBAsMBFRlc3QxDDAKBgNVBAMM
A2ZvbzEcMBoGCSqGSIb3DQEJARYNdGVzdEB0ZXN0LmNvbTCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBALG0zb43MgTji5sEGsiWXY8cFmcfsbVyL+H/7+VU
+UT5IW4EAVMr43WPGtJT9ts4lmN1AiI9Y3EJJA2v+/ySqdi4VfaWbES9CZuv0iE2
n514kjErGpFNA0jwLTdyodOfixZZLY47tOq+lWr5rIpTR7XnW9//TCI5gZIC3TzB
1Dn1SmkYfzqH/7X2W/ojzCOltjBjW8dM7IzwJ1gez2wcWlBcu8v4OXKRFbJ8nBao
EsGSL06d6ARkJJ1PqZ+JUEfserXz8EOZPTcDAkHVuCAcu21u5dnp1bpL0WJKC9+N
6E9b6L0BqQn3GF24Z6HkF8N8qbcbA69iwLhutNLSRRVQyIECAwEAAaAAMA0GCSqG
SIb3DQEBCwUAA4IBAQB7RytS3IYkYAMLnYWP+A5blWFCzUkZykObxcXChzzwpekx
4PWG9zlFmLRBZraaolv2I/++Cknv8pl7tvE3qnDLU4+MqY6weoEXyEhbi7MXchie
AH+LoyVjvEHHAo46grYvF+qocIn4Ct++bmkY288HgIECZAsfB8hS3OVt4ylnoYr0
ItwafNnlamyeBjdNNWIgpHfCw/97z0R6kmUlCMKWGf71VdLpq4gqZZuoZUedHmRY
Ufqdch7rwup73OcYtwj/pyenBeMY6hUDPGE+LXs75HQRsX60dzRpRNYDBl/K3KDG
uv/5wRkaVmEeKdM+i2l2/Hro9IMuKiLh+cOX1m/f
-----END CERTIFICATE REQUEST-----"""

    def create_device(self, **fields: Union[str, Set[str]]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:devices")
        return self.client.post(url, data, format="json")

    # POST endpoint tests
    def test_post_csr_success(self) -> None:
        """Test successful CSR submission."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        response = self.client.post(
            self.url, {"csr": self.valid_csr}, format="json"
        )

        self.assertEqual(response.status_code, 202)

        # Verify certificate was created with CSR
        device = Device.objects.get(uid=self.device_uid)
        self.assertTrue(hasattr(device, "certificate"))
        certificate = device.certificate
        self.assertEqual(certificate.csr, self.valid_csr)
        self.assertEqual(certificate.status, CertificateStatus.PENDING)
        self.assertIsNotNone(certificate.created_at)
        self.assertIsNotNone(certificate.updated_at)
        self.assertEqual(certificate.certificate, "")

    def test_post_csr_device_not_found(self) -> None:
        """Test CSR submission for non-existent device."""
        response = self.client.post(
            self.url, {"csr": self.valid_csr}, format="json"
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Device not found")

    def test_post_csr_invalid_format_missing_header(self) -> None:
        """Test CSR submission with missing BEGIN header."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        invalid_csr = """MIICvDCCAaQCAQAwdzELMAkGA1UEBhMCVVMxDTALBgNVBAgMBFRlc3Q=
-----END CERTIFICATE REQUEST-----"""

        response = self.client.post(
            self.url, {"csr": invalid_csr}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid CSR format")

    def test_post_csr_invalid_format_missing_footer(self) -> None:
        """Test CSR submission with missing END footer."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        invalid_csr = """-----BEGIN CERTIFICATE REQUEST-----
MIICvDCCAaQCAQAwdzELMAkGA1UEBhMCVVMxDTALBgNVBAgMBFRlc3Q="""

        response = self.client.post(
            self.url, {"csr": invalid_csr}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid CSR format")

    def test_post_csr_empty(self) -> None:
        """Test CSR submission with empty CSR."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        response = self.client.post(self.url, {"csr": ""}, format="json")

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid CSR format")

    def test_post_csr_overwrite_existing(self) -> None:
        """Test CSR submission overwrites existing CSR."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        # Submit first CSR
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        # Submit new CSR
        new_csr = self.valid_csr.replace("robot-123", "robot-456")
        response = self.client.post(self.url, {"csr": new_csr}, format="json")

        self.assertEqual(response.status_code, 202)
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        self.assertEqual(certificate.csr, new_csr)
        self.assertEqual(certificate.status, CertificateStatus.PENDING)
        # Certificate should be cleared
        self.assertEqual(certificate.certificate, "")

    # GET endpoint tests
    def test_get_certificate_status_pending(self) -> None:
        """Test GET when certificate is pending."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["csr"], self.valid_csr)
        self.assertEqual(data["certificate"], "")
        self.assertNotIn("detail", data)

    def test_get_certificate_status_signed(self) -> None:
        """Test GET when certificate is signed."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        # Simulate charm updating certificate
        signed_cert = (
            "-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----"
        )
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        certificate.status = CertificateStatus.SIGNED
        certificate.certificate = signed_cert
        certificate.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "signed")
        self.assertEqual(data["certificate"], signed_cert)
        self.assertEqual(data["csr"], self.valid_csr)

    def test_get_certificate_status_denied(self) -> None:
        """Test GET when certificate is denied."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        # Simulate charm denying certificate
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        certificate.status = CertificateStatus.DENIED
        certificate.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "denied")
        self.assertEqual(data["certificate"], "")

    def test_get_certificate_device_not_found(self) -> None:
        """Test GET for non-existent device."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Device or CSR not found")

    def test_get_certificate_no_csr(self) -> None:
        """Test GET when device exists but no CSR submitted."""
        self.create_device(uid=self.device_uid, address=self.device_address)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Device or CSR not found")

    # PATCH endpoint tests
    def test_patch_certificate_sign_success(self) -> None:
        """Test PATCH to mark certificate as signed."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        signed_cert = (
            "-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----"
        )
        response = self.client.patch(
            self.url,
            {
                "status": "signed",
                "certificate": signed_cert,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "signed")
        self.assertEqual(data["certificate"], signed_cert)
        self.assertEqual(data["uid"], self.device_uid)
        self.assertIsNotNone(data["updated_at"])

        # Verify certificate was updated
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        self.assertEqual(certificate.status, CertificateStatus.SIGNED)
        self.assertEqual(certificate.certificate, signed_cert)

    def test_patch_certificate_deny(self) -> None:
        """Test PATCH to mark certificate as denied."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        response = self.client.patch(
            self.url,
            {
                "status": "denied",
                "detail": "Invalid CSR",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "denied")

        # Verify certificate was updated
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        self.assertEqual(certificate.status, CertificateStatus.DENIED)

    def test_patch_certificate_device_not_found(self) -> None:
        """Test PATCH for non-existent device."""
        response = self.client.patch(
            self.url,
            {"status": "signed"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Device uid not found")

    def test_patch_certificate_invalid_status(self) -> None:
        """Test PATCH with invalid status value."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        response = self.client.patch(
            self.url,
            {"status": "invalid_status"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["error"], "Invalid status value")

    def test_patch_certificate_partial_update(self) -> None:
        """Test PATCH with only certificate (no status)."""
        self.create_device(uid=self.device_uid, address=self.device_address)
        self.client.post(self.url, {"csr": self.valid_csr}, format="json")

        signed_cert = (
            "-----BEGIN CERTIFICATE-----\nMIID...\n-----END CERTIFICATE-----"
        )
        response = self.client.patch(
            self.url,
            {"certificate": signed_cert},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        # Status should remain pending since we didn't update it
        device = Device.objects.get(uid=self.device_uid)
        certificate = device.certificate
        self.assertEqual(certificate.status, CertificateStatus.PENDING)
        self.assertEqual(certificate.certificate, signed_cert)


class GrafanaDashboardsViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:grafana_dashboards")

        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_dashboard(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        self.assertEqual(
            GrafanaDashboard.objects.get().uid, grafana_dashboard_uid
        )
        self.assertEqual(
            GrafanaDashboard.objects.get().dashboard,
            self.simple_grafana_dashboard,
        )

    def test_create_multiple_dashboards(self) -> None:
        dashboards = [
            {"uid": "d-1", "dashboard": '{"test1": "value"}'},
            {"uid": "d-2", "dashboard": '{"test2": "value"}'},
            {"uid": "d-3", "dashboard": '{"test3": "value"}'},
        ]
        for dashboard in dashboards:
            self.create_dashboard(
                uid=dashboard["uid"], dashboard=dashboard["dashboard"]
            )

        self.assertEqual(GrafanaDashboard.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, dashboard in enumerate(content_json):
            self.assertEqual(dashboards[i]["uid"], dashboard["uid"])
            self.assertEqual(
                json.loads(dashboards[i]["dashboard"]), dashboard["dashboard"]
            )

    def test_create_already_present_uid(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        # we try to create the same one
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.assertEqual(GrafanaDashboard.objects.count(), 1)
        self.assertContains(
            response,
            '{"uid":["grafana dashboard with this uid already exists."]}',
            status_code=400,
        )

    def test_create_dashboard_with_illformed_json(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        response = self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard='{"hello": {"test"sdsa"}}'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GrafanaDashboard.objects.count(), 0)
        self.assertContains(
            response,
            '{"dashboard":["Failed to load dashboard as json."]}',
            status_code=400,
        )

    def test_get_dashboards_associated_with_device(self) -> None:
        grafana_dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=grafana_dashboard_uid, dashboard=self.simple_grafana_dashboard
        )
        self.add_device(uid="robot-1").grafana_dashboards.add(
            GrafanaDashboard.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json,
            [
                {
                    "uid": grafana_dashboard_uid,
                    "dashboard": self.simple_grafana_dashboard,
                }
            ],
        )


class GrafanaDashboardViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_grafana_dashboard = {
            "id": None,
            "uid": None,
            "title": "Production Overview",
            "tags": ["templated"],
            "timezone": "browser",
            "schemaVersion": 16,
            "refresh": "25s",
        }

    def url(self, uid: str) -> str:
        return reverse("api:grafana_dashboard", args=(uid,))

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:grafana_dashboards")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_dashboard(self) -> None:
        response = self.client.get(self.url("future-dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_get_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json, self.simple_grafana_dashboard)

    def test_patch_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        data = {"dashboard": '{"test": "dash"}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], json.loads(data["dashboard"])
        )

    def test_invalid_patch_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        data = {"dashboard": '{"test": "das}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_dashboard(self) -> None:
        dashboard_uid = "dashboard-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_grafana_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 404)


class FoxgloveDashboardsViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:foxglove_dashboards")

        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_dashboard(self) -> None:
        foxglove_dashboard_uid = "layout-1"
        response = self.create_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FoxgloveDashboard.objects.count(), 1)
        self.assertEqual(
            FoxgloveDashboard.objects.get().uid, foxglove_dashboard_uid
        )
        self.assertEqual(
            FoxgloveDashboard.objects.get().dashboard,
            self.simple_foxglove_dashboard,
        )

    def test_create_multiple_dashboards(self) -> None:
        dashboards = [
            {"uid": "l-1", "dashboard": '{"test1": "value"}'},
            {"uid": "l-2", "dashboard": '{"test2": "value"}'},
            {"uid": "l-3", "dashboard": '{"test3": "value"}'},
        ]
        for dashboard in dashboards:
            self.create_dashboard(
                uid=dashboard["uid"], dashboard=dashboard["dashboard"]
            )

        self.assertEqual(FoxgloveDashboard.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, dashboard in enumerate(content_json):
            self.assertEqual(dashboards[i]["uid"], dashboard["uid"])
            self.assertEqual(
                json.loads(dashboards[i]["dashboard"]), dashboard["dashboard"]
            )

    def test_get_dashboards_associated_with_device(self) -> None:
        foxglove_dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=foxglove_dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        self.add_device(uid="robot-1").foxglove_dashboards.add(
            FoxgloveDashboard.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(
            content_json,
            [
                {
                    "uid": foxglove_dashboard_uid,
                    "dashboard": self.simple_foxglove_dashboard,
                }
            ],
        )


class FoxgloveDashboardViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_foxglove_dashboard = {
            "configById": {},
            "globalVariables": {},
            "userNodes": {},
            "playbackConfig": {"speed": 1},
        }

    def url(self, uid: str) -> str:
        return reverse("api:foxglove_dashboard", args=(uid,))

    def create_dashboard(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:foxglove_dashboards")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_dashboard(self) -> None:
        response = self.client.get(self.url("future-dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_get_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json, self.simple_foxglove_dashboard)

    def test_patch_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        data = {"dashboard": '{"test": "dash"}'}
        response = self.client.patch(
            self.url(dashboard_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], dashboard_uid)
        self.assertEqual(
            content_json["dashboard"], json.loads(data["dashboard"])
        )

    def test_delete_dashboard(self) -> None:
        dashboard_uid = "layout-1"
        self.create_dashboard(
            uid=dashboard_uid,
            dashboard=self.simple_foxglove_dashboard,
        )
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(dashboard_uid))
        self.assertEqual(response.status_code, 404)


class PrometheusAlertRuleFilesViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:prometheus_alert_rule_files")

        self.simple_prometheus_alert_rule_template = """groups:
  name: cos-robotics-model_robot_test_%%juju_device_uuid%%
  rules:
  - alert: MyRobotTest_{{ $label.instace }}
    expr: (node_memory_MemFree_bytes{device_instance="%%juju_device_uuid%%"})/1e9
       < 30"""

        self.simple_prometheus_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: MyRobotTest_{{ $label.instace }}
    expr: (node_memory_MemFree_bytes{device_instance="robot1"})/1e9
       < 30"""

    def create_alert_rule(self, **fields: Union[str, str]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_alert_rule_template(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(PrometheusAlertRuleFile.objects.count(), 1)
        self.assertEqual(
            PrometheusAlertRuleFile.objects.get().uid,
            prometheus_alert_rule_uid,
        )
        self.assertEqual(
            PrometheusAlertRuleFile.objects.get().rules,
            yaml.safe_load(self.simple_prometheus_alert_rule_template),
        )
        self.assertEqual(PrometheusAlertRuleFile.objects.get().template, True)

    def test_create_alert_rule(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PrometheusAlertRuleFile.objects.count(), 1)
        self.assertEqual(
            PrometheusAlertRuleFile.objects.get().uid,
            prometheus_alert_rule_uid,
        )
        self.assertEqual(
            PrometheusAlertRuleFile.objects.get().rules,
            yaml.safe_load(self.simple_prometheus_alert_rule),
        )
        self.assertEqual(PrometheusAlertRuleFile.objects.get().template, False)

    def test_create_multiple_alert_rules(self) -> None:
        alert_rules = [
            {"uid": "ar-1", "rules": "name: test1"},
            {"uid": "ar-2", "rules": "name: test2"},
            {"uid": "ar-3", "rules": "name: test3"},
        ]
        for alert_rule in alert_rules:
            self.create_alert_rule(
                uid=alert_rule["uid"], rules=alert_rule["rules"]
            )

        self.assertEqual(PrometheusAlertRuleFile.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, alert_rule in enumerate(content_json):
            self.assertEqual(alert_rules[i]["uid"], alert_rule["uid"])
            self.assertEqual(alert_rules[i]["rules"], alert_rule["rules"])

    def test_get_alert_rule_associated_with_device(self) -> None:
        prometheus_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=prometheus_alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        self.add_device(uid="robot1").prometheus_alert_rule_files.add(
            PrometheusAlertRuleFile.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.simple_prometheus_alert_rule_rendered = """groups:
  name: cos-robotics-model_robot_test_robot1
  rules:
  - alert: MyRobotTest_{{ $label.instace }}
    expr: (node_memory_MemFree_bytes{device_instance="robot1"})/1e9
      < 30"""
        self.assertEqual(
            content_json[0]["rules"],
            self.simple_prometheus_alert_rule_rendered,
        )


class PrometheusAlertRuleFileViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_prometheus_alert_rule_template = """groups:
  name: cos-robotics-model_robot_test_%%juju_device_uuid%%
  rules:
  - alert: MyRobotTest_{{ $label.instance }}
    expr: (node_memory_MemFree_bytes{device_instance="%%juju_device_uuid%%"})/1e9
      < 30"""

        self.simple_prometheus_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: MyRobotTest_{{ $label.instance }}
    expr: (node_memory_MemFree_bytes{device_instance="robot1"})/1e9 < 30"""

    def url(self, uid: str) -> str:
        return reverse("api:prometheus_alert_rule_file", args=(uid,))

    def create_alert_rule(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:prometheus_alert_rule_files")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_alert_rule(self) -> None:
        response = self.client.get(self.url("future-alert-rule"))
        self.assertEqual(response.status_code, 404)

    def test_get_alert_rule_template(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(
            content_json["rules"], self.simple_prometheus_alert_rule_template
        )
        self.assertEqual(content_json["template"], True)

    def test_get_alert_rule_no_template(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)

        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(
            content_json["rules"], self.simple_prometheus_alert_rule
        )
        self.assertEqual(content_json["template"], False)

    def test_patch_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )

        data = {"rules": "name: test"}

        response = self.client.patch(
            self.url(alert_rule_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(content_json["rules"], data["rules"])

    def test_delete_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_prometheus_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 404)


class LokiAlertRuleFilesViewTests(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("api:loki_alert_rule_files")

        self.simple_loki_alert_rule_template = """groups:
  name: cos-robotics-model_robot_test_%%juju_device_uuid%%
  rules:
  - alert: HighLogRatePerInstance
    expr: rate({job="loki.source.journal.read", instance="%%juju_device_uuid%%"}[5m]) > 100"""

        self.simple_loki_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: HighLogRatePerInstance
    expr: rate({job="loki.source.journal.read", instance="robot-1"}[5m]) > 100"""

    def create_alert_rule(self, **fields: Union[str, str]) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        return self.client.post(self.url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nothing(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)

    def test_create_alert_rule_template(self) -> None:
        loki_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=loki_alert_rule_uid,
            rules=self.simple_loki_alert_rule_template,
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(LokiAlertRuleFile.objects.count(), 1)
        self.assertEqual(
            LokiAlertRuleFile.objects.get().uid,
            loki_alert_rule_uid,
        )
        self.assertEqual(
            LokiAlertRuleFile.objects.get().rules,
            yaml.safe_load(self.simple_loki_alert_rule_template),
        )
        self.assertEqual(LokiAlertRuleFile.objects.get().template, True)

    def test_create_alert_rule(self) -> None:
        loki_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=loki_alert_rule_uid,
            rules=self.simple_loki_alert_rule,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LokiAlertRuleFile.objects.count(), 1)
        self.assertEqual(
            LokiAlertRuleFile.objects.get().uid,
            loki_alert_rule_uid,
        )
        self.assertEqual(
            LokiAlertRuleFile.objects.get().rules,
            yaml.safe_load(self.simple_loki_alert_rule),
        )
        self.assertEqual(LokiAlertRuleFile.objects.get().template, False)

    def test_create_multiple_alert_rules(self) -> None:
        alert_rules = [
            {"uid": "ar-1", "rules": "name: test1"},
            {"uid": "ar-2", "rules": "name: test2"},
            {"uid": "ar-3", "rules": "name: test3"},
        ]
        for alert_rule in alert_rules:
            self.create_alert_rule(
                uid=alert_rule["uid"], rules=alert_rule["rules"]
            )

        self.assertEqual(LokiAlertRuleFile.objects.count(), 3)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(len(content_json), 3)
        for i, alert_rule in enumerate(content_json):
            self.assertEqual(alert_rules[i]["uid"], alert_rule["uid"])
            self.assertEqual(alert_rules[i]["rules"], alert_rule["rules"])

    def test_get_alert_rule_associated_with_device(self) -> None:
        loki_alert_rule_uid = "first_rule"
        response = self.create_alert_rule(
            uid=loki_alert_rule_uid,
            rules=self.simple_loki_alert_rule_template,
        )
        self.add_device(uid="robot1").loki_alert_rule_files.add(
            LokiAlertRuleFile.objects.get()
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.simple_loki_alert_rule_rendered = """groups:
  name: cos-robotics-model_robot_test_robot1
  rules:
  - alert: HighLogRatePerInstance
    expr: rate({job="loki.source.journal.read", instance="robot1"}[5m])
      > 100"""
        self.assertEqual(
            content_json[0]["rules"],
            self.simple_loki_alert_rule_rendered,
        )


class LokiAlertRuleFileViewTests(APITestCase):
    def setUp(self) -> None:
        self.simple_loki_alert_rule_template = """groups:
  name: cos-robotics-model_robot_test_%%juju_device_uuid%%
  rules:
  - alert: HighLogRatePerInstance
    expr: rate({job="loki.source.journal.read", instance="%%juju_device_uuid%%"}[5m])
      > 100"""

        self.simple_loki_alert_rule = """groups:
  name: cos-robotics-model_robot_NO_TEMPLATE
  rules:
  - alert: HighLogRatePerInstance
    expr: rate({job="loki.source.journal.read", instance="robot1"}[5m]) > 100"""

    def url(self, uid: str) -> str:
        return reverse("api:loki_alert_rule_file", args=(uid,))

    def create_alert_rule(
        self, **fields: Union[str, Dict[str, Any]]
    ) -> HttpResponse:
        data = {}
        for field, value in fields.items():
            data[field] = value
        url = reverse("api:loki_alert_rule_files")
        return self.client.post(url, data, format="json")

    def add_device(self, uid: str) -> Device:
        device = Device(uid=uid, address="127.0.0.1")
        device.save()
        return device

    def test_get_nonexistent_alert_rule(self) -> None:
        response = self.client.get(self.url("future-alert-rule"))
        self.assertEqual(response.status_code, 404)

    def test_get_alert_rule_template(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_loki_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)

        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(
            content_json["rules"], self.simple_loki_alert_rule_template
        )
        self.assertEqual(content_json["template"], True)

    def test_get_alert_rule_no_template(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_loki_alert_rule,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)

        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(content_json["rules"], self.simple_loki_alert_rule)
        self.assertEqual(content_json["template"], False)

    def test_patch_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_loki_alert_rule_template,
        )

        data = {"rules": "name: test"}

        response = self.client.patch(
            self.url(alert_rule_uid), data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        content_json = json.loads(response.content)
        self.assertEqual(content_json["uid"], alert_rule_uid)
        self.assertEqual(content_json["rules"], data["rules"])

    def test_delete_alert_rule(self) -> None:
        alert_rule_uid = "alert-rule-1"
        self.create_alert_rule(
            uid=alert_rule_uid,
            rules=self.simple_loki_alert_rule_template,
        )
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 204)
        response = self.client.get(self.url(alert_rule_uid))
        self.assertEqual(response.status_code, 404)
