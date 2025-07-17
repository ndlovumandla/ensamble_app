from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

class Customer(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    gl_code = models.CharField(max_length=7)
    saqa_id = models.CharField(max_length=20)
    shorthand = models.CharField(max_length=10, unique=True)
    unit_price = models.FloatField(default=0.0)
    requires_summative_exam = models.BooleanField(default=False, help_text="Any QCTO qualification (service) requiring a summative exam")
    admin_pack_document = models.FileField(
        upload_to='service_admin_packs/',
        blank=True,
        null=True,
        help_text="Upload a Word document for this service's Admin Pack"
    )

    def __str__(self):
        return f"{self.shorthand} - {self.name}"

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

class SLA(models.Model):
    sla_reference   = models.CharField(max_length=20, unique=True)
    customer        = models.ForeignKey(Customer, on_delete=models.CASCADE)
    start_date      = models.DateField()
    end_date        = models.DateField()
    end_client_name = models.CharField(max_length=100, blank=True)
    num_tranches    = models.IntegerField()
    billing_day     = models.CharField(max_length=20)

    def __str__(self):
        return self.sla_reference

    class Meta:
        ordering = ['sla_reference']  # or another numeric field if needed

class SLA_Qualifications(models.Model):
    sla               = models.ForeignKey(SLA, on_delete=models.CASCADE)
    service           = models.ForeignKey(Service, on_delete=models.CASCADE)
    learner_count     = models.IntegerField()
    employment_status = models.CharField(max_length=20, blank=True, null=True)
    getting_data   = models.BooleanField(default=False)
    getting_laptop = models.BooleanField(default=False)
    lunch_provided = models.BooleanField(default=False)
    venue_location = models.CharField(max_length=255, blank=True, null=True)
    learnership    = models.FloatField(default=0.0)
    recruitment    = models.FloatField(default=0.0)
    hosting        = models.FloatField(default=0.0)
    technology     = models.FloatField(default=0.0)
    venue_cost     = models.FloatField(default=0.0)
    stipends       = models.FloatField(default=0.0)
    consulting     = models.FloatField(default=0.0)
    expected_clock_in = models.TimeField(null=True, blank=True)
    expected_clock_out = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sla} – {self.service} ({self.learner_count})"

    class Meta:
        verbose_name = "SLA Qualification"
        verbose_name_plural = "SLA Qualifications"

class BillingHistory(models.Model):
    sla = models.ForeignKey(SLA, on_delete=models.CASCADE)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    invoice_type = models.CharField(max_length=20, default="")
    invoice_number = models.CharField(max_length=20, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    amount = models.FloatField(default=0.0)
    billed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sla} - {self.invoice_type} ({self.invoice_number})"

    class Meta:
        verbose_name = "Billing History"
        verbose_name_plural = "Billing History"

class BillingHistoryItem(models.Model):
    billing_history = models.ForeignKey(
        BillingHistory,
        on_delete=models.CASCADE,
        related_name="items"
    )
    sla_qualification = models.ForeignKey(
        SLA_Qualifications,
        on_delete=models.PROTECT
    )
    amount = models.FloatField(
        default=0.0,
        help_text="Amount billed for this specific qualification"
    )

    class Meta:
        unique_together = ("billing_history", "sla_qualification")
        verbose_name = "Billing History Item"
        verbose_name_plural = "Billing History Items"
        ordering = ["sla_qualification"]

    def __str__(self):
        svc = self.sla_qualification.service.name
        return f"{svc}: R{self.amount:.2f}"

class Learner(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learner_profile',
        null=True,
        blank=True,
        help_text="Link to Django User; set after migration"
    )
    FirstName = models.CharField(max_length=255, default="Unknown")
    Surname = models.CharField(max_length=255, default="Unknown")
    IDNumber = models.CharField(max_length=255, unique=True, null=True, blank=True)
    Gender = models.CharField(max_length=20, default="Unknown", null=True, blank=True)
    Equity = models.CharField(max_length=50, default="Unknown", null=True, blank=True)
    EmailAddress = models.EmailField(null=True, blank=True)
    UserID = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    expected_clock_in = models.TimeField(null=True, blank=True)
    expected_clock_out = models.TimeField(null=True, blank=True)
    active_learnership = models.ForeignKey(
        'LearnerQualification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_learners'
    )

    def __str__(self):
        return f"{self.FirstName} {self.Surname}"

class Group(models.Model):
    id = models.AutoField(primary_key=True)
    projectcode = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='groups', null=True, blank=True)
    seta = models.ForeignKey('SETA', on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    sla_qualifications = models.ManyToManyField(
        SLA_Qualifications,
        related_name='groups',
        blank=True
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    project_lead = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='project_lead_groups'
    )
    etqa_lead = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='etqa_lead_groups'
    )

    def __str__(self):
        return f"Project {self.projectcode or 'N/A'}: {self.name}"

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"

class LearnerQualification(models.Model):
    sla_qualification = models.ForeignKey(SLA_Qualifications, on_delete=models.CASCADE)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('removed', 'Removed'),
            ('completed', 'Completed'),
            ('dropped', 'Dropped Out'),
            ('abducted', 'Abducted by Aliens'),
        ],
        default='active'
    )
    exit_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expected_clock_in = models.TimeField(null=True, blank=True)
    expected_clock_out = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.learner} - {self.sla_qualification} ({self.status})"

    class Meta:
        verbose_name = "Learner Qualification"
        verbose_name_plural = "Learner Qualifications"
        unique_together = ('learner', 'sla_qualification')

class WeeklySchedule(models.Model):
    learner_qualification = models.ForeignKey(LearnerQualification, on_delete=models.CASCADE, related_name='weekly_schedules')
    day = models.CharField(
        max_length=9,
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday')
        ]
    )
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('learner_qualification', 'day')
        verbose_name = "Weekly Schedule"
        verbose_name_plural = "Weekly Schedules"

    def __str__(self):
        return f"{self.learner_qualification.learner} - {self.day}"

class VATRate(models.Model):
    code = models.CharField(max_length=10, unique=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.code} @ {self.rate}% {'(current)' if self.active else ''}"

class Fingerprint(models.Model):
    learner = models.ForeignKey(
        Learner, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='fingerprints'
    )
    user_id = models.IntegerField(db_index=True)
    date = models.DateField(db_index=True)
    time = models.TimeField()
    is_clock_in = models.BooleanField(default=True)

    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['user_id', 'date', 'time']),
            models.Index(fields=['date', 'user_id']),
        ]
        verbose_name = "Fingerprint"
        verbose_name_plural = "Fingerprints"
        unique_together = ('user_id', 'date', 'time')

    def __str__(self):
        user_id = self.user_id
        return f"{user_id} - {'In' if self.is_clock_in else 'Out'} at {self.date} {self.time}"

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

class LearnerRole(models.Model):
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('learner', 'role')
        verbose_name = "Learner Role"
        verbose_name_plural = "Learner Roles"

    def __str__(self):
        return f"{self.learner} - {self.role}"

class SETA(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "SETA"
        verbose_name_plural = "SETAs"

class Module(models.Model):
    name = models.CharField(max_length=300, null=True, blank=True)
    code = models.IntegerField(unique=True, null=True, blank=True)  # Changed to IntegerField

    def __str__(self):
        return f"{self.code or ''} - {self.name or ''}"

class Service_Module(models.Model):
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    module = models.ForeignKey('Module', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.service} - {self.module}"
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError

class ProjectPlan(models.Model):
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    module = models.ForeignKey('Module', on_delete=models.CASCADE)
    module_briefing_session_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='module_briefing_session_persons'
    )
    remedial_briefing_session_start_date = models.DateField(null=True, blank=True)
    complete_formative_poe_date = models.DateField(null=True, blank=True)
    summative_qa_session_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='summative_qa_session_persons'
    )
    summative_qa_session_start_date = models.DateField(null=True, blank=True)
    complete_summative_poe_date = models.DateField(null=True, blank=True)
    assessment_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessment_persons'
    )
    assessment_date = models.DateField(null=True, blank=True)
    remedial_briefing_session_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='remedial_briefing_session_persons'
    )
    summative_qa_session_end_date = models.DateField(null=True, blank=True)
    remediation_submission_date = models.DateField(null=True, blank=True)
    remediation_assessment_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='remediation_assessment_persons'
    )
    remediation_assessment_date = models.DateField(null=True, blank=True)
    client_report_person = models.ForeignKey(
        'LearnerRole', on_delete=models.SET_NULL, null=True, blank=True, related_name='client_report_persons'
    )
    client_report_date = models.DateField(null=True, blank=True)
    module_briefing_session_start_date = models.DateField(null=True, blank=True)
    module_briefing_session_end_date = models.DateField(null=True, blank=True)
    remedial_briefing_session_end_date = models.DateField(null=True, blank=True)
    assessment_book_in_date = models.DateField(null=True, blank=True)
    assessment_book_out_date = models.DateField(null=True, blank=True)
    results_release_due_date = models.DateField(null=True, blank=True)
    remediation_booked_in_date = models.DateField(null=True, blank=True)
    remediation_booked_out_date = models.DateField(null=True, blank=True)
    remediation_results_release_due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.group} - {self.module}"


class SessionDate(models.Model):
    project_plan = models.ForeignKey('ProjectPlan', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    preferred_training_methodology = models.CharField(max_length=50)
    facilitator = models.ForeignKey(
        'LearnerRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role__name': 'Facilitator'},
        related_name='session_dates'
    )

    def __str__(self):
        return f"{self.project_plan} ({self.start_date} - {self.end_date})"

class Venue(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class VenueBooking(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
    ]
    session_date = models.ForeignKey('SessionDate', on_delete=models.SET_NULL, null=True, blank=True)
    venue = models.ForeignKey('Venue', on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    booking_purpose = models.CharField(max_length=100)
    facilitator = models.ForeignKey(
        'LearnerRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role__name': 'Facilitator'},
        related_name='venue_bookings'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='booked'
    )
    num_learners = models.IntegerField(null=True, blank=True, help_text="Number of learners attending")
    num_learners_lunch = models.IntegerField(null=True, blank=True, help_text="Number of learners getting lunch")
    combined_booking_id = models.CharField(max_length=36, null=True, blank=True, help_text="UUID for combined bookings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='venue_bookings'
    )
    
    def __str__(self):
        return f"{self.venue} ({self.start_datetime} - {self.end_datetime})"

    class Meta:
       pass

class AdobeForm(models.Model):
    name = models.CharField(max_length=255)
    pdf = models.FileField(upload_to='adobe_forms/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AdobeFormAnnexture(models.Model):
    adobe_form = models.ForeignKey(AdobeForm, on_delete=models.CASCADE, related_name='annextures')
    name = models.CharField(max_length=255)
    required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.adobe_form.name} - {self.name}"

class LearnerModulePOE(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('competent', 'Competent'),
        ('not_yet_competent', 'Not Yet Competent'),
    ]

    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='poes')
    learner_qualification = models.ForeignKey(LearnerQualification, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    poe_file = models.FileField(upload_to='poe_submissions/')
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    facilitator = models.ForeignKey(
        'LearnerRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role__name': 'Facilitator'},
        related_name='reviewed_poes'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    learner_assessment = models.ForeignKey(
        'LearnerAssessment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='poes'
    )

    class Meta:
        unique_together = ('learner', 'learner_qualification', 'module')

    def __str__(self):
        return f"{self.learner} - {self.module} ({self.get_status_display()})"

class POEAnnexture(models.Model):
    poe = models.ForeignKey(LearnerModulePOE, on_delete=models.CASCADE, related_name='annextures')
    # Add other fields for the annexure as needed
    file = models.FileField(upload_to='poe_annextures/')  # Example: file field

    def __str__(self):
        return f"Annexture for {self.poe}"

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    url_name = models.CharField(max_length=100)
    has_access = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'url_name')

    def __str__(self):
        return f"{self.role.name} - {self.url_name}"
    
# Add to existing ModulePOETemplate model class
class ModulePOETemplate(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    template_file = models.FileField(upload_to='poe_templates/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"POE Template for {self.module.name}"

class ModulePOEAnnexture(models.Model):
    template = models.ForeignKey(ModulePOETemplate, on_delete=models.CASCADE, related_name='required_annextures')
    name = models.CharField(max_length=100)
    required = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} for {self.template.module.name}"
    
class LIF(models.Model):
    learner = models.OneToOneField('Learner', on_delete=models.SET_NULL, null=True, blank=True, related_name='lif_form')

    # Identification
    national_id = models.CharField("National ID", max_length=255)
    alternative_id = models.CharField("Alternative ID", max_length=255, blank=True, null=True)
    ALTERNATIVE_ID_TYPE_CHOICES = [
        ('521', 'SAQA Member ID'),
        ('527', 'Passport Number'),
        ('529', "Driver's License"),
        ('531', 'Temporary ID Number'),
        ('533', 'None'),
        ('535', 'Unknown'),
        ('537', 'Student Number'),
        ('538', 'Work Permit Number'),
        ('539', 'Employee Number'),
        ('540', 'Birth Certificate Number'),
        ('541', 'HSRC Register Number'),
        ('561', 'ETQA Record Number'),
        ('565', 'Refugee Number'),
    ]
    alternative_id_type = models.CharField(
        "Alternative ID Type",
        max_length=3,
        choices=ALTERNATIVE_ID_TYPE_CHOICES,
        blank=True,
        null=True
    )

    # Codes
    EQUITY_CHOICES = [
        ('BA', 'Black African'), ('BC', 'Black Coloured'), ('BI', 'Black Indian'), ('Wh', 'White')
    ]
    equity_code = models.CharField("Equity Code", max_length=2, choices=EQUITY_CHOICES)

    NATIONALITY_CHOICES = [
        ('SA', 'South African'),
        ('SDC', 'SADC except SA'),
        ('ANG', 'Angola'),
        ('BOT', 'Botswana'),
        ('LES', 'Lesotho'),
        ('MAL', 'Malawi'),
        ('MAU', 'Mauritius'),
        ('MOZ', 'Mozambique'),
        ('NAM', 'Namibia'),
        ('SEY', 'Seychelles'),
        ('SWA', 'Swaziland'),
        ('TAN', 'Tanzania'),
        ('ZAI', 'Zaire'),
        ('ZAM', 'Zambia'),
        ('ZIM', 'Zimbabwe'),
        ('AIS', 'Asian Countries'),
        ('AUS', 'Australia Oceania'),
        ('EUR', 'European Countries'),
        ('NOR', 'North American Countries'),
        ('SOU', 'South/Central American'),
        ('ROA', 'Rest of Africa'),
        ('OOC', 'Other & Rest of Oceania'),
        ('U', 'Unspecified'),
        ('NOT', 'N/A: Institution'),
    ]
    nationality_code = models.CharField("Nationality Code", max_length=5, choices=NATIONALITY_CHOICES)

    HOME_LANGUAGE_CHOICES = [
        ('Afr', 'Afrikaans'), ('Eng', 'English'), ('Nde', 'isiNdebele'), ('Sep', 'sePedi'),
        ('Ses', 'seSotho'), ('Set', 'seTswana'), ('Swa', 'siSwati'), ('Tsh', 'tshiVenda'),
        ('Xho', 'isiXhosa'), ('Xit', 'xiTsonga'), ('Zul', 'isiZulu'), ('SASL', 'South African Sign Language'),
        ('Oth', 'Other'), ('U', 'Unknown')
    ]
    home_language_code = models.CharField("Home Language Code", max_length=5, choices=HOME_LANGUAGE_CHOICES)

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender_code = models.CharField("Gender", max_length=1, choices=GENDER_CHOICES, blank=True, null=True)

    CITIZEN_STATUS_CHOICES = [
        ('SA', 'South Africa'), ('D', 'Dual (SA plus other)'), ('O', 'Other'),
        ('PR', 'Permanent Resident'), ('U', 'Unknown')
    ]
    citizen_resident_status_code = models.CharField("Citizen Resident Status Code", max_length=2, choices=CITIZEN_STATUS_CHOICES, blank=True, null=True)

    PROVINCE_CHOICES = [
        ('1', 'Western Cape'), ('2', 'Eastern Cape'), ('3', 'Northern Cape'), ('4', 'Free State'),
        ('5', 'KwaZulu/Natal'), ('6', 'North West'), ('7', 'Gauteng/JHB'), ('7b', 'Gauteng/PTA'),
        ('8', 'Mpumalanga'), ('9', 'Limpopo'), ('X', 'Outside South Africa'), ('N', 'South African National')
    ]
    province_code = models.CharField("Province Code", max_length=2, choices=PROVINCE_CHOICES, blank=True, null=True)

    DISABILITY_CHOICES = [
        ('01', 'Sight (Even with Glasses)'), ('02', 'Hearing (Even with Hearing Aid)'), ('03', 'Communication (Talk/Listen)'),
        ('04', 'Physical (Move/Stand, etc.)'), ('05', 'Intellectual (Learn etc.)'), ('06', 'Emotional (Behaviour/Psychological)'),
        ('07', 'Multiple'), ('09', 'Disabled but unspecified'), ('N', 'None')
    ]
    disability_status_code = models.CharField("Disability Status Code", max_length=2, choices=DISABILITY_CHOICES,blank=True, null=True)

    SOCIO_ECONOMIC_CHOICES = [
        ('01', 'Employed'), ('02', 'Unemployed, seeking work'), ('03', 'Not working, not looking'),
        ('04', 'Home-maker, not working'), ('06', 'Scholar/Student, not working'), ('07', 'Pensioner/Retired, not working'),
        ('08', 'Not working, disabled'), ('09', 'Not working, no wish to work'), ('10', 'Not working, N.E.C.'),
        ('97', 'N/A: Aged <15'), ('98', 'N/A: Institution'), ('U', 'Unspecified')
    ]
    socio_economic_status_code = models.CharField("Socio-economic Status Code", max_length=2, choices=SOCIO_ECONOMIC_CHOICES, blank=True, null=True)

    # Personal
    learner_title = models.CharField("Learner Title", max_length=255, blank=True, null=True)
    learner_birth_date = models.DateField("Learner Birth Date")
    learner_first_name = models.CharField("Learner First Name", max_length=255)
    learner_middle_name = models.CharField("Learner Middle Name", max_length=255, blank=True, null=True)
    learner_last_name = models.CharField("Learner Last Name", max_length=255)
    learner_previous_last_name = models.CharField("Learner Previous Last Name", max_length=255, blank=True, null=True)
    learner_current_occupation = models.CharField("Learner Current Occupation", max_length=255, blank=True, null=True)
    years_in_occupation = models.PositiveIntegerField("Years in Occupation", blank=True, null=True)
    employer = models.CharField("Employer", max_length=255, blank=True, null=True)

    # Secondary Education
    HIGHEST_SECONDARY_EDUCATION_CHOICES = [
        ('Grade 8', 'Grade 8'),
        ('Grade 9', 'Grade 9'),
        ('Grade 10', 'Grade 10'),
        ('Grade 11', 'Grade 11'),
        ('Grade 12', 'Grade 12'),
    ]
    highest_secondary_education = models.CharField(
        "Highest Secondary Education",
        max_length=20,
        choices=HIGHEST_SECONDARY_EDUCATION_CHOICES,
        blank=True,
        null=True
    )
    secondary_school_name = models.CharField("School Name", max_length=255, blank=True, null=True)
    secondary_year_completed = models.PositiveIntegerField("Year Completed (Secondary)", blank=True, null=True)
    percentage_maths = models.DecimalField("Percentage - Maths", max_digits=5, decimal_places=2, blank=True, null=True)
    percentage_first_language = models.DecimalField("Percentage - 1st Language", max_digits=5, decimal_places=2, blank=True, null=True)
    percentage_second_language = models.DecimalField("Percentage - 2nd Language", max_digits=5, decimal_places=2, blank=True, null=True)

    # Tertiary Education
    TERTIARY_CHOICES = [
        ('National Certificate', 'National Certificate'),
        ('National Diploma', 'National Diploma'),
        ('National First Degree', 'National First Degree'),
        ('Post-doctoral Degree', 'Post-doctoral Degree'),
        ('Doctoral Degree', 'Doctoral Degree'),
        ('Professional Qualification', 'Professional Qualification'),
        ('Honours Degree', 'Honours Degree'),
        ('National Higher Diploma', 'National Higher Diploma'),
        ('National Masters Diploma', 'National Masters Diploma'),
        ('National Higher', 'National Higher'),
        ('Further Diploma', 'Further Diploma'),
        ('Post Graduate', 'Post Graduate'),
        ('Senior Certificate', 'Senior Certificate'),
        ('Qual at Nat Sen Cert', 'Qual at Nat Sen Cert'),
        ('Apprenticeship', 'Apprenticeship'),
        ('Post Grad B Degree', 'Post Grad B Degree'),
        ('Post Diploma Diploma', 'Post Diploma Diploma'),
        ('Post-basic Diploma', 'Post-basic Diploma'),
    ]
    highest_tertiary_education = models.CharField("Highest Tertiary Education", max_length=255, choices=TERTIARY_CHOICES, blank=True, null=True)
    tertiary_school_name = models.CharField("School Name (Tertiary)", max_length=255, blank=True, null=True)
    tertiary_year_completed = models.PositiveIntegerField("Year Completed (Tertiary)", blank=True, null=True)

    # Contact
    address_line1 = models.CharField("Address Line 1", max_length=255, blank=True, null=True)
    address_line2 = models.CharField("Address Line 2", max_length=255, blank=True, null=True)
    city = models.CharField("City", max_length=255, blank=True, null=True)
    state_province = models.CharField("State / Province", max_length=255, blank=True, null=True)
    postal_code = models.CharField("Postal / Zip Code", max_length=255, blank=True, null=True)
    phone_number = models.CharField("Learner Phone Number", max_length=255, blank=True, null=True)
    alt_contact_number = models.CharField("Alternative Contact Number", max_length=255, blank=True, null=True)
    email_address = models.EmailField("Learner Email Address", blank=True, null=True)

    # Provider/Programme
    provider_etqa_id = models.CharField("Provider ETQA ID", max_length=255, blank=True, null=True)
    provider_code = models.CharField("Provider Code", max_length=255, blank=True, null=True)
    programme_title = models.CharField("Learning Programme / Course / Qualification Title", max_length=255, blank=True, null=True)
    qualification_code = models.CharField("Qualification Code", max_length=255, blank=True, null=True)
    nqf_level = models.CharField("NQF Level", max_length=255, blank=True, null=True)
    sponsor = models.CharField("Sponsor", max_length=255, blank=True, null=True)
    duration_start_date = models.DateField("Duration - Start Date", blank=True, null=True)
    duration_end_date = models.DateField("Duration - End Date", blank=True, null=True)

    # Consent
    consent_to_process = models.BooleanField(
        "I hereby consent to The Learning Organisation collecting, storing and processing my information for the purpose of registering me with the relevant SETA",
        default=False
    )

    def __str__(self):
        if self.learner:
            return f"LIF for {self.learner}"
        first = getattr(self, 'learner_first_name', '') or ""
        last = getattr(self, 'learner_last_name', '') or ""
        name = (first + " " + last).strip()
        return f"LIF for {name or self.national_id or 'Unknown'}"
    
from django.db import models

class LIFTemplate(models.Model):
    name = models.CharField(max_length=255)
    template_file = models.FileField(upload_to='lif_templates/')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class LIFTemplateFieldMap(models.Model):
    template = models.ForeignKey(LIFTemplate, on_delete=models.CASCADE, related_name='field_mappings')
    placeholder = models.CharField(max_length=255, help_text="e.g. {{learner_surname}} in the Word template")
    lif_field = models.CharField(max_length=255, help_text="e.g. learner_last_name (LIF model field)")

    class Meta:
        unique_together = ('template', 'placeholder')  # Prevents duplicate placeholders per template

    def __str__(self):
        return f"{self.template.name}: {self.placeholder} → {self.lif_field}"
    
from django.db import models

class ExternalProject(models.Model):
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=255)
    # Add other fields as per your SQL Server table

    class Meta:
        managed = False  # Don't let Django manage the table
        db_table = 'Projects'
        app_label = 'core'

class UnitStandard(models.Model):
    title = models.CharField()
    unit_standard_type = models.CharField( blank=True, null=True)
    unit_standard_title = models.CharField(blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    credits = models.IntegerField(blank=True, null=True)
    communications_cat = models.CharField(blank=True, null=True)
    math_cat = models.CharField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_unit_standards'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_unit_standards'
    )

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "Unit Standard"
        verbose_name_plural = "Unit Standards"

class ModuleUnitStandard(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='unit_standards')
    unit_standard = models.ForeignKey(UnitStandard, on_delete=models.CASCADE, related_name='modules')

    class Meta:
        unique_together = ('module', 'unit_standard')
        verbose_name = "Module Unit Standard"
        verbose_name_plural = "Module Unit Standards"

    def __str__(self):
        return f"{self.module} - {self.unit_standard}"

class LearnerAssessment(models.Model):
    title = models.CharField(max_length=255)
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='assessments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='assessments')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assessments')
    project_plan = models.ForeignKey(ProjectPlan, on_delete=models.CASCADE, related_name='assessments')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    attempt_number = models.IntegerField(default=1)
    poe_submitted = models.BooleanField(default=False)
    remediation_submitted = models.BooleanField(default=False)
    formative_assessment = models.BooleanField(default=False)
    summative_assessment = models.BooleanField(default=False)
    assessor = models.ForeignKey(
        LearnerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_assessments'
    )
    assessor2 = models.ForeignKey(
        LearnerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secondary_assessments'
    )
    assessor3 = models.ForeignKey(
        LearnerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tertiary_assessments'
    )
    assessment_date = models.DateField(null=True, blank=True)
    actual_assessment_date = models.DateField(null=True, blank=True)
    actual_assessment_date2 = models.DateField(null=True, blank=True)
    actual_assessment_date3 = models.DateField(null=True, blank=True)
    date_booked_in = models.DateField(null=True, blank=True)
    date_booked_out = models.DateField(null=True, blank=True)
    date_booked_in2 = models.DateField(null=True, blank=True)
    date_booked_out2 = models.DateField(null=True, blank=True)
    date_booked_in3 = models.DateField(null=True, blank=True)
    date_booked_out3 = models.DateField(null=True, blank=True)
    due_date_booked_in = models.DateField(null=True, blank=True)
    due_date_booked_out = models.DateField(null=True, blank=True)
    due_date_booked_in2 = models.DateField(null=True, blank=True)
    due_date_booked_out2 = models.DateField(null=True, blank=True)
    due_date_booked_in3 = models.DateField(null=True, blank=True)
    due_date_booked_out3 = models.DateField(null=True, blank=True)
    end_date2 = models.DateField(null=True, blank=True)
    end_date3 = models.DateField(null=True, blank=True)
    colour = models.CharField(max_length=50, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assessments'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_assessments'
    )

    def __str__(self):
        return f"{self.title} - {self.learner} ({self.module})"

    class Meta:
        verbose_name = "Learner Assessment"
        verbose_name_plural = "Learner Assessments"

class AssessmentUnitStandard(models.Model):
    learner_assessment = models.ForeignKey(
        LearnerAssessment,
        on_delete=models.CASCADE,
        related_name='unit_standard_results'
    )
    unit_standard = models.ForeignKey(
        UnitStandard,
        on_delete=models.CASCADE,
        related_name='assessment_results'
    )
    status_code = models.CharField(max_length=20, blank=True, null=True)
    status_code_abbreviation = models.CharField(max_length=10, blank=True, null=True)
    status_code2 = models.CharField(max_length=20, blank=True, null=True)
    status_code_abbreviation2 = models.CharField(max_length=10, blank=True, null=True)
    status_code3 = models.CharField(max_length=20, blank=True, null=True)
    status_code_abbreviation3 = models.CharField(max_length=10, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    comments2 = models.TextField(blank=True, null=True)
    comments3 = models.TextField(blank=True, null=True)
    unit_standard2 = models.ForeignKey(
        UnitStandard,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assessment_results2'
    )
    unit_standard3 = models.ForeignKey(
        UnitStandard,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assessment_results3'
    )
    colour = models.CharField(max_length=50, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_assessment_unit_standards'
    )

    class Meta:
        unique_together = ('learner_assessment', 'unit_standard')
        verbose_name = "Assessment Unit Standard"
        verbose_name_plural = "Assessment Unit Standards"

    def __str__(self):
        return f"{self.learner_assessment} - {self.unit_standard}"

# Update the existing LearnerModulePOE model to add the learner_assessment relationship
# Add this field to the existing LearnerModulePOE class:
# learner_assessment = models.ForeignKey(
#     LearnerAssessment,
#     on_delete=models.CASCADE,
#     null=True,
#     blank=True,
#     related_name='poes'
# )