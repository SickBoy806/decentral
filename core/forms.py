from django import forms
from .models import Task
from accounts.models import CustomUser
from core.models import SupportTicket, TicketReply

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter users from same branch and role staff/user
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                branch=user.branch, role__in=['staff', 'user']
            )

class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description']  # Use 'description' not 'message'

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
