from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
from .models import Lead, LeadActivity, GoogleSheetsIntegration
from .forms import LeadForm, LeadActivityForm
from .realtime_sync import sync_google_sheets_to_crm


def page_not_found(request, unknown):
    """
    Custom 404 handler for CRM module
    """
    return render(request, '404.html', status=404)


@login_required
def loan_leads(request):
    """
    Dedicated view for loan leads only
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Build query for loan leads only
    leads = Lead.objects.filter(lead_type='loan').order_by('-created_at')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Statistics for loan leads
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    contacted_leads = leads.filter(status='contacted').count()
    qualified_leads = leads.filter(status='qualified').count()
    
    # Loan type breakdown
    personal_loans = leads.filter(loan_type='personal_loan').count()
    home_loans = leads.filter(loan_type='home_loan').count()
    business_loans = leads.filter(loan_type='business_loan').count()
    
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Loan Leads',
        'leads': leads,
        'lead_type': 'loan',
        'status_filter': status_filter,
        'search_query': search_query,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'personal_loans': personal_loans,
        'home_loans': home_loans,
        'business_loans': business_loans,
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
        'lead_type': 'loan',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    
    return render(request, 'crm/loan_leads.html', context)


@login_required
def quote_leads(request):
    """
    Dedicated view for quote leads only
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Build query for quote leads only
    leads = Lead.objects.filter(lead_type='quote').order_by('-created_at')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Statistics for quote leads
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    contacted_leads = leads.filter(status='contacted').count()
    qualified_leads = leads.filter(status='qualified').count()
    
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Quote Leads',
        'leads': leads,
        'lead_type': 'quote',
        'status_filter': status_filter,
        'search_query': search_query,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
        'lead_type': 'quote',
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    return render(request, 'crm/quote_leads.html', context)


@login_required
def leads(request):
    """
    Unified leads management view
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    lead_type_filter = request.GET.get('lead_type', '')
    search_query = request.GET.get('search', '')
    
    # Build base query
    leads = Lead.objects.all().order_by('-created_at')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if lead_type_filter:
        leads = leads.filter(lead_type=lead_type_filter)
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Statistics
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    contacted_leads = leads.filter(status='contacted').count()
    qualified_leads = leads.filter(status='qualified').count()
    
    # Lead type statistics
    loan_leads = leads.filter(lead_type='loan').count()
    quote_leads = leads.filter(lead_type='quote').count()
    
    # Get counts for sidebar
    loan_leads_count = Lead.objects.filter(lead_type='loan').count()
    quote_leads_count = Lead.objects.filter(lead_type='quote').count()
    total_leads_count = Lead.objects.count()
    
    context = {
        'page_title': 'Leads',
        'leads': leads,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'loan_leads': loan_leads,
        'quote_leads': quote_leads,
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'lead_type_choices': Lead.LEAD_TYPE_CHOICES,
        'current_status': status_filter,
        'current_lead_type': lead_type_filter,
        'search_query': search_query,
        'loan_leads_count': loan_leads_count,
        'quote_leads_count': quote_leads_count,
        'total_leads_count': total_leads_count,
    }
    return render(request, 'crm/leads_unified.html', context)


@login_required
def lead_detail(request, pk):
    """
    Lead detail view
    """
    lead = get_object_or_404(Lead, pk=pk)
    activities = lead.activities.all()
    
    if request.method == 'POST':
        form = LeadActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.lead = lead
            activity.created_by = request.user
            activity.save()
            messages.success(request, 'Activity added successfully!')
            return redirect('crm:lead_detail', pk=lead.pk)
    else:
        form = LeadActivityForm()
    
    context = {
        'page_title': f'Lead - {lead.name}',
        'lead': lead,
        'activities': activities,
        'form': form,
    }
    return render(request, 'crm/lead_detail.html', context)


@login_required
def lead_update(request, pk):
    """
    Update lead status and details
    """
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            old_status = lead.status
            updated_lead = form.save()
            
            # Log status change
            if old_status != updated_lead.status:
                LeadActivity.objects.create(
                    lead=lead,
                    activity_type='status_change',
                    description=f'Status changed from {old_status} to {updated_lead.status}',
                    created_by=request.user
                )
            
            messages.success(request, 'Lead updated successfully!')
            return redirect('crm:lead_detail', pk=lead.pk)
    else:
        form = LeadForm(instance=lead)
    
    context = {
        'page_title': f'Update Lead - {lead.name}',
        'lead': lead,
        'form': form,
    }
    return render(request, 'crm/lead_form.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_loan_lead_webhook(request):
    """
    Webhook endpoint to receive loan leads from Google Sheets form
    """
    try:
        data = json.loads(request.body)
        
        # Create loan lead from form data
        lead = Lead.objects.create(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            lead_type='loan',
            loan_type=data.get('loanType', ''),
            loan_amount=data.get('loanAmount', 0) if data.get('loanAmount') else None,
            employment_status=data.get('employment', ''),
            monthly_income=data.get('monthlyIncome', 0) if data.get('monthlyIncome') else None,
            message=data.get('message', ''),
            consent=data.get('consent', False),
            source='website',
            google_sheet_url="https://script.google.com/macros/s/AKfycby-pJuT6CjTbSViGQd3qgOYzKQe-KPH0IQJ9UZCrujWCLXnnUeqWqz6sXkHOQ28tbiz-A/exec"
        )
        
        return JsonResponse({
            'success': True,
            'lead_id': lead.id,
            'lead_type': 'loan',
            'message': 'Loan lead created successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def create_quote_lead_webhook(request):
    """
    Webhook endpoint to receive quote leads from Google Sheets form
    """
    try:
        data = json.loads(request.body)
        
        # Create quote lead from form data
        lead = Lead.objects.create(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('mobile', ''),  # Note: quote form uses 'mobile' field
            lead_type='quote',
            message=data.get('message', ''),
            consent=data.get('consent', False),
            source='website',
            google_sheet_url="https://script.google.com/macros/s/AKfycby-pJuT6CjTbSViGQd3qgOYzKQe-KPH0IQJ9UZCrujWCLXnnUeqWqz6sXkHOQ28tbiz-A/exec"
        )
        
        return JsonResponse({
            'success': True,
            'lead_id': lead.id,
            'lead_type': 'quote',
            'message': 'Quote lead created successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def sync_with_google_sheets(request, pk):
    """
    Sync lead with Google Sheets
    """
    lead = get_object_or_404(Lead, pk=pk)
    
    try:
        # Use the specific Google Sheets URL for this lead
        script_url = lead.google_sheet_url or "https://script.google.com/macros/s/AKfycby-pJuT6CjTbSViGQd3qgOYzKQe-KPH0IQJ9UZCrujWCLXnnUeqWqz6sXkHOQ28tbiz-A/exec"
        
        # Prepare data for Google Sheets
        data_to_submit = {
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'loanType': lead.loan_type,
            'loanAmount': str(lead.loan_amount) if lead.loan_amount else '',
            'employment': lead.employment_status,
            'monthlyIncome': str(lead.monthly_income) if lead.monthly_income else '',
            'message': lead.message,
            'consent': str(lead.consent),
            'timestamp': lead.created_at.isoformat(),
            'lead_id': lead.id,
            'status': lead.status,
            'lead_type': lead.lead_type
        }
        
        # Send to Google Sheets
        response = requests.post(script_url, data=data_to_submit)
        
        if response.status_code == 200:
            lead.synced_with_google = True
            lead.save()
            messages.success(request, 'Lead synced with Google Sheets successfully!')
        else:
            messages.error(request, 'Failed to sync with Google Sheets')
            
    except Exception as e:
        messages.error(request, f'Error syncing with Google Sheets: {str(e)}')
    
    return redirect('crm:lead_detail', pk=lead.pk)


@login_required
def google_sheets_settings(request):
    """
    Google Sheets integration settings
    """
    # Get or create integration settings
    loan_integration, created = GoogleSheetsIntegration.objects.get_or_create(
        integration_type='loan',
        defaults={
            'name': 'Loan Form Integration',
            'script_url': 'https://script.google.com/macros/s/AKfycby-pJuT6CjTbSViGQd3qgOYzKQe-KPH0IQJ9UZCrujWCLXnnUeqWqz6sXkHOQ28tbiz-A/exec',
            'webhook_url': request.build_absolute_uri('/crm/webhook/loan-lead/')
        }
    )
    
    quote_integration, created = GoogleSheetsIntegration.objects.get_or_create(
        integration_type='quote',
        defaults={
            'name': 'Quote Form Integration',
            'script_url': 'https://script.google.com/macros/s/AKfycby-pJuT6CjTbSViGQd3qgOYzKQe-KPH0IQJ9UZCrujWCLXnnUeqWqz6sXkHOQ28tbiz-A/exec',
            'webhook_url': request.build_absolute_uri('/crm/webhook/quote-lead/')
        }
    )
    
    integrations = GoogleSheetsIntegration.objects.all()
    
    context = {
        'page_title': 'Google Sheets Settings',
        'integrations': integrations,
        'loan_integration': loan_integration,
        'quote_integration': quote_integration,
    }
    return render(request, 'crm/google_sheets_settings.html', context)


@login_required
def leads_debug(request):
    """
    Debug view for leads with raw data display
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    lead_type_filter = request.GET.get('lead_type', '')
    search_query = request.GET.get('search', '')
    
    # Build query
    leads = Lead.objects.all().order_by('-created_at')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if lead_type_filter:
        leads = leads.filter(lead_type=lead_type_filter)
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Statistics
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    contacted_leads = leads.filter(status='contacted').count()
    qualified_leads = leads.filter(status='qualified').count()
    
    # Lead type statistics
    loan_leads = leads.filter(lead_type='loan').count()
    quote_leads = leads.filter(lead_type='quote').count()
    
    context = {
        'page_title': 'Leads Debug',
        'leads': leads,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'loan_leads': loan_leads,
        'quote_leads': quote_leads,
        'status_choices': Lead.LEAD_STATUS_CHOICES,
        'lead_type_choices': Lead.LEAD_TYPE_CHOICES,
        'current_status': status_filter,
        'current_lead_type': lead_type_filter,
        'search_query': search_query,
    }
    return render(request, 'crm/leads_debug.html', context)


@login_required
def manual_import(request):
    """
    Manual data import from forms or CSV
    """
    from apps.crm.models import Lead
    import csv
    from io import TextIOWrapper
    
    if request.method == 'POST':
        import_type = request.POST.get('import_type', 'single')
        
        if import_type == 'csv' and 'csv_file' in request.FILES:
            # Handle CSV import
            csv_file = request.FILES['csv_file']
            csv_reader = csv.DictReader(TextIOWrapper(csv_file.file, encoding='utf-8'))
            
            imported_count = 0
            for row in csv_reader:
                # Check if lead already exists
                if not Lead.objects.filter(email=row.get('email', ''), name=row.get('name', '')).exists():
                    Lead.objects.create(
                        name=row.get('name', ''),
                        email=row.get('email', ''),
                        phone=row.get('phone', ''),
                        lead_type=row.get('lead_type', 'general'),
                        loan_type=row.get('loan_type', ''),
                        loan_amount=float(row.get('loan_amount', 0)) if row.get('loan_amount') else None,
                        employment_status=row.get('employment_status', ''),
                        monthly_income=float(row.get('monthly_income', 0)) if row.get('monthly_income') else None,
                        message=row.get('message', ''),
                        consent=row.get('consent', 'False').lower() == 'true',
                        source='manual_import',
                        synced_with_google=True
                    )
                    imported_count += 1
            
            messages.success(request, f'Successfully imported {imported_count} leads from CSV!')
            
        else:
            # Handle single lead import
            Lead.objects.create(
                name=request.POST.get('name', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                lead_type=request.POST.get('lead_type', 'general'),
                loan_type=request.POST.get('loan_type', ''),
                loan_amount=float(request.POST.get('loan_amount', 0)) if request.POST.get('loan_amount') else None,
                employment_status=request.POST.get('employment_status', ''),
                monthly_income=float(request.POST.get('monthly_income', 0)) if request.POST.get('monthly_income') else None,
                message=request.POST.get('message', ''),
                consent=request.POST.get('consent', 'False') == 'on',
                source='manual_import',
                synced_with_google=True
            )
            
            messages.success(request, 'Lead imported successfully!')
        
        return redirect('crm:manual_import')
    
    # Get current statistics
    total_leads = Lead.objects.count()
    loan_leads = Lead.objects.filter(lead_type='loan').count()
    quote_leads = Lead.objects.filter(lead_type='quote').count()
    synced_leads = Lead.objects.filter(synced_with_google=True).count()
    
    context = {
        'page_title': 'Manual Data Import',
        'total_leads': total_leads,
        'loan_leads': loan_leads,
        'quote_leads': quote_leads,
        'synced_leads': synced_leads,
    }
    return render(request, 'crm/manual_import.html', context)


@login_required
def debug_import(request):
    """
    Debug import interface to test Google Sheets data import
    """
    if request.method == 'POST':
        import_type = request.POST.get('type', 'loan')
        
        try:
            if import_type == 'loan':
                # Create loan lead
                name = request.POST.get('name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                loan_type = request.POST.get('loan_type', '').strip()
                loan_amount = request.POST.get('loan_amount', '').strip()
                message = request.POST.get('message', '').strip()
                
                # Validate required fields
                if not name or not email:
                    messages.error(request, 'Name and Email are required fields!')
                    return redirect('crm:debug_import')
                
                # Create loan lead
                lead = Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone if phone else '',
                    lead_type='loan',
                    loan_type=loan_type if loan_type else '',
                    loan_amount=float(loan_amount) if loan_amount and loan_amount.replace('.', '').isdigit() else None,
                    message=message if message else '',
                    source='google_sheets',
                    synced_with_google=True,
                    status='new'
                )
                messages.success(request, f'✅ DEBUG: Loan lead "{name}" created successfully! ID: {lead.id}')
                
            elif import_type == 'quote':
                # Create quote lead
                name = request.POST.get('name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                message = request.POST.get('message', '').strip()
                
                # Validate required fields
                if not name or not email:
                    messages.error(request, 'Name and Email are required fields!')
                    return redirect('crm:debug_import')
                
                # Create quote lead
                lead = Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone if phone else '',
                    lead_type='quote',
                    message=message if message else '',
                    source='google_sheets',
                    synced_with_google=True,
                    status='new'
                )
                messages.success(request, f'✅ DEBUG: Quote lead "{name}" created successfully! ID: {lead.id}')
            
        except Exception as e:
            messages.error(request, f'❌ DEBUG ERROR: {str(e)}')
            return redirect('crm:debug_import')
        
        return redirect('crm:debug_import')
    
    # Get statistics
    google_sheets_leads = Lead.objects.filter(source='google_sheets').count()
    loan_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='loan').count()
    quote_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='quote').count()
    
    context = {
        'page_title': 'Debug Import',
        'google_sheets_leads': google_sheets_leads,
        'loan_google_sheets_leads': loan_google_sheets_leads,
        'quote_google_sheets_leads': quote_google_sheets_leads,
    }
    return render(request, 'crm/debug_import.html', context)


@login_required
def simple_import(request):
    """
    Simple import interface for Google Sheets data
    """
    if request.method == 'POST':
        import_type = request.POST.get('type', 'loan')
        
        try:
            if import_type == 'loan':
                # Create loan lead
                name = request.POST.get('name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                loan_type = request.POST.get('loan_type', '').strip()
                loan_amount = request.POST.get('loan_amount', '').strip()
                message = request.POST.get('message', '').strip()
                
                # Validate required fields
                if not name or not email:
                    messages.error(request, 'Name and Email are required fields!')
                    return redirect('crm:simple_import')
                
                # Create loan lead
                Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone if phone else '',
                    lead_type='loan',
                    loan_type=loan_type if loan_type else '',
                    loan_amount=float(loan_amount) if loan_amount and loan_amount.replace('.', '').isdigit() else None,
                    message=message if message else '',
                    source='google_sheets',
                    synced_with_google=True,
                    status='new'
                )
                messages.success(request, f'Loan lead "{name}" added successfully!')
                
            elif import_type == 'quote':
                # Create quote lead
                name = request.POST.get('name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                message = request.POST.get('message', '').strip()
                
                # Validate required fields
                if not name or not email:
                    messages.error(request, 'Name and Email are required fields!')
                    return redirect('crm:simple_import')
                
                # Create quote lead
                Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone if phone else '',
                    lead_type='quote',
                    message=message if message else '',
                    source='google_sheets',
                    synced_with_google=True,
                    status='new'
                )
                messages.success(request, f'Quote lead "{name}" added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error creating lead: {str(e)}')
            return redirect('crm:simple_import')
        
        return redirect('crm:simple_import')
    
    # Get statistics
    google_sheets_leads = Lead.objects.filter(source='google_sheets').count()
    loan_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='loan').count()
    quote_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='quote').count()
    
    context = {
        'page_title': 'Simple Google Sheets Import',
        'google_sheets_leads': google_sheets_leads,
        'loan_google_sheets_leads': loan_google_sheets_leads,
        'quote_google_sheets_leads': quote_google_sheets_leads,
    }
    return render(request, 'crm/simple_import.html', context)


@login_required
def direct_google_sheets_import(request):
    """
    Direct import from Google Sheets with manual data entry
    """
    if request.method == 'POST':
        import_type = request.POST.get('import_type', 'loan')
        
        if import_type == 'loan':
            # Handle loan data import
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            loan_type = request.POST.get('loan_type', '')
            loan_amount = request.POST.get('loan_amount', '')
            employment = request.POST.get('employment', '')
            monthly_income = request.POST.get('monthly_income', '')
            message = request.POST.get('message', '')
            
            # Create loan lead
            lead = Lead.objects.create(
                name=name,
                email=email,
                phone=phone,
                lead_type='loan',
                loan_type=loan_type,
                loan_amount=float(loan_amount) if loan_amount else None,
                employment_status=employment,
                monthly_income=float(monthly_income) if monthly_income else None,
                message=message,
                source='google_sheets',
                synced_with_google=True,
                status='new'
            )
            
            messages.success(request, f'Loan lead "{name}" imported successfully from Google Sheets!')
            
        elif import_type == 'quote':
            # Handle quote data import
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            message = request.POST.get('message', '')
            
            # Create quote lead
            lead = Lead.objects.create(
                name=name,
                email=email,
                phone=phone,
                lead_type='quote',
                message=message,
                source='google_sheets',
                synced_with_google=True,
                status='new'
            )
            
            messages.success(request, f'Quote lead "{name}" imported successfully from Google Sheets!')
        
        return redirect('crm:direct_google_sheets_import')
    
    # Get current statistics
    total_google_sheets_leads = Lead.objects.filter(source='google_sheets').count()
    loan_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='loan').count()
    quote_google_sheets_leads = Lead.objects.filter(source='google_sheets', lead_type='quote').count()
    
    context = {
        'page_title': 'Import Google Sheets Data',
        'total_google_sheets_leads': total_google_sheets_leads,
        'loan_google_sheets_leads': loan_google_sheets_leads,
        'quote_google_sheets_leads': quote_google_sheets_leads,
    }
    return render(request, 'crm/direct_google_sheets_import.html', context)


@login_required
def sync_google_sheets_data(request):
    """
    Sync existing data from Google Sheets to CRM
    """
    try:
        # Use the real-time sync function
        from .realtime_sync import sync_google_sheets_to_crm
        result = sync_google_sheets_to_crm()
        
        if result:
            # Get updated counts
            total_leads = Lead.objects.count()
            loan_leads = Lead.objects.filter(lead_type='loan').count()
            quote_leads = Lead.objects.filter(lead_type='quote').count()
            
            messages.success(request, f'Successfully synced Google Sheets data! Total: {total_leads}, Loan: {loan_leads}, Quote: {quote_leads}')
        else:
            messages.error(request, 'Failed to sync Google Sheets data')
            
    except Exception as e:
        messages.error(request, f'Error syncing Google Sheets data: {str(e)}')
    
    return redirect('crm:leads')


@login_required
def debug_leads(request):
    """
    Debug view to check leads data
    """
    from apps.crm.models import Lead
    
    leads = Lead.objects.all().order_by('-created_at')
    
    debug_info = {
        'total_leads': leads.count(),
        'loan_leads': leads.filter(lead_type='loan').count(),
        'quote_leads': leads.filter(lead_type='quote').count(),
        'general_leads': leads.filter(lead_type='general').count(),
        'synced_leads': leads.filter(synced_with_google=True).count(),
        'leads_data': []
    }
    
    for lead in leads:
        debug_info['leads_data'].append({
            'id': lead.id,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'lead_type': lead.lead_type,
            'lead_type_display': lead.get_lead_type_display(),
            'status': lead.status,
            'status_display': lead.get_status_display(),
            'loan_type': lead.loan_type,
            'loan_amount': lead.loan_amount,
            'synced_with_google': lead.synced_with_google,
            'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse(debug_info)


@login_required
def webhook_test(request):
    """
    Test page for webhook integration
    """
    context = {
        'page_title': 'Webhook Integration Test'
    }
    return render(request, 'crm/webhook_test.html', context)


@login_required
def customers(request):
    """
    Customers management view
    """
    context = {
        'page_title': 'Customers'
    }
    return render(request, 'crm/customers.html', context)


@login_required
def contacts(request):
    """
    Contacts management view
    """
    context = {
        'page_title': 'Contacts'
    }
    return render(request, 'crm/contacts.html', context)
