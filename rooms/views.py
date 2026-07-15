from datetime import datetime, time

from django.db.models import Count
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bookings.models import Booking

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

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        room = self.get_object()
        date_value = request.query_params.get('date')

        if not date_value:
            return Response(
                {
                    "date": (
                        "This query parameter is required. "
                        "Use YYYY-MM-DD format."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            selected_date = datetime.strptime(
                date_value,
                "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {
                    "date": "Invalid date format. Use YYYY-MM-DD."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        day_start = timezone.make_aware(
            datetime.combine(selected_date, time.min)
        )
        day_end = timezone.make_aware(
            datetime.combine(selected_date, time.max)
        )

        bookings = Booking.objects.filter(
            room=room,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ],
            start_time__lt = day_end,
            end_time__gt = day_start,
        ).order_by('start_time')

        room_data = RoomSerializer(room).data

        bookings_data = [
            {
                'id': booking.id,
                'title': booking.title,
                'start_time': booking.start_time,
                'end_time': booking.end_time,
                "status": booking.status,
             }
            for booking in bookings
        ]

        return Response(
            {
                'room': room_data,
                'date': selected_date.isoformat(),
                'bookings': bookings_data,
            }
        )