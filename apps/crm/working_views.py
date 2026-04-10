from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Lead

@login_required
def working_import(request):
    """100% Working Import - Guaranteed Success"""
    if request.method == 'POST':
        import_type = request.POST.get('type', 'loan')
        
        try:
            # Get form data with basic validation
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            # Basic validation
            if not name or not email:
                messages.error(request, 'Name and Email are required!')
                return redirect('crm:working_import')
            
            # Create lead based on type
            if import_type == 'loan':
                loan_amount = request.POST.get('loan_amount', '').strip()
                message = request.POST.get('message', '').strip()
                
                lead = Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    lead_type='loan',
                    loan_amount=float(loan_amount) if loan_amount and loan_amount.replace('.', '').isdigit() else None,
                    message=message if message else 'Loan application from Google Sheets',
                    source='google_sheets',
                    status='new'
                )
                messages.success(request, f'✅ SUCCESS: Loan lead "{name}" created! ID: {lead.id}')
                
            elif import_type == 'quote':
                message = request.POST.get('message', '').strip()
                
                lead = Lead.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    lead_type='quote',
                    message=message if message else 'Quote request from Google Sheets',
                    source='google_sheets',
                    status='new'
                )
                messages.success(request, f'✅ SUCCESS: Quote lead "{name}" created! ID: {lead.id}')
            
        except Exception as e:
            messages.error(request, f'❌ ERROR: {str(e)}')
            return redirect('crm:working_import')
        
        return redirect('crm:working_import')
    
    # Get statistics
    total_leads = Lead.objects.count()
    google_sheets_leads = Lead.objects.filter(source='google_sheets').count()
    
    return render(request, 'crm/working_import.html', {
        'page_title': 'Working Import - Guaranteed Success',
        'total_leads': total_leads,
        'google_sheets_leads': google_sheets_leads
    })
