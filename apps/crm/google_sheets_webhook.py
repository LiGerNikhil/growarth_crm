from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Lead

@method_decorator(csrf_exempt, name='dispatch')
class ImportGoogleSheetsRow(View):
    """Import a single row from Google Sheets to CRM"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            if not data.get('name') or not data.get('email'):
                return JsonResponse({
                    'success': False,
                    'error': 'Name and email are required'
                })
            
            # Check for duplicate
            if Lead.objects.filter(email=data['email'], name=data['name']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Lead with this name and email already exists'
                })
            
            # Create lead
            lead_data = {
                'name': data['name'],
                'email': data['email'],
                'phone': data.get('phone', ''),
                'lead_type': data.get('lead_type', 'general'),
                'message': data.get('message', ''),
                'source': 'google_sheets',
                'synced_with_google': True,
                'status': 'new'
            }
            
            # Add loan-specific fields if applicable
            if data.get('lead_type') == 'loan':
                lead_data.update({
                    'loan_type': data.get('loan_type', ''),
                    'loan_amount': data.get('loan_amount'),
                    'employment_status': data.get('employment_status', ''),
                    'monthly_income': data.get('monthly_income')
                })
            
            lead = Lead.objects.create(**lead_data)
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully imported lead: {lead.name}',
                'lead_id': lead.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
