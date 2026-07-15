from datetime import datetime, time

from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from bookings.models import Booking
from rooms.models import Room


class HomeView(TemplateView):
    template_name = "frontend/home.html"


class RoomsListView(ListView):
    model = Room
    template_name = "frontend/rooms_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        return Room.objects.select_related("room_type").filter(
            is_available=True
        ).order_by("name")


class RoomDetailView(DetailView):
    model = Room
    template_name = "frontend/room_detail.html"
    context_object_name = "room"

    def get_queryset(self):
        return Room.objects.select_related("room_type")

    def get_selected_date(self):
        date_value = self.request.GET.get("date")

        if not date_value:
            return timezone.localdate()

        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return timezone.localdate()

    def get_bookings_for_date(self, room, selected_date):
        day_start = timezone.make_aware(
            datetime.combine(selected_date, time.min)
        )
        day_end = timezone.make_aware(
            datetime.combine(selected_date, time.max)
        )

        return Booking.objects.filter(
            room=room,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ],
            start_time__lt=day_end,
            end_time__gt=day_start,
        ).select_related("user").order_by("start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        room = self.object
        selected_date = self.get_selected_date()
        bookings = self.get_bookings_for_date(room, selected_date)

        context["selected_date"] = selected_date
        context["bookings"] = bookings

        return context