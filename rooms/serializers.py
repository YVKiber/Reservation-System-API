from rest_framework import serializers

from .models import Room, RoomType


class RoomTypeSerializer(serializers.ModelSerializer):
    rooms_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = RoomType
        fields = [
            'id',
            'name',
            'description',
            'rooms_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'rooms_count',
            'created_at',
            'updated_at',
        ]

class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(
        source='room_type.name',
        read_only=True
    )

    class Meta:
        model = Room
        fields = [
            'id',
            'name',
            'room_type',
            'room_type_name',
            'description',
            'capacity',
            'location',
            'created_at',
            'updated_at',
            'is_available',
        ]
        read_only_fields = [
            'id',
            'room_type_name',
            'created_at',
            'updated_at',
        ]

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Capacity cannot be less than 0'
            )

        return value

