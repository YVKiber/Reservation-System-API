from django.utils import timezone

from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(
        source='room.name',
        read_only=True
    )
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            'id',
            'room',
            'room_name',
            'user',
            'user_username',
            'title',
            'description',
            'start_time',
            'end_time',
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'room_name',
            'user_username',
            'status',
            'created_at',
            'updated_at',
            'cancelled_at',
            'completed_at',
        ]

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        room = attrs.get('room')

        if self.instance:
            start_time = start_time or self.instance.start_time
            end_time = end_time or self.instance.end_time
            room = room or self.instance.room

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                {'end_time': 'End time must be later than start time.'}
            )

        if start_time and end_time < timezone.now():
            raise serializers.ValidationError(
                {'start_time': 'Start time cannot be in the past.'}
            )

        if room and not room.is_available:
            raise serializers.ValidationError(
                {"room": "This room is currently inactive and cannot be booked."}
            )

        if room and start_time and end_time:
            overlapping_bookings = Booking.objects.filter(
                room=room,
                status__in=[
                    Booking.Status.PENDING,
                    Booking.Status.CONFIRMED,
                ],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if self.instance:
                overlapping_bookings = overlapping_bookings.exclude(
                    pk=self.instance.pk
                )

            if overlapping_bookings.exists():
                raise serializers.ValidationError(
                    "This room is already booked for the selected time range."
                )

        return attrs