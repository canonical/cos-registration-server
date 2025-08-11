"""API views."""

import json
from typing import Any, Dict, Tuple

import api.schema_status as status
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
from django.db import transaction
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
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

from .utils import generate_tls_certificate


class HealthView(APIView):
    """Health API view."""

    @extend_schema(
        summary="Health",
        responses={
            200: OpenApiResponse(description="The application is alive."),
        },
    )
    def get(self, request: Request) -> Response:
        """Health get view."""
        return Response()


class DevicesView(ListCreateAPIView):  # type: ignore[type-arg]
    """Devices API view."""

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    @extend_schema(
        summary="Register a device",
        description="Register a device by its ID",
        responses={
            **status.code_201_device,
            **status.code_400_field_parsing,
        },
    )
    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a device."""
        with transaction.atomic():
            response = super().post(request, *args, **kwargs)
            device_uid = response.data.get("uid")
            if device_uid:
                device_ip = response.data.get("address")
                cert_data = generate_tls_certificate(device_uid, device_ip)
                response.data["certificate"] = cert_data["certificate"]
                response.data["private_key"] = cert_data["private_key"]
        return response

    @extend_schema(
        summary="List devices",
        description="List all registered devices and their attribute",
        responses={**status.code_200_device},
        parameters=[
            OpenApiParameter(
                name="fields",
                description="Filter the fields provided."
                "Will only output the fields listed in the parameter."
                "Example: ?fields=uid,create_date",
                required=False,
                type=OpenApiTypes.STR,
            )
        ],
    )
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

    @extend_schema(
        summary="Get a device",
        description="Retrieve all the fields of a device by its ID",
        responses={
            **status.code_200_device,
            **status.code_404_uid_not_found,
        },
    )
    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a device."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update a device completely",
        description="Update all the fields of a given device",
        responses={
            **status.code_201_device,
            **status.code_400_field_parsing,
            **status.code_404_uid_not_found,
        },
    )
    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a device."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update a device partially",
        description="Update the provided fields of a given device",
        responses={
            **status.code_201_device,
            **status.code_400_field_parsing,
            **status.code_404_uid_not_found,
        },
    )
    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a device."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a device",
        description="Delete a registered device",
        responses={
            204: DeviceSerializer,
            **status.code_404_uid_not_found,
        },
    )
    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a device."""
        return super().delete(request, *args, **kwargs)


class GrafanaDashboardsView(ListCreateAPIView):  # type: ignore[type-arg]
    """GrafanaDashboards API view."""

    queryset = GrafanaDashboard.objects.all()
    serializer_class = GrafanaDashboardSerializer

    @extend_schema(
        summary="Add a Grafana dashboard",
        description="Add a Grafana dashboard by its ID",
        responses={
            **status.code_201_grafana_dashboard,
            **status.code_400_field_parsing,
        },
    )
    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Grafana dashboard."""
        return super().post(request, *args, **kwargs)

    @extend_schema(
        summary="List Grafana dashboards",
        description="List all Grafana dashboards and their attribute",
        responses={**status.code_200_grafana_dashboard},
    )
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

    @extend_schema(
        summary="Download Grafana dashboard JSON file",
        description="Returns Grafana dashboard JSON object, "
        "intended for file download.",
        responses={
            **status.code_200_dashboard,
            **status.code_404_dashboard_not_found,
        },
    )
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

    @extend_schema(
        summary="Update a Grafana dashboard completely",
        description="Update all the fields of a given Grafana dashboard",
        responses={
            **status.code_201_grafana_dashboard,
            **status.code_400_field_parsing,
            **status.code_404_dashboard_not_found,
        },
    )
    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Grafana dashboard."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Grafana dashboard partially",
        description="Update the provided fields of a given Grafana dashboard",
        responses={
            **status.code_201_grafana_dashboard,
            **status.code_400_field_parsing,
            **status.code_404_dashboard_not_found,
        },
    )
    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Grafana dashboard."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a Grafana dashboard",
        description="Delete a Grafana dashboard",
        responses={
            204: GrafanaDashboardSerializer,
            **status.code_404_dashboard_not_found,
        },
    )
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

    @extend_schema(
        summary="Add a Foxglove dashboard",
        description="Add a Foxglove dashboard by its ID",
        responses={
            **status.code_201_foxglove_dashboard,
            **status.code_400_field_parsing,
        },
    )
    def post(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """POST a Foxglove dashboard."""
        return super().post(request, *args, **kwargs)

    @extend_schema(
        summary="List Foxglove dashboards",
        description="List all Foxglove dashboards and their attribute",
        responses={**status.code_200_foxglove_dashboard},
    )
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

    @extend_schema(
        summary="Download Foxglove dashboard JSON file",
        description="Returns Foxglove dashboard JSON object, "
        "intended for file download.",
        responses={
            **status.code_200_dashboard,
            **status.code_404_dashboard_not_found,
        },
    )
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

    @extend_schema(
        summary="Update a Foxglove dashboard completely",
        description="Update all the fields of a given Foxglove dashboard",
        responses={
            **status.code_201_foxglove_dashboard,
            **status.code_400_field_parsing,
            **status.code_404_dashboard_not_found,
        },
    )
    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Foxglove dashboard."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Foxglove dashboard partially",
        description="Update the provided fields of a given Foxglove dashboard",
        responses={
            **status.code_201_foxglove_dashboard,
            **status.code_400_field_parsing,
            **status.code_404_dashboard_not_found,
        },
    )
    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Foxglove dashboard."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a Foxglove dashboard",
        description="Delete a Foxglove dashboard",
        responses={
            204: FoxgloveDashboardSerializer,
            **status.code_404_dashboard_not_found,
        },
    )
    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Foxglove dashboard."""
        return super().delete(request, *args, **kwargs)


class PrometheusAlertRuleFilesView(CreateAPIView):  # type: ignore[type-arg]
    """PrometheusAlertRuleFiles API view."""

    queryset = PrometheusAlertRuleFile.objects.all()
    serializer_class = PrometheusAlertRuleFileSerializer

    @extend_schema(
        summary="List Prometheus alert rule file",
        description="List all Prometheus alert rule file and their attribute."
        "This endpoint returns all the non-templated rules as well as "
        "the templated rules rendered for the devices that specified them.",
        responses={**status.code_200_prometheus_alert_rule_file},
    )
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

    @extend_schema(
        summary="Add a Prometheus alert rule file",
        description="Add a Prometheus alert rule file by its ID",
        responses={
            **status.code_201_prometheus_alert_rule_file,
            **status.code_400_field_parsing,
        },
    )
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

    @extend_schema(
        summary="Download Prometheus alert rule file",
        description="Returns Prometheus alert rule file."
        "Templated rules won't be rendered.",
        responses={
            **status.code_200_prometheus_alert_rule_file,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a Prometheus alert rule file."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Prometheus alert rule file completely",
        description="Update all the fields of a given "
        "Prometheus alert rule file",
        responses={
            **status.code_201_prometheus_alert_rule_file,
            **status.code_400_field_parsing,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Prometheus alert rule file."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Prometheus alert rule file partially",
        description="Update the provided fields of a given "
        "Prometheus alert rule file",
        responses={
            **status.code_201_prometheus_alert_rule_file,
            **status.code_400_field_parsing,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Prometheus alert rule file."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a Prometheus alert rule file",
        description="Delete a Prometheus alert rule file",
        responses={
            204: PrometheusAlertRuleFileSerializer,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Prometheus alert rule file."""
        return super().delete(request, *args, **kwargs)


class LokiAlertRuleFilesView(CreateAPIView):  # type: ignore[type-arg]
    """LokiAlertRuleFiles API view."""

    queryset = LokiAlertRuleFile.objects.all()
    serializer_class = LokiAlertRuleFileSerializer

    @extend_schema(
        summary="List Loki alert rule file",
        description="List all Loki alert rule file and their attribute."
        "This endpoint returns all the non-templated rules as well as "
        "the templated rules rendered for the devices that specified them.",
        responses={**status.code_200_loki_alert_rule_file},
    )
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

    @extend_schema(
        summary="Add a Loki alert rule file",
        description="Add a Loki alert rule file by its ID",
        responses={
            **status.code_201_loki_alert_rule_file,
            **status.code_400_field_parsing,
        },
    )
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

    @extend_schema(
        summary="Download Loki alert rule file",
        description="Returns Loki alert rule file."
        "Templated rules won't be rendered.",
        responses={
            **status.code_200_loki_alert_rule_file,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def get(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """GET a Loki alert rule file."""
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Loki alert rule file completely",
        description="Update all the fields of a given Loki alert rule file",
        responses={
            **status.code_201_loki_alert_rule_file,
            **status.code_400_field_parsing,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def put(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PUT a Loki alert rule file."""
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Update a Loki alert rule file partially",
        description="Update the provided fields of a given "
        "Loki alert rule file",
        responses={
            **status.code_201_loki_alert_rule_file,
            **status.code_400_field_parsing,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def patch(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """PATCH a Loki alert rule file."""
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a Loki alert rule file",
        description="Delete a Loki alert rule file",
        responses={
            204: LokiAlertRuleFileSerializer,
            **status.code_404_alert_rule_file_not_found,
        },
    )
    def delete(
        self, request: Request, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> Response:
        """DELETE a Loki alert rule file."""
        return super().delete(request, *args, **kwargs)
