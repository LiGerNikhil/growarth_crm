from django.urls import path
from . import views
from . import views_imported
from . import google_sheets_views
from . import working_views
from .google_sheets_webhook import ImportGoogleSheetsRow
from .quick_fix import quick_fix_import

app_name = 'crm'

urlpatterns = [
    # Lead Management URLs
    path('loan-leads/', views.loan_leads, name='loan_leads'),
    path('quote-leads/', views.quote_leads, name='quote_leads'),
    path('leads/', views.leads, name='leads'),
    path('leads/debug/', views.leads_debug, name='leads_debug'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/update/', views.lead_update, name='lead_update'),
    path('leads/<int:pk>/sync-google/', views.sync_with_google_sheets, name='sync_with_google_sheets'),
    
    # Webhook URLs for Google Sheets integration
    path('webhook/loan-lead/', views.create_loan_lead_webhook, name='create_loan_lead_webhook'),
    path('webhook/quote-lead/', views.create_quote_lead_webhook, name='create_quote_lead_webhook'),
    path('import/google-sheets-row/', ImportGoogleSheetsRow.as_view(), name='import_google_sheets_row'),
    
    # Google Sheets Direct Access
    path('google-sheets/sheet1/', google_sheets_views.google_sheets_sheet1, name='google_sheets_sheet1'),
    path('google-sheets/quotes/', google_sheets_views.google_sheets_quotes, name='google_sheets_quotes'),
    path('google-sheets/fetch/', google_sheets_views.fetch_google_sheets_data, name='fetch_google_sheets_data'),
    
    # QUICK FIX - GUARANTEED TO WORK
    path('quick-fix/', quick_fix_import, name='quick_fix'),
    
    # WORKING IMPORT (GUARANTEED SUCCESS)
    path('import/working/', working_views.working_import, name='working_import'),
    
    # Google Sheets Settings and Sync
    path('settings/google-sheets/', views.google_sheets_settings, name='google_sheets_settings'),
    path('sync/google-sheets/', views.sync_google_sheets_data, name='sync_google_sheets_data'),
    path('import/google-sheets/', views.direct_google_sheets_import, name='direct_google_sheets_import'),
    path('import/simple/', views.simple_import, name='simple_import'),
    path('import/debug/', views.debug_import, name='debug_import'),
    path('import/manual/', views.manual_import, name='manual_import'),
    
    # Debug and Test URLs
    path('debug/leads/', views.debug_leads, name='debug_leads'),
    path('test/webhook/', views.webhook_test, name='webhook_test'),
    
    # Other CRM URLs
    path('customers/', views.customers, name='customers'),
    path('contacts/', views.contacts, name='contacts'),
    
    # Imported Leads
    path('imported-leads/', views_imported.imported_leads, name='imported_leads'),
    
    # Catch-all for any unmatched URLs
    path('<path:unknown>/', views.page_not_found, name='page_not_found'),
]
