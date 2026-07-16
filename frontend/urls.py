from django.urls import path

from . import views
from .views import BookingCreateView, BookingsListView, BookingStatusUpdateView, RoomTypeCreateView, RoomCreateView, \
    RoomAvailabilityUpdateView, RoomImageUpdateView, RoomImageDeleteView

app_name = 'frontend'


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.FrontendLoginView.as_view(), name='login'),
    path('logout/', views.FrontendLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterFrontendView.as_view(), name='register'),

    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),

    path('password-reset/', views.PasswordResetRequestFrontendView.as_view(), name='password-reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmFrontendView.as_view(), name='password-reset-confir'),

    path('rooms/', views.RoomsListView.as_view(), name='rooms-list'),
    path('room-types/create/', RoomTypeCreateView.as_view(), name='room-type-create'),
    path('rooms/create/', RoomCreateView.as_view(), name='room-create'),
    path('rooms/<int:pk>/image/', RoomImageUpdateView.as_view(), name='room-image-update'),
    path('rooms/<int:pk>/image/delete/', RoomImageDeleteView.as_view(), name='room-image-delete'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('bookings/', BookingsListView.as_view(), name='bookings-list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking-create'),
    path('rooms/<int:pk>/availability/',RoomAvailabilityUpdateView.as_view(),name='room-availability-update'),
    path('bookings/<int:pk>/status/',BookingStatusUpdateView.as_view(),name='booking-status-update'),
]