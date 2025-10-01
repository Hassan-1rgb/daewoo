from django import forms
from .models import User, Route, Bus, ComplaintSuggestion, Booking

# ----------------------------
# Admin Form (for admins only)
# ----------------------------
class AdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'phone', 'email', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'  # force role to admin
        if commit:
            user.save()
        return user

# ----------------------------
# Customer Registration Form
# ----------------------------
class CustomerRegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['name', 'phone', 'cnic_passport', 'email', 'dob', 'password', 'city', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'cnic_passport': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'  # force role to customer
        if commit:
            user.save()
        return user

# ----------------------------
# Login Form
# ----------------------------
class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))




class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['origin', 'destination', 'duration', 'distance']
        widgets = {
            'origin': forms.TextInput(attrs={'class':'form-control'}),
            'destination': forms.TextInput(attrs={'class':'form-control'}),
            'duration': forms.TextInput(attrs={'class':'form-control', 'placeholder':'HH:MM:SS'}),
            'distance': forms.NumberInput(attrs={'class':'form-control'}),
        }

class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['bus_number', 'capacity', 'route', 'bus_type', 'departure_time', 'price']
        widgets = {
            'bus_number': forms.TextInput(attrs={'class':'form-control'}),
            'capacity': forms.NumberInput(attrs={'class':'form-control'}),
            'route': forms.Select(attrs={'class':'form-control'}),
            'bus_type': forms.Select(attrs={'class':'form-control'}),
            'departure_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'price': forms.NumberInput(attrs={'class':'form-control', 'step': '0.01', 'min': '0'}),
        }



class ComplaintSuggestionForm(forms.ModelForm):
    class Meta:
        model = ComplaintSuggestion
        fields = ["suggestion_type", "title", "first_name", "email", "mobile_number", "message"]
        widgets = {
            "suggestion_type": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "03#########"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }




class BookingForm(forms.ModelForm):
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = Booking
        fields = ["route", "bus", "booking_date", "seat_number"]
