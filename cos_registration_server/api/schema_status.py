"""API schema status."""

from api.serializer import (
    DeviceSerializer,
    FoxgloveDashboardSerializer,
    GrafanaDashboardSerializer,
    LokiAlertRuleFileSerializer,
    PrometheusAlertRuleFileSerializer,
)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse

code_200_device = {200: DeviceSerializer}
code_201_device = {201: DeviceSerializer}

code_200_device_certificate = {
    200: {
        "type": "object",
        "properties": {
            "certificate": {
                "type": "string",
                "description": "PEM-encoded certificate",
            },
            "private_key": {
                "type": "string",
                "description": "PEM-encoded private key",
            },
        },
    }
}

code_404_uid_not_found = {404: OpenApiResponse(description="UID not found")}
code_404_device_address_not_found = {
    404: OpenApiResponse(description="device address not found")
}
code_404_device_certificate_not_found = {
    404: OpenApiResponse(description="Device certficate not found")
}

code_200_grafana_dashboard = {200: GrafanaDashboardSerializer}
code_201_grafana_dashboard = {201: GrafanaDashboardSerializer}

code_200_foxglove_dashboard = {200: FoxgloveDashboardSerializer}
code_201_foxglove_dashboard = {201: FoxgloveDashboardSerializer}

code_200_dashboard = {
    200: OpenApiResponse(
        response=OpenApiTypes.STR,
        description="Dashboard JSON returned as an attachment with "
        "content-disposition header like: "
        "'attachment; filename=dashboard_uid.json'",
    )
}

code_404_dashboard_not_found = {
    404: OpenApiResponse(description="Dashboard not found")
}

code_200_prometheus_alert_rule_file = {200: PrometheusAlertRuleFileSerializer}
code_201_prometheus_alert_rule_file = {201: PrometheusAlertRuleFileSerializer}

code_200_loki_alert_rule_file = {200: LokiAlertRuleFileSerializer}
code_201_loki_alert_rule_file = {201: LokiAlertRuleFileSerializer}

code_404_alert_rule_file_not_found = {
    404: OpenApiResponse(description="Alert rule file not found")
}

code_400_field_parsing = {
    400: OpenApiResponse(
        response=OpenApiTypes.STR,
        examples=[
            OpenApiExample(
                "Date parse error",
                value={"field_name": "error details"},
                status_codes=["400"],
            )
        ],
    )
}
