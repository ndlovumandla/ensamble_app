from django import forms
from django.contrib import admin
from django.db.models import Q
from django.urls import path
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin import SimpleListFilter
import re
import secrets
from django.contrib import messages

from .models import (
    Customer,
    Service,
    SLA,
    SLA_Qualifications,
    BillingHistory,
    BillingHistoryItem,
    Learner,
    LearnerQualification,
    VATRate,
    Fingerprint,
    WeeklySchedule,
    Role,
    LearnerRole,
    Group,
    SETA,
    SessionDate,
    AdobeForm,
    RolePermission,
)

# ─── Core Admins ─────────────────────────────────────────────────────

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("shorthand", "name", "gl_code", "saqa_id", "unit_price")
    search_fields = ("name", "shorthand", "saqa_id", "gl_code")

@admin.register(SETA)
class SETAAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "projectcode", "service", "seta", "start_date", "end_date")
    search_fields = ("name", "projectcode")
    list_filter = ("service", "seta")
    autocomplete_fields = ["service", "seta"]

@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ("sla_reference", "customer", "start_date", "end_date")
    search_fields = ("sla_reference", "customer__name",)

@admin.register(SLA_Qualifications)
class SLAQualificationsAdmin(admin.ModelAdmin):
    list_display = ("id", "sla", "service", "learner_count", "employment_status")
    list_filter = ("sla", "employment_status")
    search_fields = ("sla__sla_reference", "service__name",)

# ─── Billing History Inline & Admin ──────────────────────────────────

class BillingHistoryItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            amt = form.cleaned_data.get('amount') or 0
            total += amt
        if total != self.instance.amount:
            raise ValidationError(
                f"Sum of line items (R{total:.2f}) must equal invoice total "
                f"(R{self.instance.amount:.2f})."
            )

class BillingHistoryItemInline(admin.TabularInline):
    model = BillingHistoryItem
    formset = BillingHistoryItemFormSet
    extra = 1
    verbose_name = "Line-item"
    verbose_name_plural = "Line-items"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sla_qualification":
            object_id = request.resolver_match.kwargs.get("object_id")
            if object_id:
                bh = BillingHistory.objects.filter(pk=object_id).first()
                kwargs["queryset"] = (
                    SLA_Qualifications.objects.filter(sla=bh.sla)
                    if bh else SLA_Qualifications.objects.none()
                )
            else:
                kwargs["queryset"] = SLA_Qualifications.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class NumericSLAFilter(SimpleListFilter):
    title = 'By sla'
    parameter_name = 'sla'

    def lookups(self, request, model_admin):
        # Get all SLA objects and sort them numerically by the number in sla_reference
        slas = list(SLA.objects.all())
        def sla_num(sla):
            match = re.search(r'(\d+)', sla.sla_reference)
            return int(match.group(1)) if match else 0
        slas.sort(key=sla_num)
        return [(sla.id, sla.sla_reference) for sla in slas]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sla_id=self.value())
        return queryset

@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'sla',
        'invoice_number',
        'invoice_date',
        'due_date',
        'payment_date',
        'amount',
        'billed',
    )
    list_filter = (NumericSLAFilter, 'billed',)
    inlines = [BillingHistoryItemInline]

@admin.register(Learner)
class LearnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'UserID', 'FirstName', 'Surname', 'IDNumber', 'Gender', 'Equity')
    search_fields = ('UserID', 'FirstName', 'Surname', 'IDNumber')
    list_filter = ('Gender', 'Equity')
    actions = ['create_user_accounts']

    def create_user_accounts(self, request, queryset):
        created = 0
        skipped = 0
        for learner in queryset:
            # Use the field "email_address" (adjust this if your model uses a different name)
            learner_email = getattr(learner, 'email_address', None) or getattr(learner, 'EmailAddress', None) or getattr(learner, 'email', None)
            
            self.message_user(
                request,
                f"Processing learner: {learner.FirstName} {learner.Surname} (Email: {learner_email or 'No email'})",
                level=messages.INFO
            )
            
            # Check if the learner already has an associated user by checking the foreign key ID
            if getattr(learner, 'user_id', None):
                self.message_user(
                    request, 
                    f"Skipped - User already exists for {learner.FirstName} {learner.Surname}",
                    level=messages.WARNING
                )
                skipped += 1
                continue

            if not learner_email:
                self.message_user(
                    request,
                    f"Skipped - No email found for {learner.FirstName} {learner.Surname}",
                    level=messages.WARNING
                )
                skipped += 1
                continue

            username = learner_email
            if User.objects.filter(username=username).exists():
                self.message_user(
                    request,
                    f"Skipped - Username {username} already exists in User table",
                    level=messages.WARNING
                )
                skipped += 1
                continue

            password = secrets.token_urlsafe(8)
            user = User.objects.create_user(
                username=username,
                password=password,
                email=learner_email
            )
            learner.user = user
            learner.save()
            created += 1
            self.message_user(
                request,
                f"Created user for {learner.FirstName} {learner.Surname}: {username} / {password}",
                level=messages.SUCCESS
            )

        if created:
            self.message_user(request, f"Created {created} user(s).", level=messages.SUCCESS)
        if skipped:
            self.message_user(request, f"Skipped {skipped} learner(s).", level=messages.WARNING)

    create_user_accounts.short_description = (
        "Create user accounts for selected learners using their email and auto-generated passwords"
    )

class WeeklyScheduleInline(admin.TabularInline):
    model = WeeklySchedule
    extra = 7
    max_num = 7

# ─── LearnerQualification Admin with Custom Add View ─────────────────

@admin.register(LearnerQualification)
class LearnerQualificationAdmin(admin.ModelAdmin):
    list_display = ("id", "learner", "sla_qualification", "status", "created_at", "expected_clock_in", "expected_clock_out")
    list_filter = ("sla_qualification__sla", "sla_qualification", "status")
    search_fields = (
        "learner__FirstName",
        "learner__Surname",
        "learner__IDNumber",
        "learner__UserID",
    )
    autocomplete_fields = ["learner", "sla_qualification"]
    inlines = [WeeklyScheduleInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "add/",
                self.admin_site.admin_view(self.custom_add_view),
                name="learnerqualification_add",
            ),
        ]
        return custom_urls + urls

    def custom_add_view(self, request):
        context = dict(self.admin_site.each_context(request))
        if request.method == "POST":
            action = request.POST.get("action")
            lq_id = request.POST.get("learner_qualification_id")
            sla_param = request.POST.get("sla")
            if action and lq_id:
                try:
                    lq = LearnerQualification.objects.get(id=lq_id)
                except LearnerQualification.DoesNotExist:
                    context["error"] = "LearnerQualification record not found."
                else:
                    if action == "remove":
                        reason = request.POST.get("exit_reason")
                        if reason:
                            lq.status = "removed"
                            lq.exit_reason = reason
                            lq.save()
                            context["success"] = f"Learner marked as removed ({reason})."
                        else:
                            lq.delete()
                            context["success"] = "Learner permanently removed."
                            return redirect(f"{request.path}?sla={sla_param}")
                    elif action == "reactivate":
                        lq.status = "active"
                        lq.exit_reason = ""
                        lq.save()
                        context["success"] = "Learner reactivated."
            else:
                sla_id = request.POST.get("sla")
                search = request.POST.get("learner_search")
                qual_id = request.POST.get("sla_qualification")
                if sla_id and search and qual_id:
                    learner = Learner.objects.filter(
                        Q(FirstName__icontains=search) |
                        Q(Surname__icontains=search) |
                        Q(IDNumber__icontains=search) |
                        Q(UserID__exact=search)
                    ).first()
                    if learner:
                        try:
                            qual = SLA_Qualifications.objects.get(id=qual_id)
                        except SLA_Qualifications.DoesNotExist:
                            context["error"] = "Qualification not found."
                        else:
                            existing = LearnerQualification.objects.filter(
                                learner=learner,
                                sla_qualification=qual
                            ).first()
                            if existing:
                                if existing.status == "removed":
                                    existing.status = "active"
                                    existing.exit_reason = ""
                                    existing.save()
                                    context["success"] = (
                                        f"{learner.FirstName} {learner.Surname} reactivated "
                                        f"for {qual.service.name}."
                                    )
                                else:
                                    context["error"] = (
                                        f"{learner.FirstName} {learner.Surname} "
                                        "is already active in this qualification."
                                    )
                            else:
                                LearnerQualification.objects.create(
                                    learner=learner,
                                    sla_qualification=qual,
                                    status="active"
                                )
                                context["success"] = (
                                    f"{learner.FirstName} {learner.Surname} added "
                                    f"to {qual.service.name}."
                                )
                    else:
                        context["error"] = "Learner not found."
        raw_sla = request.GET.get("sla") or request.POST.get("sla")
        if raw_sla in (None, "", "None"):
            selected_sla = None
        else:
            try:
                selected_sla = int(raw_sla)
            except (ValueError, TypeError):
                selected_sla = None
        context["selected_sla"] = selected_sla
        context["slas"] = SLA.objects.all().order_by("sla_reference")
        if selected_sla is not None:
            quals = (
                SLA_Qualifications.objects
                .filter(sla_id=selected_sla)
                .select_related("service")
            )
            context["sla_qualifications"] = quals
            learners_map = {}
            for qual in quals:
                lqs = LearnerQualification.objects.filter(
                    sla_qualification=qual
                ).select_related("learner")
                learners = []
                for lq in lqs:
                    l = lq.learner
                    l.status = lq.status
                    l.exit_reason = lq.exit_reason or ""
                    l.learnerqualification_id = lq.id
                    learners.append(l)
                learners_map[qual.id] = learners
            context["learners_by_qualification"] = learners_map
        return render(
            request,
            "admin/custom_add_learnerqualification.html",
            context,
        )

@admin.register(VATRate)
class VATRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'rate', 'active')
    list_editable = ('active',)
    ordering = ('-active', 'code')

@admin.register(Fingerprint)
class FingerprintAdmin(admin.ModelAdmin):
    list_display = ('learner', 'date', 'time', 'is_clock_in')
    list_filter = ('date', 'is_clock_in')
    search_fields = ('learner__UserID', 'learner__FirstName', 'learner__Surname')
    ordering = ('date', 'time')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(LearnerRole)
class LearnerRoleAdmin(admin.ModelAdmin):
    list_display = ('learner', 'role')
    list_filter = ('role',)
    search_fields = ('learner__FirstName', 'learner__Surname', 'learner__IDNumber', 'learner__UserID', 'role__name')
    autocomplete_fields = ['learner', 'role']

@admin.register(SessionDate)
class SessionDateAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_plan', 'start_date', 'end_date', 'facilitator')
    search_fields = ('project_plan__group__name', 'facilitator__learner__FirstName', 'facilitator__learner__Surname')

# Inline learner profile on the User admin
class LearnerInline(admin.StackedInline):
    model = Learner
    can_delete = False
    fk_name = 'user'

class CustomUserAdmin(DefaultUserAdmin):
    inlines = (LearnerInline,)

# Register the User model with our custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(AdobeForm)
class AdobeFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'url_name', 'has_access')
    list_filter = ('role', 'has_access')
    search_fields = ('role__name', 'url_name')
    change_list_template = 'admin/core/rolepermission/change_list.html'  # Add this line

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('manage-permissions/', 
                 self.admin_site.admin_view(self.manage_permissions_view),
                 name='manage_permissions'),
        ]
        return custom_urls + urls

    def get_url_list(self):
        # Dictionary of URL names and their descriptions
        return [
            # --- SLA & Dashboard ---
            ('sla_dashboard', 'SLA Dashboard'),
            ('sla_detail', 'SLA Detail'),
            ('add_learner_qualification', 'Add Learner Qualification'),
            ('billing_export', 'Export Billing'),
            ('billing_payments', 'Manage Payments'),
            ('finance_dashboard', 'Finance Dashboard'),
            ('add_sla_wizard', 'Add SLA'),
            ('add_sla_qualifications', 'Add SLA Qualifications'),
            ('add_sla_billing', 'Add SLA Billing'),
            ('add_sla_learners', 'Add SLA Learners'),
            ('get_sla_qualifications', 'Get SLA Qualifications (AJAX)'),

            # --- Learner Management ---
            ('learner_list', 'Learner Management'),
            ('learner_schedule_list', 'Learner Schedules'),
            ('edit_learner_times', 'Edit Learner Times'),
            ('edit_qualification_times', 'Edit Qualification Times'),
            ('qualification_times_list', 'View Qualification Times'),
            ('edit_learner', 'Edit Learner Details'),
            ('learner_details', 'View Learner Details'),
            ('learner_role_assignment', 'Assign Learner Roles'),
            ('assign_user_id', 'Assign User ID'),
            ('add_learner', 'Add Learner'),
            ('delete_learner', 'Delete Learner'),
            ('set_learner_password', 'Set Learner Password'),

            # --- Group Management ---
            ('group_management', 'Group Management'),
            ('group_create', 'Create Groups'),
            ('group-edit', 'Edit Group'),
            ('group-delete', 'Delete Group'),
            ('group_qualification_assignment', 'Assign Group Qualifications'),
            ('assign_learner_qualification_to_group', 'Assign Learner Qualification to Group'),

            # --- Project Plan & Session Dates ---
            ('projectplan_list', 'Project Plans'),
            ('projectplan_add', 'Add Project Plan'),
            ('projectplan_edit', 'Edit Project Plan'),
            ('projectplan_delete', 'Delete Project Plan'),
            ('projectplan_detail', 'Project Plan Detail'),
            ('sessiondate_list', 'Session Dates'),
            ('sessiondate_add', 'Add Session Date'),
            ('sessiondate_edit', 'Edit Session Date'),
            ('sessiondate_delete', 'Delete Session Date'),
            ('upload_project_plan_excel', 'Upload Project Plan Excel'),
            ('upload_session_date_excel', 'Upload Session Date Excel'),

            # --- Venue & Bookings ---
            ('venue_list', 'Venues'),
            ('venue_add', 'Add Venue'),
            ('venuebooking_list', 'Venue Bookings'),
            ('venuebooking_add', 'Add Venue Booking'),
            ('venuebooking_edit', 'Edit Venue Booking'),
            ('venuebooking_delete', 'Delete Venue Booking'),
            ('venuebooking_calendar', 'Venue Booking Calendar'),
            ('venuebooking_modal_form', 'Venue Booking Modal Form'),
            ('venuebooking_switch', 'Switch Venue Booking'),
            ('venue_availability_api', 'Venue Availability API'),
            ('venuebooking_events_api', 'Venue Booking Events API'),

            # --- Service/Module Management ---
            ('service-list', 'Services'),
            ('service-add', 'Add Service'),
            ('service-edit', 'Edit Service'),
            ('service-delete', 'Delete Service'),
            ('module-list', 'Modules'),
            ('module-add', 'Add Module'),
            ('module-edit', 'Edit Module'),
            ('module-delete', 'Delete Module'),
            ('service-module-list', 'Service Modules'),
            ('service-module-add', 'Add Service Module'),
            ('service-module-edit', 'Edit Service Module'),
            ('service-module-delete', 'Delete Service Module'),
            ('upload_group_excel', 'Upload Group Excel'),
            ('upload_module_excel', 'Upload Module Excel'),

            # --- POE & Adobe Forms ---
            ('poe_submission', 'Submit POE'),
            ('poe_list', 'View POE List'),
            ('poe_template_list', 'View POE Templates'),
            ('poe_template_add', 'Add POE Template'),
            ('poe_annextures', 'Manage POE Annextures'),
            ('facilitator_poe_list', 'Facilitator POE List'),
            ('facilitator_poe_feedback', 'Facilitator POE Feedback'),
            ('admin_poe_dashboard', 'Admin POE Dashboard'),
            ('adobe_form_list', 'Adobe Forms'),
            ('adobe_form_upload', 'Upload Adobe Forms'),
            ('adobe_form_download', 'Download Adobe Forms'),
            ('adobe_form_submit', 'Submit Adobe Forms'),

            # --- Learner Portal ---
            ('learner_portal', 'Learner Portal Access'),
            ('learner_home', 'Learner Home'),
            ('view_attendance', 'View Attendance'),
            ('view_upcoming_dates', 'View Upcoming Dates'),
            ('submit_poe', 'Submit POE'),
            ('sit_summative_exam', 'Sit Summative Exam'),

            # --- External Projects ---
            ('external_project_list', 'External Project List'),

            # --- LIF Forms ---
            ('lif_form', 'LIF Form'),
            ('lif_update', 'Update LIF Form'),
            ('upload_lif_template', 'Upload LIF Template'),
            ('map_lif_template_fields', 'Map LIF Template Fields'),
            ('lif_template_list', 'LIF Template List'),
            ('generate_lif_word', 'Generate LIF Word'),

            # --- Role Permissions ---
            ('role_permission_management', 'Role Permission Management'),
            ('switch_role', 'Switch Role'),

            # --- AJAX/Autocomplete ---
            ('learner-autocomplete', 'Learner Autocomplete'),
            ('facilitator-autocomplete', 'Facilitator Autocomplete'),
            ('get_learner_qualifications', 'Get Learner Qualifications (AJAX)'),
        ]

    def manage_permissions_view(self, request):
        roles = Role.objects.all()
        
        if request.method == 'POST':
            for role in roles:
                url_names = request.POST.getlist(f'permissions_{role.id}')
                # Update permissions for this role
                RolePermission.objects.filter(role=role).update(has_access=False)
                for url_name in url_names:
                    RolePermission.objects.update_or_create(
                        role=role,
                        url_name=url_name,
                        defaults={'has_access': True}
                    )
            self.message_user(request, 'Permissions updated successfully')
            return redirect('..')

        # Get current permissions
        role_permissions = {}
        for role in roles:
            role_permissions[role.id] = RolePermission.objects.filter(
                role=role, 
                has_access=True
            ).values_list('url_name', flat=True)

        context = {
            'opts': self.model._meta,
            'roles': roles,
            'url_list': self.get_url_list(),
            'role_permissions': role_permissions,
            'title': 'Manage Role Permissions',
            'is_popup': False,
            'has_permission': True,
            'app_label': self.model._meta.app_label,
            'original': None,
        }
        
        return render(request, 'admin/manage_permissions.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_manage_permissions_permission'] = True
        return super().changelist_view(request, extra_context)

