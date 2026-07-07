from django.shortcuts import render
from django.db.models import Count

from rest_framework import viewsets

from .models import Room, RoomType
from .permissions import IsStaffOrReadOnly
from .serializers import RoomSerializer, RoomTypeSerializer


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return RoomType.objects.annotate(
            rooms_count=Count('rooms')
        ).order_by(
            'name'
        )

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = [
        'room_type',
        'is_available',
        'capacity',
    ]
    search_fields = [
        'name',
        'description',
        'room_type_name',
        'location',
    ]
    ordering_fields = [
        'name',
        'capacity',
        'created_at',
    ]
    ordering = ['name']

    def get_queryset(self):
        return Room.objects.select_related(
            'room_type',
        ).order_by(
            'name'
        )