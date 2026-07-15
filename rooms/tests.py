from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking

from .models import Room, RoomType


User = get_user_model()


class RoomsAPITests(APITestCase):
    def setUp(self):
        self.room_types_url = "/api/room-types/"
        self.rooms_url = "/api/rooms/"

        self.user = User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="StrongPassword123!",
            first_name="Existing",
            last_name="User",
        )

        self.staff_user = User.objects.create_user(
            username="staff_user",
            email="staff@example.com",
            password="StrongPassword123!",
            is_staff=True,
        )

        self.room_type = RoomType.objects.create(
            name="Conference Room",
            description="Room type for meetings.",
        )

        self.room = Room.objects.create(
            name="Room A",
            room_type=self.room_type,
            location="First floor",
            capacity=8,
            description="Small meeting room.",
            is_available=True,
        )

    def test_anyone_can_list_room_types(self):
        response = self.client.get(self.room_types_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_anyone_can_list_rooms(self):
        response = self.client.get(self.rooms_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_regular_user_cannot_create_room_type(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "name": "Training Room",
            "description": "Room type for trainings.",
        }

        response = self.client.post(
            self.room_types_url,
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_create_room_type(self):
        self.client.force_authenticate(user=self.staff_user)

        payload = {
            "name": "Training Room",
            "description": "Room type for trainings.",
        }

        response = self.client.post(
            self.room_types_url,
            payload,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RoomType.objects.count(), 2)
        self.assertEqual(response.data["name"], "Training Room")

    def test_regular_user_cannot_create_room(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "name": "Room B",
            "room_type": self.room_type.id,
            "location": "Second floor",
            "capacity": 10,
            "description": "Another meeting room.",
            "is_active": True,
        }

        response = self.client.post(
            self.rooms_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_staff_user_can_create_room(self):
        self.client.force_authenticate(user=self.staff_user)

        payload = {
            "name": "Room B",
            "room_type": self.room_type.id,
            "location": "Second floor",
            "capacity": 10,
            "description": "Another meeting room.",
            "is_active": True,
        }

        response = self.client.post(
            self.rooms_url,
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Room.objects.count(), 2)
        self.assertEqual(response.data["name"], "Room B")
        self.assertEqual(response.data["room_type_name"], "Conference Room")

    def test_room_capacity_must_be_greater_than_zero(self):
        self.client.force_authenticate(user=self.staff_user)

        payload = {
            "name": "Invalid Room",
            "room_type": self.room_type.id,
            "location": "Third floor",
            "capacity": 0,
            "description": "Invalid capacity.",
            "is_active": True,
        }

        response = self.client.post(
            self.rooms_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.data)

    def test_room_availability_requires_date_query_param(self):
        response = self.client.get(
            f"{self.rooms_url}{self.room.id}/availability/"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.data)

    def test_room_availability_rejects_invalid_date_format(self):
        response = self.client.get(
            f"{self.rooms_url}{self.room.id}/availability/?date=10-07-2026"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date", response.data)

    def test_room_availability_returns_room_data_and_active_bookings(self):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Team meeting",
            description="Weekly team sync.",
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CONFIRMED,
        )

        selected_date = start_time.date().isoformat()

        response = self.client.get(
            f"{self.rooms_url}{self.room.id}/availability/?date={selected_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("room", response.data)
        self.assertIn("date", response.data)
        self.assertIn("bookings", response.data)

        self.assertEqual(response.data["room"]["id"], self.room.id)
        self.assertEqual(response.data["room"]["name"], self.room.name)
        self.assertEqual(
            response.data["room"]["room_type"],
            self.room_type.id,
        )
        self.assertEqual(
            response.data["room"]["room_type_name"],
            self.room_type.name,
        )
        self.assertEqual(
            response.data["room"]["location"],
            self.room.location,
        )
        self.assertEqual(
            response.data["room"]["capacity"],
            self.room.capacity,
        )
        self.assertEqual(
            response.data["room"]["description"],
            self.room.description,
        )
        self.assertEqual(
            response.data["room"]["is_available"],
            self.room.is_available,
        )

        self.assertEqual(response.data["date"], selected_date)
        self.assertEqual(len(response.data["bookings"]), 1)
        self.assertEqual(response.data["bookings"][0]["id"], booking.id)
        self.assertEqual(
            response.data["bookings"][0]["title"],
            "Team meeting",
        )
        self.assertEqual(
            response.data["bookings"][0]["status"],
            Booking.Status.CONFIRMED,
        )

    def test_room_availability_does_not_return_cancelled_bookings(self):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Cancelled meeting",
            description="Cancelled booking.",
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.CANCELLED,
        )

        selected_date = start_time.date().isoformat()

        response = self.client.get(
            f"{self.rooms_url}{self.room.id}/availability/?date={selected_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["room"]["id"], self.room.id)
        self.assertEqual(response.data["date"], selected_date)
        self.assertEqual(len(response.data["bookings"]), 0)

    def test_room_availability_does_not_return_completed_bookings(self):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Completed meeting",
            description="Completed booking.",
            start_time=start_time,
            end_time=end_time,
            status=Booking.Status.COMPLETED,
        )

        selected_date = start_time.date().isoformat()

        response = self.client.get(
            f"{self.rooms_url}{self.room.id}/availability/?date={selected_date}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["room"]["id"], self.room.id)
        self.assertEqual(response.data["date"], selected_date)
        self.assertEqual(len(response.data["bookings"]), 0)