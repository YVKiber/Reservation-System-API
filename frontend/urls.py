from django.urls import path

from . import views
from .views import BookingCreateView, BookingCancelView, MyBookingsListView

app_name = 'frontend'


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('rooms/', views.RoomsListView.as_view(), name='rooms-list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('bookings/', MyBookingsListView.as_view(), name='bookings-list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/<int:pk>/cancel/',BookingCancelView.as_view(),name='booking-cancel',),
]