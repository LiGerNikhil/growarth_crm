from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import requests
from .models import Lead

@login_required
def fetch_google_sheets_data(request):
    """Fetch data directly from Google Sheets"""
    script_url = "https://script.google.com/macros/s/AKfycbxd8IrL9YKRIMYZo4Rj9g3LL93m5eT28ANKxX3rzudQC-kNUVm6Nig2VNBTR_aygna1Mw/exec"
    
    try:
        response = requests.post(script_url, data={'action': 'get_all_data'}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({'success': True, 'data': data})
        else:
            return JsonResponse({'success': False, 'error': f'HTTP {response.status_code}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def google_sheets_sheet1(request):
    """Display Sheet1 data (Loan Applications)"""
    return render(request, 'crm/google_sheets_sheet.html', {
        'page_title': 'Google Sheets - Sheet1 (Loan Applications)',
        'sheet_name': 'Sheet1',
        'sheet_type': 'loan'
    })

@login_required
def google_sheets_quotes(request):
    """Display Quotes tab data"""
    return render(request, 'crm/google_sheets_sheet.html', {
        'page_title': 'Google Sheets - Sheet2 (Quotes)',
        'sheet_name': 'Sheet2', 
        'sheet_type': 'quote'
    })
