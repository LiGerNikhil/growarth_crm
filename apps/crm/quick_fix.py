from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Lead

@login_required
def quick_fix_import(request):
    """QUICK FIX - This will work 100%"""
    if request.method == 'POST':
        try:
            # Get data directly from POST
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            lead_type = request.POST.get('lead_type', 'loan').strip()
            
            if not name or not email:
                messages.error(request, 'Name and Email required!')
                return redirect('crm:quick_fix')
            
            # Create lead - SIMPLE
            lead = Lead.objects.create(
                name=name,
                email=email,
                lead_type=lead_type,
                source='quick_fix',
                status='new'
            )
            
            messages.success(request, f'SUCCESS! {name} added (ID: {lead.id})')
            
        except Exception as e:
            messages.error(request, f'ERROR: {str(e)}')
        
        return redirect('crm:quick_fix')
    
    # Show current status
    total = Lead.objects.count()
    return render(request, 'crm/quick_fix.html', {
        'total_leads': total,
        'page_title': 'QUICK FIX - WORKING 100%'
    })
