from django import forms
from .models import Lead, LeadActivity


class LeadForm(forms.ModelForm):
    """Form for creating and updating leads"""
    
    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'phone', 'lead_type', 'status', 'source', 'loan_type', 
            'loan_amount', 'employment_status', 'monthly_income', 
            'message', 'assigned_to', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'lead_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'loan_type': forms.TextInput(attrs={'class': 'form-control'}),
            'loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'employment_status': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class LeadActivityForm(forms.ModelForm):
    """Form for adding lead activities"""
    
    class Meta:
        model = LeadActivity
        fields = ['activity_type', 'description']
        widgets = {
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the activity...'}),
        }


class LoanLeadCaptureForm(forms.Form):
    """Form for capturing loan leads from website"""
    
    # Basic Information
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Full Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Phone Number',
            'required': False
        }),
        required=False
    )
    
    # Loan Information
    loan_type = forms.CharField(
        max_length=100,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        required=False
    )
    
    loan_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Desired Loan Amount',
            'step': '0.01',
            'required': False
        }),
        required=False
    )
    
    employment_status = forms.CharField(
        max_length=100,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        required=False
    )
    
    monthly_income = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Monthly Income',
            'step': '0.01',
            'required': False
        }),
        required=False
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about your requirements...',
            'required': False
        }),
        required=False
    )
    
    consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        required=True,
        label="I consent to be contacted regarding my loan inquiry"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for select fields
        self.fields['loan_type'].widget.choices = [
            ('', 'Select Loan Type'),
            ('personal_loan', 'Personal Loan'),
            ('home_loan', 'Home Loan'),
            ('business_loan', 'Business Loan'),
            ('car_loan', 'Car Loan'),
            ('education_loan', 'Education Loan'),
            ('other', 'Other')
        ]
        
        self.fields['employment_status'].widget.choices = [
            ('', 'Select Employment Status'),
            ('employed', 'Employed'),
            ('self_employed', 'Self Employed'),
            ('business_owner', 'Business Owner'),
            ('student', 'Student'),
            ('retired', 'Retired'),
            ('unemployed', 'Unemployed'),
            ('other', 'Other')
        ]


class QuoteLeadCaptureForm(forms.Form):
    """Form for capturing quote leads from website"""
    
    # Basic Information
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Full Name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        })
    )
    
    mobile = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Mobile Number',
            'required': False
        }),
        required=False
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about your requirements...',
            'required': False
        }),
        required=False
    )
    
    consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        required=True,
        label="I consent to be contacted regarding my quote request"
    )
