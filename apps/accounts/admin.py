from django.contrib import admin

from django.db import models

from .models import (

    Employee, OnboardingTask, Document, ManagerRequest, Team,

    ExcelBatch, ExcelBatchRow, Lead, LoginStatistics, UserActivityLog,

    LeadActivityLog, Attendance, Break, Violation, Leave, LeaveApproval,

    Ticket, TicketComment, MISReport

)





@admin.register(Employee)

class EmployeeAdmin(admin.ModelAdmin):

    list_display = ('employee_id', 'full_name', 'email', 'role', 'manager', 'team_leader', 'employment_status', 'start_date')

    list_filter = ('role', 'employment_status', 'employee_type', 'department', 'manager', 'team_leader')

    search_fields = ('first_name', 'last_name', 'email', 'employee_id')

    readonly_fields = ('employee_id', 'created_at', 'updated_at')

    ordering = ('-created_at',)

    

    fieldsets = (

        ('Basic Information', {

            'fields': ('user', 'employee_id', 'first_name', 'last_name', 'email', 'phone')

        }),

        ('Role & Hierarchy', {

            'fields': ('role', 'manager', 'team_leader', 'employment_status')

        }),

        ('Job Details', {

            'fields': ('employee_type', 'department', 'position')

        }),

        ('Onboarding Details', {

            'fields': ('hire_date', 'start_date', 'probation_end_date')

        }),

        ('Compensation', {

            'fields': ('salary', 'bonus_percentage')

        }),

        ('Personal Information', {

            'fields': ('date_of_birth', 'address', 'city', 'state', 'postal_code', 'country')

        }),

        ('Emergency Contact', {

            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')

        }),

        ('System Information', {

            'fields': ('created_at', 'updated_at', 'created_by'),

            'classes': ('collapse',)

        }),

    )





@admin.register(Attendance)

class AttendanceAdmin(admin.ModelAdmin):

    list_display = ('employee', 'date', 'start_time', 'end_time', 'status', 'total_hours', 'overtime_hours', 'is_active')

    list_filter = ('status', 'date', 'is_active', 'employee__role')

    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-date', '-created_at')





@admin.register(Break)

class BreakAdmin(admin.ModelAdmin):

    list_display = ('attendance', 'break_type', 'start_time', 'end_time', 'duration_hours', 'is_auto_break')

    list_filter = ('break_type', 'is_auto_break', 'start_time', 'end_time')

    search_fields = ('attendance__employee__first_name', 'attendance__employee__last_name')

    readonly_fields = ('duration_hours', 'created_at', 'updated_at')

    ordering = ('-start_time',)





@admin.register(Violation)

class ViolationAdmin(admin.ModelAdmin):

    list_display = ('employee', 'attendance', 'violation_type', 'violation_time', 'resolved', 'resolved_by')

    list_filter = ('violation_type', 'resolved', 'violation_time', 'employee__role')

    search_fields = ('employee__first_name', 'employee__last_name', 'description')

    readonly_fields = ('resolved_at', 'created_at', 'updated_at')

    ordering = ('-violation_time',)





@admin.register(LoginStatistics)

class LoginStatisticsAdmin(admin.ModelAdmin):

    list_display = ('manager', 'team_leader', 'date', 'file_count', 'login_count', 'total_count', 'updated_by')

    list_filter = ('date', 'manager', 'team_leader', 'updated_by')

    search_fields = ('manager__full_name', 'team_leader__full_name')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-date',)





@admin.register(UserActivityLog)

class UserActivityLogAdmin(admin.ModelAdmin):

    list_display = ('user', 'created_at', 'ip_address')

    list_filter = ('created_at',)

    search_fields = ('user__username',)

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-created_at',)





@admin.register(LeadActivityLog)

class LeadActivityLogAdmin(admin.ModelAdmin):

    list_display = ('lead', 'user', 'action_type', 'created_at', 'ip_address')

    list_filter = ('action_type', 'created_at')

    search_fields = ('lead__id', 'user__username', 'description')

    readonly_fields = ('created_at',)

    ordering = ('-created_at',)





@admin.register(Lead)

class LeadAdmin(admin.ModelAdmin):

    list_display = ('id', 'status', 'source', 'assigned_to', 'created_at')

    list_filter = ('status', 'source', 'assigned_to', 'created_at')

    search_fields = ('id',)

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-created_at',)





@admin.register(ExcelBatch)

class ExcelBatchAdmin(admin.ModelAdmin):

    list_display = ('id', 'total_rows', 'processed_rows', 'status', 'created_at')

    list_filter = ('status', 'created_at')

    search_fields = ('id',)

    readonly_fields = ('created_at',)

    ordering = ('-created_at',)





@admin.register(ExcelBatchRow)

class ExcelBatchRowAdmin(admin.ModelAdmin):

    list_display = ('batch', 'row_number', 'status', 'error_message')

    list_filter = ('status', 'batch')

    search_fields = ('error_message',)

    readonly_fields = ()

    ordering = ('batch', 'row_number')





@admin.register(OnboardingTask)

class OnboardingTaskAdmin(admin.ModelAdmin):

    list_display = ('title', 'employee', 'status', 'due_date')

    list_filter = ('status', 'due_date')

    search_fields = ('title', 'employee__first_name', 'employee__last_name')

    ordering = ('-created_at',)





@admin.register(Document)

class DocumentAdmin(admin.ModelAdmin):

    list_display = ('title', 'employee', 'document_type', 'uploaded_at', 'uploaded_by')

    list_filter = ('document_type', 'uploaded_at')

    search_fields = ('title', 'employee__first_name', 'employee__last_name')

    readonly_fields = ('uploaded_at',)

    ordering = ('-uploaded_at',)





@admin.register(ManagerRequest)

class ManagerRequestAdmin(admin.ModelAdmin):

    list_display = ('employee', 'status', 'created_at', 'approved_by')

    list_filter = ('status', 'created_at')

    search_fields = ('employee__first_name', 'employee__last_name', 'reason')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-created_at',)





@admin.register(Team)

class TeamAdmin(admin.ModelAdmin):

    list_display = ('name', 'team_leader', 'department', 'is_active', 'created_at')

    list_filter = ('department', 'is_active', 'created_at')

    search_fields = ('name', 'team_leader__first_name', 'team_leader__last_name')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-created_at',)





@admin.register(Leave)

class LeaveAdmin(admin.ModelAdmin):

    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by', 'created_at')

    list_filter = ('leave_type', 'status', 'created_at', 'start_date', 'end_date')

    search_fields = ('employee__first_name', 'employee__last_name', 'reason')

    readonly_fields = ('created_at', 'updated_at', 'approved_at')

    ordering = ('-created_at',)



    def get_queryset(self, request):

        qs = super().get_queryset(request)

        # Superadmin and admin can see all leaves

        if request.user.employee.is_superadmin or request.user.employee.is_admin:

            return qs

        # Managers can see leaves of their direct reports and team leaders

        elif request.user.employee.is_manager:

            return qs.filter(

                models.Q(employee__reports_to=request.user.employee) |

                models.Q(employee__team_leader__reports_to=request.user.employee)

            )

        # Team leaders can see leaves of their team members

        elif request.user.employee.is_team_leader:

            return qs.filter(employee__team_leader=request.user.employee)

        # Employees can only see their own leaves

        else:

            return qs.filter(employee=request.user.employee)





@admin.register(LeaveApproval)

class LeaveApprovalAdmin(admin.ModelAdmin):

    list_display = ('leave', 'approver', 'status', 'approved_at', 'created_at')

    list_filter = ('status', 'approved_at', 'created_at')

    search_fields = ('leave__employee__first_name', 'leave__employee__last_name', 'comments')

    readonly_fields = ('created_at', 'updated_at')

    ordering = ('-created_at',)



    def get_queryset(self, request):

        qs = super().get_queryset(request)

        # Superadmin and admin can see all approvals

        if request.user.employee.is_superadmin or request.user.employee.is_admin:

            return qs

        # Managers can see approvals for leaves of their direct reports and team leaders

        elif request.user.employee.is_manager:

            return qs.filter(

                models.Q(leave__employee__reports_to=request.user.employee) |

                models.Q(leave__employee__team_leader__reports_to=request.user.employee)

            )

        # Team leaders can see approvals for leaves of their team members

        elif request.user.employee.is_team_leader:

            return qs.filter(leave__employee__team_leader=request.user.employee)

        # Employees can only see approvals for their own leaves

        else:

            return qs.filter(leave__employee=request.user.employee)


class TicketCommentInline(admin.TabularInline):
    """Inline comments for tickets in admin"""
    model = TicketComment
    extra = 1
    readonly_fields = ('created_at', 'is_admin_reply')
    fields = ('author', 'message', 'created_at', 'is_admin_reply')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin configuration for Support Tickets"""
    list_display = ('ticket_number', 'subject', 'employee', 'category', 'priority', 'status', 'created_at')
    list_filter = ('status', 'category', 'priority', 'created_at')
    search_fields = ('ticket_id', 'subject', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('employee', 'subject', 'category', 'priority', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Attachments', {
            'fields': ('attachment',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TicketCommentInline]
    
    def ticket_number(self, obj):
        return obj.ticket_number
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see tickets from their department
        if hasattr(request.user, 'employee'):
            return qs.filter(employee__department=request.user.employee.department)
        return qs.none()


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """Admin configuration for Ticket Comments"""
    list_display = ('ticket', 'author', 'is_admin_reply', 'created_at')
    list_filter = ('is_admin_reply', 'created_at')
    search_fields = ('message', 'author__first_name', 'author__last_name')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see comments from their department
        if hasattr(request.user, 'employee'):
            return qs.filter(ticket__employee__department=request.user.employee.department)
        return qs.none()


@admin.register(MISReport)
class MISReportAdmin(admin.ModelAdmin):
    list_display = [
        'login_date', 'app_id', 'customer_name', 'mobile_number', 
        'team_leader', 'manager', 'product', 'login_amount', 
        'disbursed_amount', 'status'
    ]
    list_filter = [
        'login_date', 'team_leader', 'manager', 'status', 'product'
    ]
    search_fields = [
        'app_id', 'customer_name', 'mobile_number', 'pan_no', 'company_name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by'
    ]
    date_hierarchy = 'login_date'
    ordering = ['-login_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'login_date', 'app_id', 'customer_name', 'mobile_number',
                'applicant_type', 'dob', 'pan_no', 'salary', 'company_name'
            )
        }),
        ('Loan Details', {
            'fields': (
                'login_amount', 'disbursed_amount', 'product', 'tanure', 'bank', 'location'
            )
        }),
        ('Status & Assignment', {
            'fields': (
                'status', 'current_status', 'team_leader', 'manager', 'aro'
            )
        }),
        ('Banker Details', {
            'fields': (
                'banker_name', 'banker_no'
            )
        }),
        ('System Information', {
            'fields': (
                'created_at', 'updated_at', 'created_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see MIS reports based on their role
        if hasattr(request.user, 'employee'):
            employee = request.user.employee
            if employee.is_admin or employee.is_superadmin:
                return qs
            elif employee.is_manager:
                return qs.filter(team_leader__employee__reports_to=employee)
            elif employee.is_team_leader:
                return qs.filter(team_leader=request.user)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
