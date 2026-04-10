from django.db import models
from django.contrib.auth.models import User


class Lead(models.Model):
    """Lead model for managing potential customers"""
    
    LEAD_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]
    
    LEAD_SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('other', 'Other'),
    ]
    
    # Lead Type
    LEAD_TYPE_CHOICES = [
        ('loan', 'Loan Application'),
        ('quote', 'Quote Request'),
        ('general', 'General Inquiry'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    unique_id = models.CharField(max_length=255, unique=True, blank=True, null=True)  # For Google Sheets unique identification
    
    # Lead Details
    lead_type = models.CharField(max_length=20, choices=LEAD_TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=LEAD_STATUS_CHOICES, default='new')
    source = models.CharField(max_length=20, choices=LEAD_SOURCE_CHOICES, default='website')
    
    # Loan Information (for loan leads)
    loan_type = models.CharField(max_length=100, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    employment_status = models.CharField(max_length=100, blank=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    message = models.TextField(blank=True)
    consent = models.BooleanField(default=False)
    
    # System Fields
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this lead")
    
    # Google Sheets Integration
    google_sheets_id = models.CharField(max_length=100, blank=True, help_text="Google Sheets row ID")
    synced_with_google = models.BooleanField(default=False)
    google_sheet_url = models.URLField(blank=True, help_text="Google Sheets Web App URL")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.get_lead_type_display()})"
    
    @property
    def is_new(self):
        return self.status == 'new'
    
    @property
    def days_since_creation(self):
        from datetime import datetime
        return (datetime.now().date() - self.created_at.date()).days


class LeadActivity(models.Model):
    """Track activities and interactions with leads"""
    
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
        ('status_change', 'Status Change'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lead Activity"
        verbose_name_plural = "Lead Activities"
    
    def __str__(self):
        return f"{self.lead.name} - {self.get_activity_type_display()}"


class GoogleSheetsIntegration(models.Model):
    """Manage Google Sheets integration settings"""
    
    INTEGRATION_TYPE_CHOICES = [
        ('loan', 'Loan Form'),
        ('quote', 'Quote Form'),
    ]
    
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    script_url = models.URLField(help_text="Google Sheets Web App URL")
    webhook_url = models.URLField(blank=True, help_text="Local webhook endpoint")
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    total_records = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Google Sheets Integration"
        verbose_name_plural = "Google Sheets Integrations"
    
    def __str__(self):
        return f"{self.name} ({self.get_integration_type_display()})"
