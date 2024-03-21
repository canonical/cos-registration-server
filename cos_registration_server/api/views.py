"""API views."""

import json

from api.serializer import (
    DeviceSerializer,
    FoxgloveDashboardSerializer,
    GrafanaDashboardSerializer,
)
from applications.models import FoxgloveDashboard, GrafanaDashboard
from devices.models import Device
from django.http import HttpResponse
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


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
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(data=data)
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
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(device, data=data, partial=True)
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
        data = JSONParser().parse(request)
        serialized = GrafanaDashboardSerializer(data=data)
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
        data = JSONParser().parse(request)
        serialized = GrafanaDashboardSerializer(
            dashboard, data=data, partial=True
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
        data = JSONParser().parse(request)
        serialized = FoxgloveDashboardSerializer(data=data)
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
        data = JSONParser().parse(request)
        serialized = FoxgloveDashboardSerializer(
            dashboard, data=data, partial=True
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
