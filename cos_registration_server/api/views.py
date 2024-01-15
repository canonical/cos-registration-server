from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser

from devices.models import Device
from api.serializer import DeviceSerializer

@csrf_exempt
def devices(request):
    if request.method == 'GET':
        devices = Device.objects.all()
        serialized = DeviceSerializer(devices, many=True)
        return JsonResponse(serialized.data, safe=False)
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(data=data)
        if serialized.is_valid():
            print(f"HEEEEERRRRRR: {serialized.validated_data['uid']}")
            if Device.objects.filter(uid=serialized.validated_data['uid']).exists():
                return JsonResponse({"error": "Device uid already exists"}, status=409)
            serialized.save()
            return JsonResponse(serialized.data, status=201)
        return JsonResponse(serialized.errors, status=400)

@csrf_exempt
def device(request, uid):
    try:
        device = Device.objects.get(uid=uid)
    except Device.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serialized = DeviceSerializer(device)
        return JsonResponse(serialized.data)
    if request.method == 'PATCH':
        data = JSONParser().parse(request)
        serialized = DeviceSerializer(device, data=data, partial=True)
        if serialized.is_valid():
            serialized.save()
            return JsonResponse(serialized.data)
        return JsonResponse(serialized.errors, status=400)
    elif request.method == 'DELETE':
        device.delete()
        return HttpResponse(status=204)
