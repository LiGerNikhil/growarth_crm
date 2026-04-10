from django.contrib import admin
from .models import Lead, LeadActivity, GoogleSheetsIntegration


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'phone', 'lead_type', 'status', 'source', 
        'loan_type', 'loan_amount', 'assigned_to', 'created_at', 'synced_with_google'
    ]
    list_filter = [
        'lead_type', 'status', 'source', 'loan_type', 'employment_status', 
        'synced_with_google', 'created_at'
    ]
    search_fields = ['name', 'email', 'phone', 'message']
    list_editable = ['status', 'assigned_to']
    readonly_fields = ['created_at', 'updated_at', 'synced_with_google']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'lead_type', 'status', 'source')
        }),
        ('Loan Information', {
            'fields': ('loan_type', 'loan_amount', 'employment_status', 'monthly_income'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('message', 'consent', 'assigned_to', 'notes')
        }),
        ('Google Sheets Integration', {
            'fields': ('google_sheet_url', 'google_sheets_id', 'synced_with_google'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'description', 'created_by', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['lead__name', 'lead__email', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('lead', 'activity_type', 'description', 'created_by')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lead', 'created_by')


@admin.register(GoogleSheetsIntegration)
class GoogleSheetsIntegrationAdmin(admin.ModelAdmin):
    list_display = ['name', 'integration_type', 'is_active', 'total_records', 'last_sync']
    list_filter = ['integration_type', 'is_active', 'created_at']
    search_fields = ['name', 'script_url']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Integration Information', {
            'fields': ('name', 'integration_type', 'script_url', 'webhook_url')
        }),
        ('Status Information', {
            'fields': ('is_active', 'total_records', 'last_sync')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
