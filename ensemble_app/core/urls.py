from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import LIFUpdateView, LIFDeleteView

from .views import (
    LIFUpdateView,
    GroupDetailView,
    ServiceListView, 
    LearnerAttendanceView,
    LearnerGroupsView,
    LearnerProjectPlansView,
    ServiceCreateView, 
    ServiceUpdateView, 
    ServiceDeleteView,
    ModuleListView, 
    ModuleCreateView, 
    ModuleUpdateView, 
    ModuleDeleteView,
    ServiceModuleListView, 
    external_project_list,
    ServiceModuleCreateView, 
    ServiceModuleUpdateView, 
    ServiceModuleDeleteView,
    POEListView,
    AdminPOETemplateUploadView,
    AdminPOEAnnextureConfigView,
    venuebooking_events_api,
    ProjectPlanListView, 
    ProjectPlanCreateView, 
    ProjectPlanUpdateView, 
    ProjectPlanDeleteView,
    SessionDateListView, 
    SessionDateCreateView, 
    SessionDateUpdateView, 
    SessionDateDeleteView,
    VenueListView, 
    VenueCreateView,
    VenueBookingListView, 
    VenueBookingCreateView, 
    VenueBookingUpdateView, 
    VenueBookingDeleteView,
    SLADashboardView, 
    SLADetailView, 
    AddLearnerQualificationView, 
    BillingExportView, 
    upload_fingerprint, 
    FingerprintListView, 
    AssignUserIDView,
    assign_learner_qualification_to_group,
    LearnerListView,
    LearnerScheduleListView,
    EditLearnerTimesView,
    EditQualificationTimesView,
    QualificationTimesListView,
    EditLearnerView,
    LearnerDetailsView,
    LearnerRoleAssignmentView,
    GroupManagementView,
    BillingPaymentsView, 
    get_sla_qualifications,
    FinanceDashboardView, 
    SLAWizardStep1View, 
    SLAWizardStep1View, 
    SLAWizardStep2View, 
    SLAWizardStep3View,
    SLAWizardStep4View,
    LearnerAutocomplete,
    SLAWizardStep4View,
    LearnerPortalView,
    POESubmissionView,
    FacilitatorPOEListView,
    FacilitatorPOEFeedbackView,
    FacilitatorAutocomplete,
    TemplateView,
    AddLearnerView,
    all_sessions_api,
    DeleteLearnerView,
    GroupCreateView, 
    get_learner_qualifications,
    VenueBookingCalendarView,
    ProjectPlanDetailView,
    upload_group_excel,
    SetLearnerPasswordView,
    upload_module_excel,
    upload_group_excel, 
    upload_module_excel,
    upload_project_plan_excel,
    upload_session_date_excel,
    FacilitatorAutocomplete,
    GroupQualificationAssignmentView,
    AdobeFormListView, AdobeFormUploadView, AdobeFormDownloadView, AdobeFormFilledSubmitView,
    LIFCreateView,
    upload_lif_template,
    map_lif_template_fields,
    lif_template_list,
    generate_lif_word,
)
    
from django.contrib.auth.views import LogoutView
from .views import home_redirect_view, LearnerHomeView 
from .views import RolePermissionManagementView

urlpatterns = [
    path('home-redirect/', home_redirect_view, name='home_redirect'),
    path('learner_home/', LearnerHomeView.as_view(), name='learner_home'),
    path('', SLADashboardView.as_view(), name='sla_dashboard'),
    path('sla/<int:pk>/', SLADetailView.as_view(), name='sla_detail'),
    path('sla/<int:sla_id>/qual/<int:qual_id>/add/', AddLearnerQualificationView.as_view(), name='add_learner_qualification'),
    path('billing/export/', BillingExportView.as_view(), name='billing_export'),
    path('fingerprint/upload/', upload_fingerprint, name='upload_fingerprint'),
    path('fingerprint/', FingerprintListView.as_view(), name='fingerprint_list'),
    path('learner/<int:learner_id>/assign-user-id/', AssignUserIDView.as_view(), name='assign_user_id'),
    path('learners/', LearnerListView.as_view(), name='learner_list'),
    path('learner-schedules/', LearnerScheduleListView.as_view(), name='learner_schedule_list'),
    path('learner-qualification/<int:learner_qualification_id>/edit-times/', EditLearnerTimesView.as_view(), name='edit_learner_times'),
    path('qualification/<int:qual_id>/edit-times/', EditQualificationTimesView.as_view(), name='edit_qualification_times'),
    path('qualifications/times/', QualificationTimesListView.as_view(), name='qualification_times_list'),
    path('learner/<int:learner_id>/edit/', EditLearnerView.as_view(), name='edit_learner'),
    path('learner/<int:learner_id>/', LearnerDetailsView.as_view(), name='learner_details'),
    path('learner/roles/', LearnerRoleAssignmentView.as_view(), name='learner_role_assignment'),
    path('groups/manage/', GroupManagementView.as_view(), name='group_management'),
    path('groups/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    path('groups/assign-lq/', assign_learner_qualification_to_group, name='assign_learner_qualification_to_group'),
    path("billing/payments/", BillingPaymentsView.as_view(), name="billing_payments"),
    path("finance/", FinanceDashboardView.as_view(), name="finance_dashboard"),
    path('accounts/', include('django.contrib.auth.urls')),
    path("finance/add-sla/", SLAWizardStep1View.as_view(), name="add_sla_wizard"),
    path("finance/add-sla/<int:sla_id>/qualifications/", SLAWizardStep2View.as_view(), name="add_sla_qualifications"),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('ajax/learner-qualifications/', get_learner_qualifications, name='get_learner_qualifications'),
    path("finance/add-sla/<int:sla_id>/billing/",SLAWizardStep3View.as_view(),name="add_sla_billing"),
    path("finance/add-sla/<int:sla_id>/learners/", SLAWizardStep4View.as_view(), name="add_sla_learners"),
    path('ajax/get_sla_qualifications/', get_sla_qualifications, name='get_sla_qualifications'),
        path(
      'learner-autocomplete/',
      LearnerAutocomplete.as_view(),
      name='learner-autocomplete'
    ),
    path(
      'finance/add-sla/<int:sla_id>/learners/',
      SLAWizardStep4View.as_view(),
      name='add_sla_learners'
    ),
    path('portal/', LearnerPortalView.as_view(), name='learner_portal'),
        path(
        'portal/attendance/',
        TemplateView.as_view(template_name='portal/attendance.html'),
        name='view_attendance'
    ),
    path(
        'portal/upcoming-dates/',
        TemplateView.as_view(template_name='portal/upcoming_dates.html'),
        name='view_upcoming_dates'
    ),
    path(
        'portal/submit-poe/',
        TemplateView.as_view(template_name='portal/submit_poe.html'),
        name='submit_poe'
    ),
    path(
        'portal/sit-summative-exam/',
        TemplateView.as_view(template_name='portal/summative_exam.html'),
        name='sit_summative_exam'
    ),
    path('learners/add/', AddLearnerView.as_view(), name='add_learner'),
    path('learners/<int:learner_id>/delete/', DeleteLearnerView.as_view(), name='delete_learner'),
    path('projectplans/', ProjectPlanListView.as_view(), name='projectplan_list'),
    path('projectplans/add/', ProjectPlanCreateView.as_view(), name='projectplan_add'),
    path('projectplans/<int:pk>/edit/', ProjectPlanUpdateView.as_view(), name='projectplan_edit'),
    path('projectplans/<int:pk>/delete/', ProjectPlanDeleteView.as_view(), name='projectplan_delete'),
    path('projectplans/<int:pk>/', ProjectPlanDetailView.as_view(), name='projectplan_detail'),
    path('api/all-sessions/', all_sessions_api, name='all_sessions_api'),
    path('sessiondates/', SessionDateListView.as_view(), name='sessiondate_list'),
    path('sessiondates/add/', SessionDateCreateView.as_view(), name='sessiondate_add'),
    path('sessiondates/<int:pk>/edit/', SessionDateUpdateView.as_view(), name='sessiondate_edit'),
    path('sessiondates/<int:pk>/delete/', SessionDateDeleteView.as_view(), name='sessiondate_delete'),

    path('venues/', VenueListView.as_view(), name='venue_list'),
    path('venues/add/', VenueCreateView.as_view(), name='venue_add'),

    path('venuebookings/', VenueBookingListView.as_view(), name='venuebooking_list'),
    path('venuebookings/add/', VenueBookingCreateView.as_view(), name='venuebooking_add'),
    path('venuebookings/<int:pk>/edit/', VenueBookingUpdateView.as_view(), name='venuebooking_edit'),
    path('venuebookings/<int:pk>/delete/', VenueBookingDeleteView.as_view(), name='venuebooking_delete'),
    path('api/venuebookings/', venuebooking_events_api, name='venuebooking_events_api'),  # Add this line
    path('venuebookings/calendar/', VenueBookingCalendarView.as_view(), name='venuebooking_calendar'),
    # --- Service CRUD ---
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/add/", ServiceCreateView.as_view(), name="service-add"),
    path("services/<int:pk>/edit/", ServiceUpdateView.as_view(), name="service-edit"),
    path("services/<int:pk>/delete/", ServiceDeleteView.as_view(), name="service-delete"),

    # --- Module CRUD ---
    path("modules/", ModuleListView.as_view(), name="module-list"),
    path("modules/add/", ModuleCreateView.as_view(), name="module-add"),
    path("modules/<int:pk>/edit/", ModuleUpdateView.as_view(), name="module-edit"),
    path("modules/<int:pk>/delete/", ModuleDeleteView.as_view(), name="module-delete"),

    # --- Service_Module CRUD ---
    path("service-modules/", ServiceModuleListView.as_view(), name="service-module-list"),
    path("service-modules/add/", ServiceModuleCreateView.as_view(), name="service-module-add"),
    path("service-modules/<int:pk>/edit/", ServiceModuleUpdateView.as_view(), name="service-module-edit"),
    path("service-modules/<int:pk>/delete/", ServiceModuleDeleteView.as_view(), name="service-module-delete"),
    path('groups/upload_excel/', upload_group_excel, name='upload_group_excel'),
    path('modules/upload_excel/', upload_module_excel, name='upload_module_excel'),
    path('projectplans/upload_excel/', upload_project_plan_excel, name='upload_project_plan_excel'),
    path('sessiondates/upload_excel/', upload_session_date_excel, name='upload_session_date_excel'),
    path('facilitator-autocomplete/', FacilitatorAutocomplete.as_view(), name='facilitator-autocomplete'),
    # urls.py
    path('venuebookings/<int:pk>/delete/', VenueBookingDeleteView.as_view(), name='venuebooking_delete'),
    path('venuebookings/<int:pk>/edit/', VenueBookingUpdateView.as_view(), name='venuebooking_edit'),
    path('group-qualifications/', GroupQualificationAssignmentView.as_view(), name='group_qualification_assignment'),
    path('learner/<int:learner_id>/set-password/', 
     SetLearnerPasswordView.as_view(), 
     name='set_learner_password'),
]

urlpatterns += [
    path('adobe-forms/', AdobeFormListView.as_view(), name='adobe_form_list'),
    path('adobe-forms/upload/', AdobeFormUploadView.as_view(), name='adobe_form_upload'),
    path('adobe-forms/<int:pk>/download/', AdobeFormDownloadView.as_view(), name='adobe_form_download'),
    path('adobe-forms/<int:pk>/submit/', AdobeFormFilledSubmitView.as_view(), name='adobe_form_submit'),
]

urlpatterns += [
    path('poe/submit/', POESubmissionView.as_view(), name='poe_submission'),
    path('facilitator/poes/', FacilitatorPOEListView.as_view(), name='facilitator_poe_list'),
    path('facilitator/poe/<int:poe_id>/feedback/', FacilitatorPOEFeedbackView.as_view(), name='facilitator_poe_feedback'),
]

# Add these URL patterns to urlpatterns list
urlpatterns += [
    path('poe/submit/', POESubmissionView.as_view(), name='poe_submission'),
    path('poe/list/', POEListView.as_view(), name='poe_list'),
    path('poe/templates/', AdminPOETemplateUploadView.as_view(), name='poe_template_list'),
    path('poe/templates/add/', AdminPOETemplateUploadView.as_view(), name='poe_template_add'),
    path('poe/templates/<int:template_id>/annextures/', AdminPOEAnnextureConfigView.as_view(), name='poe_annextures'),
]

from .views import AdminPOESubmissionsDashboardView

urlpatterns += [
    path('poe/poe-dashboard/', AdminPOESubmissionsDashboardView.as_view(), name='admin_poe_dashboard'),
]

from .views import assess_poe
urlpatterns += [
    path('poe/<int:poe_id>/assess/', assess_poe, name='assess_poe'),
]

from .views import learner_assessment_results

urlpatterns += [
    path('poe/results/', learner_assessment_results, name='learner_assessment_results'),
]

urlpatterns += [
    path('role-permissions/', RolePermissionManagementView.as_view(), name='role_permission_management'),
]

from .views import SwitchRoleView

urlpatterns += [
    path('switch-role/', SwitchRoleView.as_view(), name='switch_role'),
]

urlpatterns += [
    # ...existing URL patterns...

    # Learner portal views
    path('learner/attendance/', LearnerAttendanceView.as_view(), name='learner_attendance'),
    path('learner/groups/', LearnerGroupsView.as_view(), name='learner_groups'),
    path('learner/project-plans/', LearnerProjectPlansView.as_view(), name='learner_project_plans'),

    # ...remaining URL patterns...
]
from .views import GroupUpdateView, GroupDeleteView

urlpatterns += [
    # ...existing urls...
    path('groups/<int:pk>/edit/', GroupUpdateView.as_view(), name='group-edit'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group-delete'),
]

from .views import venue_availability_api
urlpatterns += [
    path('api/venue-availability/', venue_availability_api, name='venue_availability_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('lif-form/', LIFCreateView.as_view(), name='lif_form'),
    path('lif-form/update/', LIFUpdateView.as_view(), name='lif_update'),
    path('lif_templates/upload/', upload_lif_template, name='upload_lif_template'),
    path('lif_templates/<int:template_id>/map/', map_lif_template_fields, name='map_lif_template_fields'),
    path('lif_templates/list/', lif_template_list, name='lif_template_list'),
    path('lif_templates/generate/', generate_lif_word, name='generate_lif_word'),
]

from .views import VenueBookingSwitchView

urlpatterns += [
    path('venuebooking/switch/', VenueBookingSwitchView.as_view(), name='venuebooking_switch'),
]

from .views import external_project_list

urlpatterns += [
    path('external-projects/', external_project_list, name='external_project_list'),
]

from .views import VenueBookingModalFormView, CancelVenueBookingView

urlpatterns += [
 
    path('venuebooking/modal-form/', VenueBookingModalFormView.as_view(), name='venuebooking_modal_form'),
    path('cancel-venue-booking/', CancelVenueBookingView.as_view(), name='cancel_venue_booking'),
]

from .views import generate_bulk_lif_zip

urlpatterns += [
    path('lif/generate_bulk_zip/', generate_bulk_lif_zip, name='generate_bulk_lif_zip'),
]

from .views import CognitoLIFEntriesView

urlpatterns += [
    path('cognito-lif/', CognitoLIFEntriesView.as_view(), name='cognito_lif_entries'),
]

from .views import ExportCognitoToLIFView

urlpatterns += [
    path('cognito-lif/export/', ExportCognitoToLIFView.as_view(), name='export_cognito_to_lif'),
]

from .views import lif_list_json

urlpatterns += [
    path('lif-list-json/', lif_list_json, name='lif_list_json'),
]

# Add this to your urlpatterns
from .views import LIFTemplateDeleteView

urlpatterns += [
    path('lif_template/<int:pk>/delete/', LIFTemplateDeleteView.as_view(), name='lif_template_delete'),
]

from . import views

urlpatterns += [
    # ...existing urls...
    path('groups/generate-admin-pack/', views.generate_bulk_admin_pack_zip, name='generate_bulk_admin_pack_zip'),
    path('lif/<int:pk>/', LIFUpdateView.as_view(), name='lif_update'),  # Read/Edit
    path('lif/<int:pk>/delete/', LIFDeleteView.as_view(), name='lif_delete'),  # Delete
]

