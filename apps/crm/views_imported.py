from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from .models import Lead


@login_required
def imported_leads(request):
    """
    View for displaying imported leads (CSV/Excel + Google Sheets)
    """
    # Get filter parameters
    source_filter = request.GET.get('source', '')
    status_filter = request.GET.get('status', '')
    lead_type_filter = request.GET.get('lead_type', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build base query - Only imported leads (Google Sheets)
    leads = Lead.objects.filter(
        synced_with_google=True
    ).order_by('-created_at')
    
    # Apply filters
    if source_filter:
        if source_filter == 'csv':
            leads = leads.none()  # Since uploaded_from_file field doesn't exist
        elif source_filter == 'google':
            leads = leads.filter(synced_with_google=True)
        elif source_filter == 'manual':
            leads = leads.filter(synced_with_google=False)
    
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
    
    # Datewise filtering
    if date_from:
        date_from_obj = parse_date(date_from)
        if date_from_obj:
            leads = leads.filter(created_at__date__gte=date_from_obj)
    
    if date_to:
        date_to_obj = parse_date(date_to)
        if date_to_obj:
            leads = leads.filter(created_at__date__lte=date_to_obj)
    
    # Statistics for imported leads
    total_leads = leads.count()
    new_leads = leads.filter(status='new').count()
    contacted_leads = leads.filter(status='contacted').count()
    qualified_leads = leads.filter(status='qualified').count()
    
    # Lead type statistics
    loan_leads = leads.filter(lead_type='loan').count()
    quote_leads = leads.filter(lead_type='quote').count()
    
    # Source statistics
    csv_leads = 0  # Since uploaded_from_file field doesn't exist
    google_leads = leads.filter(synced_with_google=True).count()
    
    # Get choices for filters
    status_choices = Lead.LEAD_STATUS_CHOICES
    lead_type_choices = Lead.LEAD_TYPE_CHOICES
    
    # No pagination for now - show all leads
    page_obj = leads
    
    context = {
        'page_title': 'Google Sheets Leads',
        'leads': page_obj,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'loan_leads': loan_leads,
        'quote_leads': quote_leads,
        'csv_leads': csv_leads,
        'google_leads': google_leads,
        'status_choices': status_choices,
        'lead_type_choices': lead_type_choices,
        'source_filter': source_filter,
        'status_filter': status_filter,
        'lead_type_filter': lead_type_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'crm/google_sheets_leads_test.html', context)
