from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from accounts.serializers import send_verification_email
from bookings.models import Booking
from rooms.models import RoomType, Room

User = get_user_model()

class BookingCreateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'room',
            'title',
            'description',
            'start_time',
            'end_time',
        ]
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError(
                'End time must be later than start time.'
            )

        return cleaned_data

class RegisterFrontendForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Create a strong password",
                "autocomplete": "new-password",
            }
        ),
    )

    password_confirm = forms.CharField(
        label="Confirm password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Repeat your password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Choose a username",
                    "autocomplete": "username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter your email",
                    "autocomplete": "email",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter your first name",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter your last name",
                    "autocomplete": "family-name",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "A user with this email already exists."
            )

        return email

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "A user with this username already exists."
            )

        return username

    def clean_password(self):
        password = self.cleaned_data["password"]

        validate_password(password)

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error(
                "password_confirm",
                "Passwords do not match."
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.is_active = False
        user.set_password(
            self.cleaned_data["password"]
        )

        if commit:
            user.save()
            send_verification_email(user)

        return user

class FrontendLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter your username",
                "autocomplete": "username",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )

class ResendVerificationForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )

    def save(self):
        email = self.cleaned_data["email"]

        user = User.objects.filter(email=email).first()

        if not user:
            return

        if user.is_active:
            return

        send_verification_email(user)


class PasswordResetRequestFrontendForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )


class PasswordResetConfirmFrontendForm(forms.Form):
    new_password = forms.CharField(
        label="New password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Create a strong password",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password_confirm = forms.CharField(
        label="Confirm password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Repeat your password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")

        validate_password(password)

        return password

    def clean(self):
        cleaned_data = super().clean()

        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if new_password and new_password_confirm and new_password != new_password_confirm:
            self.add_error(
                "new_password_confirm",
                "Passwords do not match."
            )
        return cleaned_data

class RoomTypeCreateForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room type name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room type description",
                    "rows": 4,
                }
            ),
        }

class RoomCreateForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "name",
            "room_type",
            "location",
            "capacity",
            "image",
            "description",
            "is_available",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room name",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room location",
                }
            ),
            "capacity": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room capacity",
                    "min": 1,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "placeholder": "Enter room description",
                    "rows": 4,
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-input",
                }
            ),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]

        if capacity <= 0:
            raise forms.ValidationError(
                "Capacity must be greater than 0."
            )

        return capacity

class RoomImageUpdateForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "image",
        ]
        widgets = {
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-input",
                }
            ),
        }