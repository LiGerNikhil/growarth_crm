from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import staff_views
from . import document_views
from . import attendance_views
from . import support_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('logout-success/', views.logout_success, name='logout_success'),
    
    # Profile and Settings URLs
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='account_settings'),
    
    # Employee Management URLs (Unified)
    path('', staff_views.StaffManagementView.as_view(), name='staff_management'),
    path('create/', staff_views.staff_create_view, name='staff_create'),
    path('<int:pk>/', staff_views.staff_detail_view, name='staff_detail'),
    path('<int:pk>/update/', staff_views.staff_update_view, name='staff_update'),
    path('<int:pk>/toggle-status/', staff_views.toggle_employee_status, name='toggle_employee_status'),
    path('bulk-assign/', staff_views.bulk_assign_employees, name='bulk_assign'),
    path('hierarchy/', staff_views.staff_hierarchy_view, name='staff_hierarchy'),
    
    # Organization View for Employees
    path('organization/', views.employee_organization_view, name='employee_organization'),
    
    # Employee Detail View
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    
    # Lead Forwarding System
    path('lead-forward-dashboard/', views.lead_forward_dashboard, name='lead_forward_dashboard'),
    path('forward-lead/<int:lead_id>/', views.forward_lead, name='forward_lead'),
    path('my-forwarded-leads/', views.my_forwarded_leads, name='my_forwarded_leads'),
    path('update-forward-status/<int:forward_id>/', views.update_forward_status, name='update_forward_status'),
    path('forward-activity-log/<int:forward_id>/', views.forward_activity_log, name='forward_activity_log'),
    
    # Manager Management URLs
    path('managers/', views.manager_list, name='manager_list'),
    
    # Team Management URLs
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('teams/<int:pk>/update/', views.update_team, name='update_team'),
    path('employees/<int:employee_pk>/assign-team/', views.assign_employee_to_team, name='assign_employee_to_team'),
    path('employee-assignment/', views.employee_assignment, name='employee_assignment'),
    path('bulk-assign/', views.bulk_assign_employees, name='bulk_assign_employees'),
    path('quick-assign/', views.quick_assign_to_team_leader, name='quick_assign_to_team_leader'),
    path('employees/<int:employee_pk>/remove-from-team/', views.remove_from_team, name='remove_from_team'),
    path('team-leaders/<int:team_leader_pk>/assign/', views.team_leader_assignment, name='team_leader_assignment'),
    path('my-team/', views.my_team, name='my_team'),
    
    # Phone Number Management
    path('phone-assignments/', staff_views.phone_assignment_list, name='phone_assignment_list'),
    path('phone-assignments/assign/<int:employee_id>/', staff_views.assign_phone_number, name='assign_phone_number'),
    path('phone-assignments/update/<int:phone_id>/', staff_views.update_phone_assignment, name='update_phone_assignment'),
    path('phone-assignments/delete/<int:phone_id>/', staff_views.delete_phone_assignment, name='delete_phone_assignment'),
    
    # Excel Upload and Batch Management
    path('excel-upload/', views.excel_upload, name='excel_upload'),
    path('excel-batches/', views.excel_batch_list, name='excel_batch_list'),
    path('excel-batches/<int:pk>/', views.excel_batch_detail, name='excel_batch_detail'),
    path('excel-batches/<int:pk>/delete/', views.delete_excel_batch, name='delete_excel_batch'),
    
    # Lead Management
    path('leads/filter/<str:status>/', views.leads_by_status, name='leads_by_status'),
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/assign/', views.assign_leads, name='assign_leads'),
    path('leads/unassign/', views.unassign_leads, name='unassign_leads'),
    path('leads/delete/', views.delete_leads, name='delete_leads'),
    path('my-leads/', views.my_leads, name='my_leads'),
    
    # Lead Management APIs
    path('api/leads-for-deletion/', views.api_leads_for_deletion, name='api_leads_for_deletion'),
    path('api/employee-leads/<int:employee_id>/', views.api_employee_leads, name='api_employee_leads'),
    
    # Onboarding Task URLs
    path('employees/<int:employee_pk>/onboarding/create/', views.create_onboarding_task, name='create_onboarding_task'),
    path('onboarding/<int:pk>/update/', views.update_onboarding_task, name='update_onboarding_task'),
    
    # Document Management URLs
    path('employees/<int:employee_pk>/documents/upload/', views.upload_document, name='upload_document'),
    
    # HR Dashboard
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    
    # Login Statistics Dashboard
    path('login-statistics/', views.login_statistics_dashboard, name='login_statistics_dashboard'),
    path('login-statistics/<str:manager_name>/', views.manager_details, name='manager_details'),
    path('login-statistics/<int:pk>/update/', views.update_login_statistics, name='update_login_statistics'),
    path('login-statistics/<int:pk>/delete/', views.delete_login_statistics, name='delete_login_statistics'),
    path('login-statistics/export/excel/', views.export_login_statistics_excel, name='export_login_statistics_excel'),
    
    # User Activity Logs
    path('user-activity-logs/', views.user_activity_logs, name='user_activity_logs'),
    
    # Employee Performance Dashboard
    path('employee-performance/', views.employee_performance_dashboard, name='employee_performance_dashboard'),
    
    # Attendance Management URLs
    path('attendance/start/', views.start_work, name='start_work'),
    path('attendance/end/', views.end_work, name='end_work'),
    path('attendance/break/start/<str:break_type>/', views.start_break, name='start_break'),
    path('attendance/break/end/', views.end_break, name='end_break'),
    path('attendance/employee/<int:employee_id>/', views.employee_attendance_stats, name='employee_attendance_stats'),
    path('attendance/stats/', views.employee_attendance_stats, name='my_attendance_stats'),
    
    # Employee Details API
    path('employee-details/<int:employee_id>/', views.employee_details_api, name='employee_details_api'),
    
    # Attendance Admin URLs
    path('attendance-admin/', views.attendance_admin, name='attendance_admin'),
    path('violation/<int:violation_id>/resolve/', views.resolve_violation, name='resolve_violation'),
    
    # Password Management URLs
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Leave Management URLs
    path('leave/apply/', views.apply_leave, name='apply_leave'),
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/my/', views.my_leaves, name='my_leaves'),
    path('leave/<int:pk>/', views.leave_details, name='leave_details'),
    path('leave/<int:pk>/approve/', views.approve_leave, name='approve_leave'),
    path('leave/<int:pk>/reject/', views.reject_leave, name='reject_leave'),

    # Phone Assignment URLs
    path('phone-assignments/', staff_views.phone_assignment_list, name='phone_assignment_list'),
    path('phone-assignments/assign/', staff_views.assign_phone_simple, name='assign_phone_simple'),
    path('phone-assignments/assign/<int:employee_id>/', staff_views.assign_phone_number, name='assign_phone_number'),
    path('phone-assignments/<int:phone_id>/update/', staff_views.update_phone_assignment, name='update_phone_assignment'),
    path('phone-assignments/<int:phone_id>/delete/', staff_views.delete_phone_assignment, name='delete_phone_assignment'),
    
    # Break Management URLs
    path('break-management/', staff_views.break_management_dashboard, name='break_management_dashboard'),
    path('my-break-status/', staff_views.my_break_status, name='my_break_status'),
    
    # Document Management URLs
    path('documents/', document_views.DocumentEmployeeListView.as_view(), name='document_employee_list'),
    path('documents/manage/<int:employee_id>/', document_views.DocumentListView.as_view(), name='document_list'),
    path('documents/upload/<int:employee_id>/', document_views.DocumentCreateView.as_view(), name='document_upload'),
    path('documents/<int:pk>/delete/', document_views.DocumentDeleteView.as_view(), name='document_delete'),
    path('documents/<int:pk>/download/', document_views.download_document, name='document_download'),
    path('documents/export-bank-details/', document_views.export_bank_details_excel, name='export_bank_details'),
    
    # Attendance Report URLs
    path('attendance/report/', attendance_views.AttendanceReportView.as_view(), name='attendance_report'),
    path('attendance/override/<int:attendance_id>/', attendance_views.override_attendance_status, name='override_attendance_status'),
    path('attendance/export/', attendance_views.export_attendance_report_excel, name='export_attendance_report'),
    
    # Support Ticket System URLs
    path('tickets/', support_views.TicketListView.as_view(), name='ticket_list'),
    path('tickets/create/', support_views.TicketCreateView.as_view(), name='ticket_create'),
    path('tickets/<int:pk>/', support_views.TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/<int:ticket_id>/comment/', support_views.add_ticket_comment, name='add_ticket_comment'),
    path('tickets/<int:ticket_id>/update-status/', support_views.update_ticket_status, name='update_ticket_status'),
    
    # MIS (Management Information System) URLs
    path('mis/', views.mis_dashboard, name='mis_dashboard'),
    path('mis/create/', views.mis_create, name='mis_create'),
    path('mis/<int:pk>/', views.mis_detail, name='mis_detail'),
    path('mis/<int:pk>/edit/', views.mis_edit, name='mis_edit'),
    path('mis/<int:pk>/manager-edit/', views.mis_manager_edit, name='mis_manager_edit'),
    path('mis/<int:pk>/delete/', views.mis_delete, name='mis_delete'),
    path('mis/<int:pk>/admin-edit/', views.mis_admin_edit, name='mis_admin_edit'),
    path('mis/<int:pk>/admin-delete/', views.mis_admin_delete, name='mis_admin_delete'),
    path('mis/export/', views.mis_export_excel, name='mis_export_excel'),
    
    # Lead Assignment Management URLs
    path('lead-assignment/', staff_views.lead_assignment_dashboard, name='lead_assignment_dashboard'),
    path('lead-assignment/<int:pk>/', staff_views.lead_assignment_detail, name='lead_assignment_detail'),
    path('lead-assignment/<int:pk>/reassign/', staff_views.reassign_lead, name='reassign_lead'),
    path('lead-assignment/<int:pk>/update/', staff_views.update_lead_status, name='update_lead_status'),
    path('lead-assignment/<int:pk>/activity/', staff_views.lead_activity_logs, name='lead_activity_logs'),
    path('lead-assignment/employee/<int:employee_id>/', staff_views.employee_leads_view, name='employee_leads'),
    
    # Interview Management URLs
    path('interviews/', staff_views.interview_dashboard, name='interview_dashboard'),
    path('interviews/candidates/', staff_views.candidate_list, name='candidate_list'),
    path('interviews/candidates/add/', staff_views.add_candidate, name='add_candidate'),
    path('interviews/candidates/<int:candidate_id>/edit/', staff_views.edit_candidate, name='edit_candidate'),
    path('interviews/schedule/', staff_views.schedule_interview, name='schedule_interview'),
    path('interviews/schedule/<int:candidate_id>/', staff_views.schedule_interview, name='schedule_interview_for_candidate'),
    path('interviews/<int:interview_id>/', staff_views.interview_detail, name='interview_detail'),
    path('interviews/send-reminders/', staff_views.send_interview_reminders, name='send_interview_reminders'),
    
    # Password Change Request URLs
    path('password-change-request/', staff_views.password_change_request, name='password_change_request'),
    path('password-requests/', staff_views.password_request_list, name='password_request_list'),
    path('password-requests/<int:request_id>/change/', staff_views.change_user_password, name='change_user_password'),
    path('password-requests/<int:request_id>/approve/', staff_views.approve_password_request, name='approve_password_request'),
    path('password-requests/<int:request_id>/reject/', staff_views.reject_password_request, name='reject_password_request'),
    
    # Team Members URLs
    path('team-members/', staff_views.team_members, name='team_members'),
    
    # Lead Activity Tracking URLs
    path('lead-activity/', views.lead_activity_logs, name='lead_activity_logs'),
    path('lead-activity/<int:activity_id>/', views.lead_activity_detail, name='lead_activity_detail'),
    
    # EMI Calculator URLs
    path('emi-calculator/', views.emi_calculator, name='emi_calculator'),
    
    # Geolocation Security URLs
    path('geolocation-logs/', views.geolocation_logs, name='geolocation_logs'),
    path('geolocation-logs/export/', views.export_geolocation_logs, name='export_geolocation_logs'),
]
