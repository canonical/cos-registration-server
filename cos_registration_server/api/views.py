"""API views."""

from api.serializer import DeviceSerializer, GrafanaDashboardSerializer
from applications.models import GrafanaDashboard
from devices.models import Device
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser


def devices(request):
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


def device(request, uid):
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


def grafana_dashboards(request):
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


def grafana_dashboard(request, uid):
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
        return JsonResponse(serialized.data)
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
