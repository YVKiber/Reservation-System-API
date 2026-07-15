from django.urls import path

from . import views


app_name = 'frontend'


urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('rooms/', views.RoomsListView.as_view(), name='rooms-list'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
]