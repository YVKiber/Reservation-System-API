from datetime import datetime, time

from django.utils import timezone
from django.contrib.auth import get_user_model, login, logout
from accounts.serializers import PasswordResetConfirmSerializer, PasswordResetRequestSerializer
from django.contrib.auth.tokens import default_token_generator
from bookings.models import Booking
from rooms.models import Room
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView, View, FormView
from django.utils.encoding import force_str
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import urlsafe_base64_decode
from .forms import BookingCreateForm, RegisterFrontendForm, PasswordResetConfirmFrontendForm, \
    PasswordResetRequestFrontendForm, ResendVerificationForm

User = get_user_model()

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

class FrontendLoginView(FormView):
    template_name = "frontend/login.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("frontend:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("frontend:home")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs['request'] = self.request

        return kwargs

    def form_valid(self, form):
        user = form.get_user()

        login(self.request, user)

        messages.success(
            self.request,
            "You have been logged in successfully."
        )

        return super().form_valid(form)

class FrontendLogoutView(View):
    def post(self, request):
        logout(request)

        messages.success(
            self.request,
            "You have been logged out successfully."
        )

        return redirect("frontend:home")

class RegisterFrontendView(FormView):
    template_name = "frontend/register.html"
    form_class = RegisterFrontendForm
    success_url = reverse_lazy("frontend:login")

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            "Account was created. Please check your email to verify your account.",
        )

        return super().form_valid(form)

class VerifyEmailView(TemplateView):
    template_name = 'frontend/email_verification_result.html'

    def get(self, request, *args, **kwargs):
        uid = request.GET.get('uid')
        token = request.GET.get('token')

        if not uid or not token:
            return self.render_to_response(
                self.get_context_data(
                    success=False,
                    title="Invalid verification link",
                    message="The verification link is missing required data.",
                )
            )

        try:
            user_id = force_str(
                urlsafe_base64_decode(uid)
            )

            user = User.objects.get(pk=user_id)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return self.render_to_response(
                self.get_context_data(
                    success=False,
                    title="Invalid verification link",
                    message="The verification link is invalid or broken.",
                )
            )

        if user.is_active:
            return self.render_to_response(
                self.get_context_data(
                    success=True,
                    title="Email already verified",
                    message="Your account has already been verified. You can log in.",
                )
            )

        if not default_token_generator.check_token(user, token):
            return self.render_to_response(
                self.get_context_data(
                    success=False,
                    title="Invalid or expired link",
                    message="This verification link is invalid or has expired. You can request a new one.",
                )
            )

        user.is_active = True
        user.save(
            update_fields=['is_active']
        )

        return self.render_to_response(
            self.get_context_data(
                success=True,
                title="Email verified successfully",
                message="Your email has been verified. You can now log in to your account.",
            )
        )

class ResendVerificationView(FormView):
    template_name = "frontend/resend_verification.html"
    form_class = ResendVerificationForm
    success_url = reverse_lazy("frontend:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("frontend:home")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            "If an unverified account with this email exists, a verification email has been sent."
        )

        return super().form_valid(form)


class PasswordResetRequestFrontendView(FormView):
    template_name = "frontend/password_reset.html"
    form_class = PasswordResetRequestFrontendForm
    success_url = reverse_lazy("frontend:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("frontend:home")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        serializer = PasswordResetRequestSerializer(
            data={
                "email": form.cleaned_data["email"],
            }
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        messages.success(
            self.request,
            "If an account with this email exists, a password reset email has been sent."
        )

        return super().form_valid(form)


class PasswordResetConfirmFrontendView(FormView):
    template_name = "frontend/password_reset_confirm.html"
    form_class = PasswordResetConfirmFrontendForm
    success_url = reverse_lazy("frontend:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("frontend:home")

        self.uid = self.request.GET.get('uid')
        self.token = self.request.GET.get('token')

        if not self.uid or not self.token:
            messages.error(
                request,
                "Invalid password reset link."
            )

            return redirect("frontend:password-reset")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        serializer = PasswordResetConfirmSerializer(
            data={
                "uid": self.uid,
                "token": self.token,
                "new_password": form.cleaned_data["new_password"],
            }
        )
        if not serializer.is_valid():
            for error_list in serializer.errors.values():
                for error in error_list:
                    form.add_error(
                        None,
                        error
                    )

            return self.form_invalid(form)

        serializer.save()

        messages.success(
            self.request,
            "Your password has been reset successfully. You can now log in."
        )

        return super().form_valid(form)
