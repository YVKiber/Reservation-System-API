from django import forms

from bookings.models import Booking


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