from django import forms
from .models import Booking, Payment


class BookingAdminForm(forms.ModelForm):
    """Admin form for Booking model"""
    
    class Meta:
        model = Booking
        fields = '__all__'
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class PaymentInlineForm(forms.ModelForm):
    """Inline form for Payment"""
    
    class Meta:
        model = Payment
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
