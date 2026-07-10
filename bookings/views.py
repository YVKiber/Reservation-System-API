
from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Booking
from .permissions import IsOwnerOrStaff
from .serializers import BookingSerializer


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    filterset_fields = [
        'room',
        'status',
        'start_time',
        'end_time',
    ]
    search_fields = [
        'title',
        'description',
        'room__name',
        'room__username',
    ]
    ordering_fields = [
        'start_time',
        'end_time',
        'created_at',
        'status',
    ]
    ordering = ('-start_time',)

    def get_queryset(self):
        queryset = Booking.objects.select_related(
            'room',
            'user',
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            user = self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()

        if booking.status == Booking.Status.CANCELLED:
            return Response(
                {"detail": "Booking is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if booking.status == Booking.Status.COMPLETED:
            return Response(
                {"detail": "Completed booking cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancelled_at', 'updated_at'])

        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()

        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff users can confirm bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status != Booking.Status.PENDING:
            return Response(
                {"detail": "Only pending bookings can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=['status', 'updated_at'])

        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        booking = self.get_object()

        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff users can complete bookings."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status not in [Booking.Status.PENDING, Booking.Status.CONFIRMED]:
            return Response(
                {"detail": "Only active bookings can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.Status.COMPLETED
        booking.completed_at = timezone.now()
        booking.save(update_fields=['status', 'updated_at', 'completed_at'])

        serializer = self.get_serializer(booking)
        return Response(serializer.data)




