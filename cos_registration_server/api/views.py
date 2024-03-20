"""API views."""

import json

from api.serializer import (
    DeviceSerializer,
    FoxgloveDashboardSerializer,
    GrafanaDashboardSerializer,
)
from applications.models import FoxgloveDashboard, GrafanaDashboard
from devices.models import Device
from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser


def devices(request: HttpRequest) -> HttpResponse:
    """Devices API view.

    request: Http request (GET,POST).
    return: Http JSON response.
    """
    if request.method == "GET":
        devices = Device.objects.all().values(
            "uid", "creation_date", "address"
        )
        serialized = DeviceSerializer(devices, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(data=data)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)
    return HttpResponse(status=405)


def device(request: HttpRequest, uid: str) -> HttpResponse:
    """Device API view.

    request: Http request (GET,PACH, DELETE).
    uid: Device UID passed in the URL.
    return: Http JSON response.
    """
    try:
        device = Device.objects.get(uid=uid)
    except Device.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serialized = DeviceSerializer(device)
        return JsonResponse(serialized.data)
    if request.method == "PATCH":
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(device, data=data, partial=True)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == "DELETE":
        device.delete()
        return HttpResponse(status=204)
    return HttpResponse(status=405)


def grafana_dashboards(request: HttpRequest) -> HttpResponse:
    """Grafana dashboards API view.

    request: Http request (GET,POST).
    return: Http JSON response.
    """
    if request.method == "GET":
        dashboards = GrafanaDashboard.objects.all()
        serialized = GrafanaDashboardSerializer(dashboards, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serialized = GrafanaDashboardSerializer(data=data)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)
    return HttpResponse(status=405)


def grafana_dashboard(request: HttpRequest, uid: str) -> HttpResponse:
    """Grafana dashboard API view.

    request: Http request (GET,PACH, DELETE).
    uid: GrafanaDashboard UID passed in the URL.
    return: Http JSON response.
    """
    try:
        dashboard = GrafanaDashboard.objects.get(uid=uid)
    except GrafanaDashboard.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serialized = GrafanaDashboardSerializer(dashboard)
        response = HttpResponse(
            json.dumps(serialized.data["dashboard"]),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{serialized.data["uid"]}.json"'
        )
        return response
    if request.method == "PATCH":
        data = JSONParser().parse(request)
        serialized = GrafanaDashboardSerializer(
            dashboard, data=data, partial=True
        )
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == "DELETE":
        dashboard.delete()
        return HttpResponse(status=204)
    return HttpResponse(status=405)


def foxglove_dashboards(request: HttpRequest) -> HttpResponse:
    """Foxglove dashboards API view.

    request: Http request (GET,POST).
    return: Http JSON response.
    """
    if request.method == "GET":
        dashboards = FoxgloveDashboard.objects.all()
        serialized = FoxgloveDashboardSerializer(dashboards, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serialized = FoxgloveDashboardSerializer(data=data)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)
    return HttpResponse(status=405)


def foxglove_dashboard(request: HttpRequest, uid: str) -> HttpResponse:
    """Foxglove dashboard API view.

    request: Http request (GET,PACH, DELETE).
    uid: FoxgloveDashboard UID passed in the URL.
    return: Http JSON response.
    """
    try:
        dashboard = FoxgloveDashboard.objects.get(uid=uid)
    except FoxgloveDashboard.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serialized = FoxgloveDashboardSerializer(dashboard)
        response = HttpResponse(
            json.dumps(serialized.data["dashboard"]),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{serialized.data["uid"]}.json"'
        )
        return response
    if request.method == "PATCH":
        data = JSONParser().parse(request)
        serialized = FoxgloveDashboardSerializer(
            dashboard, data=data, partial=True
        )
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == "DELETE":
        dashboard.delete()
        return HttpResponse(status=204)
    return HttpResponse(status=405)
