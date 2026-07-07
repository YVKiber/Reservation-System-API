from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

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
