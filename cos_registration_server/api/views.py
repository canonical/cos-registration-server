"""API views."""

import json
from typing import Any, Dict, Tuple

from api.serializer import (
    DeviceSerializer,
    FoxgloveDashboardSerializer,
    GrafanaDashboardSerializer,
    LokiAlertRuleFileSerializer,
    PrometheusAlertRuleFileSerializer,
)
from applications.models import (
    FoxgloveDashboard,
    GrafanaDashboard,
    LokiAlertRuleFile,
    PrometheusAlertRuleFile,
)
from applications.utils import render_alert_rule_template_for_device
from devices.models import Device
from django.http import HttpResponse
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Health API view."""

    def get(self, request: Request) -> Response:
        """Health get view."""
        return Response()


class DevicesView(ListCreateAPIView):  # type: ignore[type-arg]
    """Devices API view."""

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a device."""
        return super().post(request, *args, **kwargs)

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET devices."""
        return super().get(request, *args, **kwargs)


class DeviceView(RetrieveUpdateDestroyAPIView):  # type: ignore[type-arg]
    """Device API view."""

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = "uid"

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a device."""
        return super().get(request, *args, **kwargs)

    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a device."""
        return super().put(request, *args, **kwargs)

    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a device."""
        return super().patch(request, *args, **kwargs)

    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a device."""
        return super().delete(request, *args, **kwargs)


class GrafanaDashboardsView(ListCreateAPIView):  # type: ignore[type-arg]
    """GrafanaDashboards API view."""

    queryset = GrafanaDashboard.objects.all()
    serializer_class = GrafanaDashboardSerializer

    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Grafana dashboard."""
        return super().post(request, *args, **kwargs)

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET Grafana dashboards."""
        return super().get(request, *args, **kwargs)


class GrafanaDashboardView(
    DestroyAPIView,  # type: ignore[type-arg]
    UpdateAPIView,  # type: ignore[type-arg]
):
    """GrafanaDashboard API view."""

    queryset = GrafanaDashboard.objects.all()
    serializer_class = GrafanaDashboardSerializer
    lookup_field = "uid"

    def _get_dashboard(self, uid: str) -> GrafanaDashboard:
        try:
            dashboard = GrafanaDashboard.objects.get(uid=uid)
            return dashboard
        except GrafanaDashboard.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> HttpResponse:
        """Grafana dashboard get view.

        Retuns the file instead of the model view.
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

    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Grafana dashboard."""
        return super().put(request, *args, **kwargs)

    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Grafana dashboard."""
        return super().patch(request, *args, **kwargs)

    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Grafana dashboard."""
        return super().delete(request, *args, **kwargs)


class FoxgloveDashboardsView(ListCreateAPIView):  # type: ignore[type-arg]
    """FoxgloveDashboards API view."""

    queryset = FoxgloveDashboard.objects.all()
    serializer_class = FoxgloveDashboardSerializer
    lookup_field = "uid"

    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Foxglove dashboard."""
        return super().post(request, *args, **kwargs)

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET Foxglove dashboards."""
        return super().get(request, *args, **kwargs)


class FoxgloveDashboardView(
    DestroyAPIView,  # type: ignore[type-arg]
    UpdateAPIView,  # type: ignore[type-arg]
):
    """FoxgloveDashboard API view."""

    queryset = FoxgloveDashboard.objects.all()
    serializer_class = FoxgloveDashboardSerializer
    lookup_field = "uid"

    def _get_dashboard(self, uid: str) -> FoxgloveDashboard:
        try:
            dashboard = FoxgloveDashboard.objects.get(uid=uid)
            return dashboard
        except FoxgloveDashboard.DoesNotExist:
            raise NotFound("Object does not exist")

    def get(self, request: Request, uid: str) -> HttpResponse:
        """Foxglove dashboard get view.

        Retuns the file instead of the model view.
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

    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Foxglove dashboard."""
        return super().put(request, *args, **kwargs)

    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Foxglove dashboard."""
        return super().patch(request, *args, **kwargs)

    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Foxglove dashboard."""
        return super().delete(request, *args, **kwargs)


class PrometheusAlertRuleFilesView(CreateAPIView):  # type: ignore[type-arg]
    """PrometheusAlertRuleFiles API view."""

    queryset = PrometheusAlertRuleFile.objects.all()
    serializer_class = PrometheusAlertRuleFileSerializer

    def get(self, request: Request) -> Response:
        """Prometheus Alert Rules get view.

        Return non-templated as well as rendered templated rules.
        """
        # retrieve alert rules that are not a template and serialize them
        no_template_alert_rules = PrometheusAlertRuleFile.objects.filter(
            template=False
        )

        serialized = PrometheusAlertRuleFileSerializer(
            no_template_alert_rules, many=True
        )

        # retrieve template alert rules and render them
        rendered_rules = []

        template_alert_rules = PrometheusAlertRuleFile.objects.filter(
            template=True
        )
        devices = Device.objects.all()

        for device in devices:
            for rule in device.prometheus_alert_rule_files.all():
                if rule in template_alert_rules:
                    rendered_rule = render_alert_rule_template_for_device(
                        rule, device
                    )
                    rendered_rules.append(
                        {
                            "uid": rule.uid + "/" + device.uid,
                            "rules": rendered_rule,
                        }
                    )

        # rendered rules are already dumped to get them rendered via jinja
        # hence they are already serialized as strings.
        serialized_list = list(serialized.data) + rendered_rules
        return Response(serialized_list)

    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Prometheus alert rule file."""
        return super().post(request, *args, **kwargs)


class PrometheusAlertRuleFileView(
    RetrieveUpdateDestroyAPIView  # type: ignore[type-arg]
):
    """PrometheusAlertRuleFile API view.

    Return non rendered rule.
    """

    queryset = PrometheusAlertRuleFile.objects.all()
    serializer_class = PrometheusAlertRuleFileSerializer
    lookup_field = "uid"

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a Prometheus alert rule file."""
        return super().get(request, *args, **kwargs)

    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Prometheus alert rule file."""
        return super().put(request, *args, **kwargs)

    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Prometheus alert rule file."""
        return super().patch(request, *args, **kwargs)

    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Prometheus alert rule file."""
        return super().delete(request, *args, **kwargs)


class LokiAlertRuleFilesView(CreateAPIView):  # type: ignore[type-arg]
    """LokiAlertRuleFiles API view."""

    queryset = LokiAlertRuleFile.objects.all()
    serializer_class = LokiAlertRuleFileSerializer

    def get(self, request: Request) -> Response:
        """Loki Alert Rules get view.

        Return non-templated as well as rendered templated rules.
        """
        # retrieve alert rules that are not a template and serialize them
        no_template_alert_rules = LokiAlertRuleFile.objects.filter(
            template=False
        )

        serialized = LokiAlertRuleFileSerializer(
            no_template_alert_rules, many=True
        )

        # retrieve template alert rules and render them
        rendered_rules = []

        template_alert_rules = LokiAlertRuleFile.objects.filter(template=True)
        devices = Device.objects.all()

        for device in devices:
            for rule in device.loki_alert_rule_files.all():
                if rule in template_alert_rules:
                    rendered_rule = render_alert_rule_template_for_device(
                        rule, device
                    )
                    rendered_rules.append(
                        {
                            "uid": rule.uid + "/" + device.uid,
                            "rules": rendered_rule,
                        }
                    )

        # rendered rules are already dumped to get them rendered via jinja
        # hence they are already serialized as strings.
        serialized_list = list(serialized.data) + rendered_rules
        return Response(serialized_list)

    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Loki alert rule file."""
        return super().post(request, *args, **kwargs)


class LokiAlertRuleFileView(
    RetrieveUpdateDestroyAPIView  # type: ignore[type-arg]
):
    """LokiAlertRuleFile API view.

    Returns non-rendered rules.
    """

    queryset = LokiAlertRuleFile.objects.all()
    lookup_field = "uid"
    serializer_class = LokiAlertRuleFileSerializer

    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a Loki alert rule file."""
        return super().get(request, *args, **kwargs)

    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Loki alert rule file."""
        return super().put(request, *args, **kwargs)

    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Loki alert rule file."""
        return super().patch(request, *args, **kwargs)

    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Loki alert rule file."""
        return super().delete(request, *args, **kwargs)
