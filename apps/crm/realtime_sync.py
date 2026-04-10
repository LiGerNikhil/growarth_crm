import requests
import json
from django.core.management.base import BaseCommand
from apps.crm.models import Lead
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Real-time sync Google Sheets data to CRM'

    def handle(self, *args, **options):
        sync_google_sheets_to_crm()

def sync_google_sheets_to_crm():
    """Real-time sync Google Sheets data to CRM"""
    script_url = "https://script.google.com/macros/s/AKfycbxd8IrL9YKRIMYZo4Rj9g3LL93m5eT28ANKxX3rzudQC-kNUVm6Nig2VNBTR_aygna1Mw/exec"
    
    try:
        # Fetch data from Google Sheets - try individual sheets first
        sheet1_response = requests.post(script_url, data={'action': 'get_sheet1'}, timeout=30)
        sheet2_response = requests.post(script_url, data={'action': 'get_quotes'}, timeout=30)
        
        if sheet1_response.status_code != 200 or sheet2_response.status_code != 200:
            return False
        
        sheet1_result = sheet1_response.json()
        sheet2_result = sheet2_response.json()
        
        if not sheet1_result.get('success') or not sheet2_result.get('success'):
            return False
        
        # Get data from individual sheets
        sheet1_data = sheet1_result.get('data', [])
        sheet2_data = sheet2_result.get('data', [])
        
        # Get current CRM leads
        crm_leads = Lead.objects.filter(source='google_sheets')
        
        # Clear existing Google Sheets leads to avoid duplicates
        crm_leads.delete()
        
        # Process Sheet1 (Loan Applications)
        sheet1_email_set = set()
        
        for row in sheet1_data:
            if row.get('name') and row.get('email'):
                sheet1_email_set.add(row['email'])
                
                # Create unique identifier using email + name
                unique_id = f"{row['email']}_{row['name']}"
                
                # Create lead (no duplicates since we cleared first)
                lead = Lead.objects.create(
                    unique_id=unique_id,
                    email=row['email'],
                    name=row['name'],
                    phone=str(row.get('phone', '')),
                    lead_type='loan',
                    loan_type=row.get('loanType', ''),
                    loan_amount=float(row.get('loanAmount', 0)) if row.get('loanAmount') and str(row.get('loanAmount')).replace('.', '').isdigit() else None,
                    employment_status=row.get('employment', ''),
                    monthly_income=float(row.get('monthlyIncome', 0)) if row.get('monthlyIncome') and str(row.get('monthlyIncome')).replace('.', '').isdigit() else None,
                    message=row.get('message', ''),
                    status='new',
                    source='google_sheets',
                    synced_with_google=True
                )
        
        # Process Sheet2 (Quotes)
        sheet2_email_set = set()
        
        for row in sheet2_data:
            if row.get('name') and (row.get('email') or row.get('mobile')):
                email = row.get('email', '') or row.get('mobile', '')
                sheet2_email_set.add(email)
                
                # Create unique identifier using email + name
                unique_id = f"{email}_{row['name']}"
                
                # Create lead (no duplicates since we cleared first)
                lead = Lead.objects.create(
                    unique_id=unique_id,
                    email=email,
                    name=row['name'],
                    phone=str(row.get('mobile', '') or row.get('phone', '')),
                    lead_type='quote',
                    message=row.get('message', ''),
                    status='new',
                    source='google_sheets',
                    synced_with_google=True
                )
        
        # No need to remove leads since we cleared all first
        
        # Final count
        total_leads = Lead.objects.filter(source='google_sheets').count()
        loan_leads = Lead.objects.filter(source='google_sheets', lead_type='loan').count()
        quote_leads = Lead.objects.filter(source='google_sheets', lead_type='quote').count()
        
        return True
        
    except Exception as e:
        return False

if __name__ == "__main__":
    sync_google_sheets_to_crm()
