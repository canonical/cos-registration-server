from devices.models import Device
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class DeviceSerializer(serializers.Serializer):
    uid = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=Device.objects.all())],
    )
    creation_date = serializers.DateTimeField(read_only=True)
    address = serializers.IPAddressField(required=True)

    def create(self, validated_data):
        return Device.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.address = validated_data.get("address", instance.address)
        instance.save()
        return instance
