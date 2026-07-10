from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from rooms.models import Room, RoomType

from .models import Booking


User = get_user_model()


class BookingsAPITests(APITestCase):
    def setUp(self):
        self.bookings_url = "/api/bookings/"

        self.user = User.objects.create_user(
            username="regular_user",
            email="regular@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="StrongPassword123!",
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

        self.inactive_room = Room.objects.create(
            name="Inactive Room",
            room_type=self.room_type,
            location="Second floor",
            capacity=6,
            description="Inactive room.",
            is_available=False,
        )

        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = self.start_time + timedelta(hours=1)

    def test_authenticated_user_can_create_booking(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "room": self.room.id,
            "title": "Team meeting",
            "description": "Weekly team sync.",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(response.data["title"], "Team meeting")
        self.assertEqual(response.data["room"], self.room.id)
        self.assertEqual(response.data["room_name"], self.room.name)
        self.assertEqual(response.data["user_username"], self.user.username)
        self.assertEqual(response.data["status"], Booking.Status.PENDING)

    def test_anonymous_user_cannot_create_booking(self):
        payload = {
            "room": self.room.id,
            "title": "Anonymous booking",
            "description": "Should not be allowed.",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Booking.objects.count(), 0)

    def test_regular_user_sees_only_own_bookings(self):
        Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Own booking",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
        )

        Booking.objects.create(
            room=self.room,
            user=self.other_user,
            title="Other booking",
            description="Other user booking.",
            start_time=self.start_time + timedelta(hours=2),
            end_time=self.end_time + timedelta(hours=2),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.bookings_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Own booking")

    def test_staff_user_sees_all_bookings(self):
        Booking.objects.create(
            room=self.room,
            user=self.user,
            title="User booking",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
        )

        Booking.objects.create(
            room=self.room,
            user=self.other_user,
            title="Other user booking",
            description="Other user booking.",
            start_time=self.start_time + timedelta(hours=2),
            end_time=self.end_time + timedelta(hours=2),
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.bookings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["results"]), 2)

    def test_user_cannot_create_booking_in_past(self):
        self.client.force_authenticate(user=self.user)

        past_start_time = timezone.now() - timedelta(hours=2)
        past_end_time = timezone.now() - timedelta(hours=1)

        payload = {
            "room": self.room.id,
            "title": "Anonymous booking",
            "description": "Should not be allowed.",
            "start_time": past_start_time.isoformat(),
            "end_time": past_end_time.isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_time", response.data)
        self.assertEqual(Booking.objects.count(), 0)

    def test_user_cannot_create_booking_with_invalid_time_range(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "room": self.room.id,
            "title": "Invalid time range",
            "description": "End time is before start time.",
            "start_time": self.end_time.isoformat(),
            "end_time": self.start_time.isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_time", response.data)
        self.assertEqual(Booking.objects.count(), 0)

    def test_user_cannot_book_inactive_room(self):
        self.client.force_authenticate(user=self.user)

        payload = {
            "room": self.inactive_room.id,
            "title": "Inactive room booking",
            "description": "Should not be allowed.",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("room", response.data)
        self.assertEqual(Booking.objects.count(), 0)

    def test_user_cannot_create_overlapping_booking(self):
        Booking.objects.create(
            room=self.room,
            user=self.other_user,
            title="Existing booking",
            description="Already booked.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.user)

        payload = {
            "room": self.room.id,
            "title": "Overlapping booking",
            "description": "This should fail.",
            "start_time": (self.start_time + timedelta(minutes=30)).isoformat(),
            "end_time": (self.end_time + timedelta(minutes=30)).isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.count(), 1)

    def test_back_to_back_booking_is_allowed(self):
        Booking.objects.create(
            room=self.room,
            user=self.other_user,
            title="Existing booking",
            description="Already booked.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.user)

        payload = {
            "room": self.room.id,
            "title": "Back-to-back booking",
            "description": "This should be allowed.",
            "start_time": self.end_time.isoformat(),
            "end_time": (self.end_time + timedelta(hours=1)).isoformat(),
        }

        response = self.client.post(
            self.bookings_url,
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 2)

    def test_owner_can_cancel_own_booking(self):
        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Booking to cancel",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.PENDING,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"{self.bookings_url}{booking.id}/cancel/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(booking.cancelled_at)

    def test_staff_can_confirm_booking(self):
        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Booking to confirm",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.PENDING,
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            f"{self.bookings_url}{booking.id}/confirm/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_regular_user_cannot_confirm_booking(self):
        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Booking to confirm",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.PENDING,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"{self.bookings_url}{booking.id}/confirm/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_staff_can_complete_booking(self):
        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            title="Booking to complete",
            description="User booking.",
            start_time=self.start_time,
            end_time=self.end_time,
            status=Booking.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            f"{self.bookings_url}{booking.id}/complete/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking.refresh_from_db()

        self.assertEqual(booking.status, Booking.Status.COMPLETED)
        self.assertIsNotNone(booking.completed_at)