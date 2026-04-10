from django import forms
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):
    """Form for creating and editing support tickets"""
    
    class Meta:
        model = Ticket
        fields = ['subject', 'category', 'priority', 'description', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ticket subject'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your issue in detail...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].label = 'Subject'
        self.fields['category'].label = 'Category'
        self.fields['priority'].label = 'Priority'
        self.fields['description'].label = 'Description'
        self.fields['attachment'].label = 'Attachment (Optional)'


class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to tickets"""
    
    class Meta:
        model = TicketComment
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your comment here...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message'].label = 'Message'


class TicketStatusForm(forms.ModelForm):
    """Form for updating ticket status"""
    
    class Meta:
        model = Ticket
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
