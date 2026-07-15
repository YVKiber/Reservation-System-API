from datetime import datetime, time

from django.utils import timezone

from bookings.models import Booking
from rooms.models import Room
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, View

from .forms import BookingCreateForm

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

class MyBookingsListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'frontend/bookings_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.select_related(
            'room',
            'room__room_type',
            'user',
        ).filter(
            user=self.request.user,
        ).order_by('-start_time')\

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingCreateForm
    template_name = 'frontend/booking_form.html'
    success_url = reverse_lazy('frontend:bookings-list')

    def form_valid(self, form):
        booking = form.save(commit=False)
        booking.user = self.request.user

        overlapping_bookings = Booking.objects.filter(
            room=booking.room,
            status__in=[
                Booking.Status.PENDING,
                Booking.Status.CONFIRMED,
            ],
            start_time__lt=booking.end_time,
            end_time__gt=booking.start_time,
        )

        if overlapping_bookings.exists():
            form.add_error(
                None,
                'This room is already booked for the selected time range.',
            )
            return self.form_invalid(form)

        booking.save()

        messages.success(
            self.request,
            'Booking was created successfully.',
        )

        return redirect(self.success_url)


class BookingCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = Booking.objects.filter(
            pk=pk,
            user=request.user,
        ).first()

        if not booking:
            messages.error(
                request,
                'Booking was not found or you do not have permission to cancel it.',
            )
            return redirect('frontend:bookings-list')

        if booking.status == Booking.Status.CANCELLED:
            messages.warning(
                request,
                'This booking is already cancelled.',
            )
            return redirect('frontend:bookings-list')

        if booking.status == Booking.Status.COMPLETED:
            messages.error(
                request,
                'Completed booking cannot be cancelled.',
            )
            return redirect('frontend:bookings-list')

        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(
            update_fields=[
                'status',
                'cancelled_at',
                'updated_at',
            ]
        )

        messages.success(
            request,
            'Booking was cancelled successfully.',
        )

        return redirect('frontend:bookings-list')