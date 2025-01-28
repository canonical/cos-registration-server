"""API views."""

import json

import yaml
from api.serializer import (
    DeviceSerializer,
    FoxgloveDashboardSerializer,
    GrafanaDashboardSerializer,
    PrometheusAlertRuleSerializer,
)
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    PrometheusAlertRule,
)
from devices.models import Device
from django.http import HttpResponse
from jinja2 import Environment
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Health API view."""

    def get(self, request: Request) -> Response:
        """Health get view.

        request: Http GET request.
        return: Http JSON response.
        """
        return Response()


class DevicesView(APIView):
    """Devices API view."""

    def get(self, request: Request) -> Response:
        """Devices get view.

        request: Http GET request.
        return: Http JSON response.
        """
        devices = Device.objects.all()
        serialized = DeviceSerializer(
            devices, many=True, context={"request": request}
        )
        return Response(serialized.data)

    def post(self, request: Request) -> Response:
        """Devices post view.

        request: Http GET request.
        return: Http JSON response.
        """
        serialized = DeviceSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data, status=201)
        return Response(serialized.errors, status=400)


class DeviceView(APIView):
    """Device API view."""

    def _get_device(self, uid: str) -> Device:
        try:
            device = Device.objects.get(uid=uid)
            return device
        except Device.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> Response:
        """Device get view.

        request: Http GET request.
        uid: Device UID passed in the URL.
        return: Http JSON response.
        """
        device = self._get_device(uid)
        serialized = DeviceSerializer(device, context={"request": request})
        return Response(serialized.data)

    def patch(self, request: Request, uid: str) -> Response:
        """Device patch view.

        request: Http PATCH request.
        uid: Device UID passed in the URL.
        return: Http JSON response.
        """
        device = self._get_device(uid)
        serialized = DeviceSerializer(device, data=request.data, partial=True)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data)
        return Response(serialized.errors, status=400)

    def delete(self, request: Request, uid: str) -> Response:
        """Device delete view.

        request: Http DELETE request.
        uid: Device UID passed in the URL.
        return: Http response.
        """
        device = self._get_device(uid)
        device.delete()
        return Response(status=204)


class GrafanaDashboardsView(APIView):
    """GrafanaDashboards API view."""

    def get(self, request: Request) -> Response:
        """Grafana dashboards get view.

        request: Http GET request.
        return: Http JSON response.
        """
        dashboards = GrafanaDashboard.objects.all()
        serialized = GrafanaDashboardSerializer(dashboards, many=True)
        return Response(serialized.data)

    def post(self, request: Request) -> Response:
        """Grafana dashboards post view.

        request: Http POST request.
        return: Http JSON response.
        """
        serialized = GrafanaDashboardSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data, status=201)
        return Response(serialized.errors, status=400)


class GrafanaDashboardView(APIView):
    """GrafanaDashboard API view."""

    def _get_dashboard(self, uid: str) -> GrafanaDashboard:
        try:
            dashboard = GrafanaDashboard.objects.get(uid=uid)
            return dashboard
        except GrafanaDashboard.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> HttpResponse:
        """Grafana dashboard get view.

        request: Http GET request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        serialized = GrafanaDashboardSerializer(dashboard)
        response = HttpResponse(
            json.dumps(serialized.data["dashboard"]),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{serialized.data["uid"]}.json"'
        )
        return response

    def patch(self, request: Request, uid: str) -> Response:
        """Grafana dashboard patch view.

        request: Http PATCH request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        serialized = GrafanaDashboardSerializer(
            dashboard, data=request.data, partial=True
        )
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data)
        return Response(serialized.errors, status=400)

    def delete(self, request: Request, uid: str) -> Response:
        """Grafana dashboard delete view.

        request: Http DELETE request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        dashboard.delete()
        return Response(status=204)


class FoxgloveDashboardsView(APIView):
    """FoxgloveDashboards API view."""

    def get(self, request: Request) -> Response:
        """Foxglove dashboards get view.

        request: Http GET request.
        return: Http JSON response.
        """
        dashboards = FoxgloveDashboard.objects.all()
        serialized = FoxgloveDashboardSerializer(dashboards, many=True)
        return Response(serialized.data)

    def post(self, request: Request) -> Response:
        """Foxglove dashboards post view.

        request: Http POST request.
        return: Http JSON response.
        """
        serialized = FoxgloveDashboardSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data, status=201)
        return Response(serialized.errors, status=400)


class FoxgloveDashboardView(APIView):
    """FoxgloveDashboard API view."""

    def _get_dashboard(self, uid: str) -> FoxgloveDashboard:
        try:
            dashboard = FoxgloveDashboard.objects.get(uid=uid)
            return dashboard
        except FoxgloveDashboard.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> HttpResponse:
        """Foxglove dashboard get view.

        request: Http GET request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        serialized = FoxgloveDashboardSerializer(dashboard)
        response = HttpResponse(
            json.dumps(serialized.data["dashboard"]),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{serialized.data["uid"]}.json"'
        )
        return response

    def patch(self, request: Request, uid: str) -> Response:
        """Foxglove dashboard patch view.

        request: Http PATCH request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        serialized = FoxgloveDashboardSerializer(
            dashboard, data=request.data, partial=True
        )
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data)
        return Response(serialized.errors, status=400)

    def delete(self, request: Request, uid: str) -> Response:
        """Foxglove dashboard delete view.

        request: Http DELETE request.
        return: Http JSON response.
        """
        dashboard = self._get_dashboard(uid)
        dashboard.delete()
        return Response(status=204)


class PrometheusAlertRulesView(APIView):
    """PrometheusAlertRules API view."""

    def get(self, request: Request) -> Response:
        """Prometheus Alert Rules get view.

        request: Http GET request.
        return: Http JSON response.
        """
        alert_rules = PrometheusAlertRule.objects.all()
        rendered_rules = []

        template_alert_rules = PrometheusAlertRule.objects.filter(
            template=True
        )
        devices = Device.objects.all()

        for device in devices:
            for rule in device.prometheus_alert_rules.all():
                if rule in template_alert_rules:
                    env = Environment(
                        variable_start_string="%%",
                        variable_end_string="%%",
                    )
                    rule_string = yaml.dump(rule.rules)
                    template = env.from_string(rule_string)
                    context = {"juju_device_uuid": f"{device.uid}"}
                    rendered_rule = template.render(context)
                    rendered_rules.append(
                        {
                            "uid": rule.uid + "_" + device.uid,
                            "rules": rendered_rule,
                        }
                    )
        serialized = PrometheusAlertRuleSerializer(alert_rules, many=True)
        serialized_list = list(serialized.data)
        serialized_list.extend(rendered_rules)
        return Response(serialized_list)

    def post(self, request: Request) -> Response:
        """Prometheus Alert Rules post view.

        request: Http POST request.
        return: Http JSON response.
        """
        serialized = PrometheusAlertRuleSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data, status=201)
        return Response(serialized.errors, status=400)


class PrometheusAlertRuleView(APIView):
    """PrometheusAlertRule API view."""

    def _get_alert_rule(self, uid: str) -> PrometheusAlertRule:
        try:
            alert_rule = PrometheusAlertRule.objects.get(uid=uid)
            return alert_rule
        except PrometheusAlertRule.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> HttpResponse:
        """Prometheus alert rule get view.

        request: Http GET request.
        return: Http JSON response.
        """
        alert_rule = self._get_alert_rule(uid)
        serialized = PrometheusAlertRuleSerializer(alert_rule)

        response = HttpResponse(
            serialized.data["rules"],
            content_type="application/yaml",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{serialized.data["uid"]}.rule"'
        )
        return response

    def patch(self, request: Request, uid: str) -> Response:
        """Prometheus alert rule patch view.

        request: Http PATCH request.
        return: Http JSON response.
        """
        alert_rule = self._get_alert_rule(uid)
        serialized = PrometheusAlertRuleSerializer(
            alert_rule, data=request.data, partial=True
        )
        if serialized.is_valid():
            serialized.save()
            return Response(serialized.data)
        return Response(serialized.errors, status=400)

    def delete(self, request: Request, uid: str) -> Response:
        """Prometheus alert rule delete view.

        request: Http DELETE request.
        return: Http JSON response.
        """
        alert_rule = self._get_alert_rule(uid)
        alert_rule.delete()
        return Response(status=204)
