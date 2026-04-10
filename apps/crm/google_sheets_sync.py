import requests
import json
from django.core.management.base import BaseCommand
from apps.crm.models import Lead
from datetime import datetime

def sync_google_sheets_to_crm():
    """Sync Google Sheets data to CRM database"""
    script_url = "https://script.google.com/macros/s/AKfycbxd8IrL9YKRIMYZo4Rj9g3LL93m5eT28ANKxX3rzudQC-kNUVm6Nig2VNBTR_aygna1Mw/exec"
    
    try:
        # Fetch data from Google Sheets
        response = requests.post(script_url, data={'action': 'get_all_data'}, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
        result = response.json()
        
        if not result.get('success'):
            print(f"❌ Error: {result.get('error')}")
            return False
        
        # Process Sheet1 (Loan Applications)
        sheet1_data = result.get('data', {}).get('sheet1', [])
        for row in sheet1_data:
            if row.get('name') and row.get('email'):
                # Check if lead already exists
                if not Lead.objects.filter(email=row['email'], name=row['name'], source='google_sheets').exists():
                    Lead.objects.create(
                        name=row.get('name', ''),
                        email=row.get('email', ''),
                        phone=str(row.get('phone', '')),
                        lead_type='loan',
                        loan_type=row.get('loanType', ''),
                        loan_amount=float(row.get('loanAmount', 0)) if row.get('loanAmount') else None,
                        employment_status=row.get('employment', ''),
                        monthly_income=float(row.get('monthlyIncome', 0)) if row.get('monthlyIncome') else None,
                        message=row.get('message', ''),
                        source='google_sheets',
                        status='new'
                    )
                    print(f"✅ Created loan lead: {row.get('name')}")
        
        # Process Sheet2 (Quotes)
        sheet2_data = result.get('data', {}).get('sheet2', [])
        for row in sheet2_data:
            if row.get('name') and row.get('email'):
                # Check if lead already exists
                if not Lead.objects.filter(email=row['email'], name=row['name'], source='google_sheets').exists():
                    Lead.objects.create(
                        name=row.get('name', ''),
                        email=row.get('email', ''),
                        phone=str(row.get('mobile', '') or row.get('phone', '')),
                        lead_type='quote',
                        message=row.get('message', ''),
                        source='google_sheets',
                        status='new'
                    )
                    print(f"✅ Created quote lead: {row.get('name')}")
        
        print(f"✅ Sync completed: {len(sheet1_data)} loan leads, {len(sheet2_data)} quote leads")
        return True
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        return False

if __name__ == "__main__":
    sync_google_sheets_to_crm()
