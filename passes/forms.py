from django import forms
from django.forms import formset_factory
from .models import Event, EventSession, Member


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'venue', 'banner']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'input-field', 'rows': 4, 'placeholder': 'Description'}),
            'venue': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Venue'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'input-field-file'}),
        }


class EventSessionForm(forms.ModelForm):
    class Meta:
        model = EventSession
        fields = ['date', 'start_time', 'end_time', 'capacity']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'input-field', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input-field', 'type': 'time'}),
            'capacity': forms.NumberInput(attrs={'class': 'input-field', 'placeholder': '0 = unlimited'}),
        }


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'father_name', 'address', 'phone_number', 'company_name', 'pass_type']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Full Name'}),
            'father_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': "Father's Name"}),
            'address': forms.Textarea(attrs={'class': 'input-field', 'rows': 2, 'placeholder': 'Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Phone Number'}),
            'company_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Company Name (optional)'}),
            'pass_type': forms.Select(attrs={'class': 'input-field'}),
        }


MemberFormSet = formset_factory(MemberForm, extra=5, can_delete=False)


class RegisterPassForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=EventSession.objects.none(),
        widget=forms.Select(attrs={'class': 'input-field'}),
        label="Choose Date & Time",
    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event is not None:
            self.fields['session'].queryset = event.sessions.all()
