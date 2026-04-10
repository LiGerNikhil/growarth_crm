from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse_lazy
from .models import Ticket, TicketComment
from .support_forms import TicketForm, TicketCommentForm


class IsAdminOrHRMixin(UserPassesTestMixin):
    """Mixin to allow only Admin or HR users"""
    def test_func(self):
        return (self.request.user.employee.is_admin or 
                self.request.user.employee.is_hr or 
                self.request.user.employee.is_superadmin)


class TicketListView(LoginRequiredMixin, ListView):
    """List view for support tickets"""
    model = Ticket
    template_name = 'accounts/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user.employee
        
        # Base queryset based on user permissions
        if user.is_admin or user.is_hr or user.is_superadmin:
            queryset = Ticket.objects.select_related('employee').prefetch_related('comments')
        elif user.is_manager:
            # Managers can see tickets from:
            # 1. Direct reports (employees who report to manager)
            # 2. Direct team leaders (team leaders who report to manager)
            # 3. Employees whose team leader reports to manager
            # 4. Manager's own tickets
            queryset = Ticket.objects.filter(
                Q(employee__reports_to=user) |                    # Direct reports
                Q(employee__team_leader=user) |                   # Direct team leaders
                Q(employee__team_leader__reports_to=user) |        # Employees whose team leader reports to manager
                Q(employee=user)                                   # Manager's own tickets
            ).select_related('employee').prefetch_related('comments')
        else:
            queryset = Ticket.objects.filter(employee=user).select_related('employee').prefetch_related('comments')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) | 
                Q(description__icontains=search) |
                Q(employee__full_name__icontains=search) |
                Q(ticket_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Support Tickets'
        
        # Add counts for dashboard
        user = self.request.user.employee
        if user.is_admin or user.is_hr or user.is_superadmin:
            queryset = Ticket.objects.all()
        elif user.is_manager:
            # Managers can see tickets from:
            # 1. Direct reports (employees who report to manager)
            # 2. Direct team leaders (team leaders who report to manager)
            # 3. Employees whose team leader reports to manager
            # 4. Manager's own tickets
            queryset = Ticket.objects.filter(
                Q(employee__reports_to=user) |                    # Direct reports
                Q(employee__team_leader=user) |                   # Direct team leaders
                Q(employee__team_leader__reports_to=user) |        # Employees whose team leader reports to manager
                Q(employee=user)                                   # Manager's own tickets
            )
        else:
            queryset = Ticket.objects.filter(employee=user)
            
        context['total_tickets'] = queryset.count()
        context['open_tickets'] = queryset.filter(status='open').count()
        context['in_progress_tickets'] = queryset.filter(status='in_progress').count()
        context['resolved_tickets'] = queryset.filter(status='resolved').count()
        
        # Debug: Check if tickets have IDs
        if context['tickets']:
            for ticket in context['tickets']:
                print(f"Ticket ID: {ticket.ticket_id}, Number: {ticket.ticket_number}")
        
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a single ticket"""
    model = Ticket
    template_name = 'accounts/ticket_detail.html'
    context_object_name = 'ticket'
    
    def get_object(self):
        ticket = super().get_object()
        # Debug: Print ticket info
        print(f"TicketDetailView: ticket_id={ticket.ticket_id}, employee={ticket.employee.full_name if ticket.employee else 'None'}")
        return ticket
    
    def get_queryset(self):
        user = self.request.user.employee
        
        # Base queryset based on user permissions
        if user.is_admin or user.is_hr or user.is_superadmin:
            return Ticket.objects.select_related('employee').prefetch_related('comments__author')
        elif user.is_manager:
            # Managers can see tickets from:
            # 1. Direct reports (employees who report to manager)
            # 2. Direct team leaders (team leaders who report to manager)
            # 3. Employees whose team leader reports to manager
            # 4. Manager's own tickets
            return Ticket.objects.filter(
                Q(employee__reports_to=user) |                    # Direct reports
                Q(employee__team_leader=user) |                   # Direct team leaders
                Q(employee__team_leader__reports_to=user) |        # Employees whose team leader reports to manager
                Q(employee=user)                                   # Manager's own tickets
            ).select_related('employee').prefetch_related('comments__author')
        else:
            return Ticket.objects.filter(employee=user).select_related('employee').prefetch_related('comments__author')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Ticket {self.object.ticket_number}'
        context['comment_form'] = TicketCommentForm()
        
        # Check if user can comment (employees can comment on their own tickets, managers on team tickets)
        user = self.request.user.employee
        can_comment = (
            self.object.employee == user or 
            user.is_admin or user.is_hr or user.is_superadmin
        )
        
        # Managers can comment on tickets from their team
        if user.is_manager:
            can_comment = can_comment or (
                self.object.employee.reports_to == user or                    # Direct reports
                self.object.employee.team_leader == user or                   # Direct team leaders
                (self.object.employee.team_leader and self.object.employee.team_leader.reports_to == user)  # Employees whose team leader reports to manager
            )
        
        # Check if user can update status
        can_update_status = (
            user.is_admin or user.is_hr or user.is_superadmin
        )
        
        # Managers can update status of team tickets
        if user.is_manager:
            can_update_status = can_update_status or (
                self.object.employee.reports_to == user or                    # Direct reports
                self.object.employee.team_leader == user or                   # Direct team leaders
                (self.object.employee.team_leader and self.object.employee.team_leader.reports_to == user)  # Employees whose team leader reports to manager
            )
        
        context['can_comment'] = can_comment
        context['can_update_status'] = can_update_status
        
        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    """Create a new support ticket"""
    model = Ticket
    form_class = TicketForm
    template_name = 'accounts/ticket_create.html'
    success_url = reverse_lazy('accounts:ticket_list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        messages.success(self.request, f'Support ticket {form.instance.ticket_number} created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Support Ticket'
        return context


@login_required
@require_POST
def add_ticket_comment(request, ticket_id):
    """Add a comment to a ticket"""
    print(f"add_ticket_comment called with ticket_id: {ticket_id}")
    print(f"POST data: {dict(request.POST)}")
    print(f"User: {request.user.employee.full_name if request.user.employee else 'Anonymous'}")
    
    try:
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        print(f"Found ticket: {ticket.ticket_number}")
    except Ticket.DoesNotExist:
        print("Ticket not found")
        messages.error(request, 'Ticket not found')
        return redirect('accounts:ticket_list')
    
    user = request.user.employee
    print(f"Request user: {user.full_name}")
    print(f"Ticket employee: {ticket.employee.full_name if ticket.employee else 'None'}")
    
    # Check permissions
    if ticket.employee != user and not (user.is_admin or user.is_hr or user.is_superadmin):
        print("Permission denied")
        messages.error(request, 'Permission denied')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)
    
    form = TicketCommentForm(request.POST)
    if form.is_valid():
        print("Form is valid")
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = user
        comment.is_admin_reply = user.is_admin or user.is_hr or user.is_superadmin
        comment.save()
        print(f"Comment saved: {comment}")
        
        # Update ticket status if admin replies
        if comment.is_admin_reply and ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save()
            print("Ticket status updated to 'in_progress'")
        
        messages.success(request, 'Comment added successfully!')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)
    else:
        print("Form is invalid")
        messages.error(request, 'Invalid comment')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)


@login_required
@require_POST
def update_ticket_status(request, ticket_id):
    """Update ticket status"""
    print(f"update_ticket_status called with ticket_id: {ticket_id}")
    print(f"POST data: {dict(request.POST)}")
    print(f"User: {request.user.employee.full_name if request.user.employee else 'Anonymous'}")
    
    try:
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        print(f"Found ticket: {ticket.ticket_number}")
    except Ticket.DoesNotExist:
        print("Ticket not found")
        messages.error(request, 'Ticket not found')
        return redirect('accounts:ticket_list')
    
    user = request.user.employee
    print(f"Request user: {user.full_name}")
    
    # Check permissions
    can_update = (
        user.is_admin or user.is_hr or user.is_superadmin
    )
    
    # Managers can update status of team tickets
    if user.is_manager:
        can_update = can_update or (
            ticket.employee.reports_to == user or                    # Direct reports
            ticket.employee.team_leader == user or                   # Direct team leaders
            (ticket.employee.team_leader and ticket.employee.team_leader.reports_to == user)  # Employees whose team leader reports to manager
        )
    
    if not can_update:
        print("Permission denied")
        messages.error(request, 'Permission denied')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)
    
    new_status = request.POST.get('status')
    print(f"New status: {new_status}")
    
    if new_status in ['open', 'in_progress', 'resolved', 'closed']:
        old_status = ticket.status
        ticket.status = new_status
        if new_status in ['resolved', 'closed']:
            ticket.resolved_at = timezone.now()
        ticket.save()
        print(f"Status updated from {old_status} to {new_status}")
        
        messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)
    else:
        print("Invalid status")
        messages.error(request, 'Invalid status')
        return redirect('accounts:ticket_detail', pk=ticket.ticket_id)


def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    status_classes = {
        'open': 'bg-danger',
        'in_progress': 'bg-warning',
        'resolved': 'bg-success',
        'closed': 'bg-secondary'
    }
    return status_classes.get(status, 'bg-secondary')
