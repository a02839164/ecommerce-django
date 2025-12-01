# support/forms.py
from django import forms
from .models import SupportTicket

class SupportTicketForm(forms.ModelForm):
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={"rows": 4,"placeholder": "Type your message..."}),
        required=True
    )

    class Meta:
        model = SupportTicket
        fields = ["subject", "category", "message"]
