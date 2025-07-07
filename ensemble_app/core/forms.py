from datetime import date
from django import forms
from .models import AdobeForm
from django.db.models import Q
from django.forms import modelformset_factory
from django.forms.widgets import SelectDateWidget
from .models import SLA, SLA_Qualifications, BillingHistory, Learner, Customer
from dal import autocomplete
from django import forms
from .models import Group, SETA, Service, LearnerQualification,LearnerRole
from .models import ProjectPlan, SessionDate, Venue, VenueBooking, Module, AdobeForm,AdobeFormAnnexture, LearnerModulePOE
from .models import Service, Module, Service_Module
from django import forms
from .models import ModulePOETemplate, ModulePOEAnnexture


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'gl_code', 'saqa_id', 'shorthand', 'unit_price', 'requires_summative_exam']

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['name', 'code']

class ServiceModuleForm(forms.ModelForm):
    class Meta:
        model = Service_Module
        fields = ['service', 'module']

class GroupCreateForm(forms.ModelForm):
    sla_qualifications = forms.ModelMultipleChoiceField(
        queryset=SLA_Qualifications.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select the SLA Qualifications for this group"
    )

    class Meta:
        model = Group
        fields = ['name', 'projectcode', 'service', 'seta', 'sla_qualifications', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['sla_qualifications'].queryset = SLA_Qualifications.objects.filter(
                service=self.instance.service
            )
        self.fields['service'].widget.attrs.update({'class': 'form-control'})
        self.fields['seta'].widget.attrs.update({'class': 'form-control'})

class SETAForm(forms.ModelForm):
    class Meta:
        model = SETA
        fields = ['name']

class AssignLearnerQualificationForm(forms.Form):
    learner = forms.ModelChoiceField(
        queryset=Learner.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Learner"
    )
    sla_qualification = forms.ModelChoiceField(
        queryset=SLA_Qualifications.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="SLA Qualification"
    )

    def clean(self):
        cleaned_data = super().clean()
        learner = cleaned_data.get('learner')
        sla_qualification = cleaned_data.get('sla_qualification')
        if learner and sla_qualification:
            exists = LearnerQualification.objects.filter(
                learner=learner,
                sla_qualification=sla_qualification
            ).exists()
            if exists:
                raise forms.ValidationError("This learner is already assigned to this SLA Qualification.")
        return cleaned_data

class SLAForm(forms.ModelForm):
    BILLING_DAY_CHOICES = [
        ('First', 'First'),
        ('Last',  'Last'),
    ]

    sla_reference   = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="SLA reference"
    )
    customer        = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Customer"
    )
    start_date      = forms.DateField(
        widget=SelectDateWidget(
            years=range(date.today().year, date.today().year + 6),
            empty_label=("Year", "Month", "Day"),
            attrs={'class': 'form-select d-inline w-auto'}
        ),
        label="Start date"
    )
    end_date        = forms.DateField(
        widget=SelectDateWidget(
            years=range(date.today().year, date.today().year + 6),
            empty_label=("Year", "Month", "Day"),
            attrs={'class': 'form-select d-inline w-auto'}
        ),
        label="End date"
    )
    end_client_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="End client name"
    )
    num_tranches    = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Num tranches"
    )
    billing_day     = forms.ChoiceField(
        choices=BILLING_DAY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Billing day"
    )

    class Meta:
        model = SLA
        fields = [
            'sla_reference',
            'customer',
            'start_date',
            'end_date',
            'end_client_name',
            'num_tranches',
            'billing_day',
        ]


class SLAQualificationForm(forms.ModelForm):
    EMPLOYMENT_STATUS_CHOICES = [
        ('employed',   'Employed'),
        ('unemployed', 'Unemployed'),
    ]

    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    getting_data = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    getting_laptop = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    lunch_provided = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    venue_location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Venue (location)",
    )

    class Meta:
        model = SLA_Qualifications
        fields = [
            'service',
            'learner_count',
            'employment_status',
            'getting_data',
            'getting_laptop',
            'lunch_provided',
            'venue_location',
            'learnership',
            'recruitment',
            'hosting',
            'technology',
            'venue_cost',
            'stipends',
            'consulting',
        ]


SLAQualificationFormSet = modelformset_factory(
    SLA_Qualifications,
    form=SLAQualificationForm,
    extra=1,
    can_delete=True,
)

class TrancheBillingForm(forms.Form):
    invoice_type  = forms.CharField(widget=forms.HiddenInput())
    due_date      = forms.DateField(
        label="Due date",
        widget=forms.DateInput(attrs={'type': 'date','class':'form-control'}),
        required=False
    )
    total_amount  = forms.DecimalField(
        label="Tranche total (R)",
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'step':'0.01','class':'form-control'})
    )

    def __init__(self, *args, sla=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sla is None:
            raise ValueError("TrancheBillingForm requires sla=")
        self.sla = sla
        for qual in SLA_Qualifications.objects.filter(sla=sla).select_related('service'):
            self.fields[f"qual_{qual.id}"] = forms.DecimalField(
                label=f"{qual.service.name} (R)",
                max_digits=12, decimal_places=2,
                required=False,
                widget=forms.NumberInput(attrs={'step':'0.01','class':'form-control'})
            )

    def clean(self):
        cleaned = super().clean()
        total   = cleaned.get('total_amount') or 0
        allocated = sum(
            cleaned.get(f"qual_{q.id}") or 0
            for q in SLA_Qualifications.objects.filter(sla=self.sla)
        )
        if allocated > total:
            self.add_error(
                'total_amount',
                f"Sum of qualification amounts (R{allocated:.2f}) exceeds tranche total (R{total:.2f})."
            )
        return cleaned
        
class QualificationLearnersForm(forms.Form):
    learners = forms.ModelMultipleChoiceField(
        queryset=Learner.objects.none(),  # set in __init__
        widget=autocomplete.ModelSelect2Multiple(
            url='learner-autocomplete',
            attrs={'data-placeholder': 'Search by name or ID…'}
        ),
        label="Select Learners",
        required=False,
    )

    def __init__(self, *args, sla_qual=None, **kwargs):
        """
        sla_qual: instance of SLA_Qualifications to know max learner_count
        """
        super().__init__(*args, **kwargs)
        if sla_qual is None:
            raise ValueError("QualificationLearnersForm requires sla_qual=")
        self.sla_qual = sla_qual

        # allow all learners to be searched
        self.fields['learners'].queryset = Learner.objects.all()
        # show help text:
        self.fields['learners'].help_text = f"Up to {sla_qual.learner_count} learners."

    def clean_learners(self):
        learners = self.cleaned_data.get('learners')
        if len(learners) > self.sla_qual.learner_count:
            raise forms.ValidationError(
                f"Cannot select more than {self.sla_qual.learner_count} learners."
            )
        return learners

class LearnerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Learner.objects.all()
        if self.q:
            qs = qs.filter(
                Q(FirstName__icontains=self.q)
                | Q(Surname__icontains=self.q)
                | Q(IDNumber__icontains=self.q)
            )
        return qs

class ProjectPlanForm(forms.ModelForm):
    class Meta:
        model = ProjectPlan
        fields = '__all__'

class SessionDateForm(forms.ModelForm):
    class Meta:
        model = SessionDate
        fields = '__all__'

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = '__all__'

from django import forms
from .models import VenueBooking, SessionDate, LearnerRole

class VenueBookingForm(forms.ModelForm):
    session_dates = forms.ModelMultipleChoiceField(
        queryset=SessionDate.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Select multiple sessions to book together (hold Ctrl/Cmd)."
    )

    class Meta:
        model = VenueBooking
        fields = [
            'session_date', 'venue', 'start_datetime', 'end_datetime',
            'booking_purpose', 'facilitator', 'status',
            'num_learners', 'num_learners_lunch'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'facilitator' in self.fields:
            self.fields['facilitator'].queryset = LearnerRole.objects.filter(role__name='Facilitator')
            self.fields['num_learners'].disabled = True
        # Prepopulate num_learners if session_date is set and not already filled
        if not self.initial.get('num_learners'):
            session_date_id = self.initial.get('session_date') or self.data.get('session_date')
            if session_date_id:
                from .views import get_default_num_learners_for_session
                default = get_default_num_learners_for_session(session_date_id)
                if default:
                    self.fields['num_learners'].initial = default
                    
class AdobeFormUploadForm(forms.ModelForm):
    class Meta:
        model = AdobeForm
        fields = ['name', 'pdf']

class AdobeFormFilledSubmissionForm(forms.Form):
    filled_pdf = forms.FileField(label="Upload filled PDF form")
    your_email = forms.EmailField(label="Your Email")
    recipient_email = forms.EmailField(label="Send To Email")

class AnnextureTemplateForm(forms.ModelForm):
    class Meta:
        model = AdobeFormAnnexture
        fields = ['name', 'required', 'order']

class FacilitatorPOEUploadForm(forms.ModelForm):
    class Meta:
        model = AdobeForm
        fields = ['name', 'pdf']

    annextures = forms.CharField(
        widget=forms.Textarea,
        help_text="Enter annexture names, one per line (e.g. Activity 1, Activity 2)",
        required=False
    )

    def clean_annextures(self):
        data = self.cleaned_data['annextures']
        if data:
            return [x.strip() for x in data.split('\n') if x.strip()]
        return []

class LearnerLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

from django import forms
from .models import LearnerModulePOE

# ...existing code...

class POESubmissionForm(forms.ModelForm):
    class Meta:
        model = LearnerModulePOE
        fields = ['poe_file']

    def __init__(self, *args, **kwargs):
        self.learner = kwargs.pop('learner', None)
        self.learner_qualification = kwargs.pop('learner_qualification', None)
        self.module = kwargs.pop('module', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.learner and self.learner_qualification and self.module:
            exists = LearnerModulePOE.objects.filter(
                learner=self.learner,
                learner_qualification=self.learner_qualification,
                module=self.module
            ).exists()
            if exists:
                raise forms.ValidationError("You have already submitted a POE for this module.")
        return cleaned_data

class FacilitatorPOEFeedbackForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=(
            ('competent', 'Competent'),
            ('not_yet_competent', 'Not Yet Competent'),
        ),
        widget=forms.RadioSelect,
        label="Assessment"
    )

    class Meta:
        model = LearnerModulePOE
        fields = ['status', 'feedback']

class ModulePOETemplateForm(forms.ModelForm):
    class Meta:
        model = ModulePOETemplate
        fields = ['module', 'template_file']
        widgets = {
            'module': forms.Select(attrs={'class': 'form-select'}),
            'template_file': forms.FileInput(attrs={'class': 'form-control'})
        }

class ModulePOEAnnextureForm(forms.ModelForm):
    class Meta:
        model = ModulePOEAnnexture
        fields = ['name', 'required']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class POESubmissionForm(forms.Form):
    module_id = forms.IntegerField(widget=forms.HiddenInput())
    qualification_id = forms.IntegerField(widget=forms.HiddenInput())
    poe_file = forms.FileField(label='POE Document')

    def __init__(self, *args, **kwargs):
        self.template = kwargs.pop('template', None)
        super().__init__(*args, **kwargs)

        # Dynamically add annexture fields if template is provided
        if self.template:
            for annexture in self.template.required_annextures.all():
                self.fields[f'annexture_{annexture.id}'] = forms.FileField(
                    label=annexture.name,
                    required=annexture.required
                )

    def clean(self):
        cleaned_data = super().clean()
        errors = []

        # Check main POE file
        if not cleaned_data.get('poe_file'):
            errors.append('POE file is required.')

        # Check required annextures
        if self.template:
            for annexture in self.template.required_annextures.filter(required=True):
                if not self.files.get(f'annexture_{annexture.id}'):
                    errors.append(f"Annexture required: {annexture.name}")

        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data


from django import forms
from .models import LIF, LIFTemplate, LIFTemplateFieldMap

class LIFForm(forms.ModelForm):
    consent_to_process = forms.BooleanField(
        label="I hereby consent to The Learning Organisation collecting, storing and processing my information for the purpose of registering me with the relevant SETA",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_consent_to_process'}),
    )

    class Meta:
        model = LIF
        exclude = ['learner']
        widgets = {
            'alternative_id_type': forms.Select(choices=[
                ('', '---------'),
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
            ]),
            'learner_birth_date': forms.DateInput(attrs={'type': 'date'}),
            'secondary_year_completed': forms.NumberInput(attrs={'min': 1975, 'max': 2025}),
            'tertiary_year_completed': forms.NumberInput(attrs={'min': 1975, 'max': 2025}),
            'duration_start_date': forms.DateInput(attrs={'type': 'date'}),
            'duration_end_date': forms.DateInput(attrs={'type': 'date'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal / Zip Code'}),
        }

    def clean_consent_to_process(self):
        value = self.cleaned_data.get('consent_to_process')
        if not value:
            raise forms.ValidationError("You must consent to processing for registration.")
        return value

LIF_FIELD_CHOICES = [
    ('learner', 'Learner (FK)'),
    ('national_id', 'National ID'),
    ('alternative_id', 'Alternative ID'),
    ('alternative_id_type', 'Alternative ID Type'),
    ('equity_code', 'Equity Code'),
    ('nationality_code', 'Nationality Code'),
    ('gender_code', 'Gender Code'),
    ('citizen_resident_status_code', 'Citizen Resident Status Code'),
    ('home_language_code', 'Home Language Code'),
    ('province_code', 'Province Code'),
    ('disability_status_code', 'Disability Status Code'),
    ('socio_economic_status_code', 'Socio-economic Status Code'),
    ('learner_title', 'Learner Title'),
    ('learner_birth_date', 'Learner Birth Date'),
    ('learner_first_name', 'Learner First Name'),
    ('learner_middle_name', 'Learner Middle Name'),
    ('learner_last_name', 'Learner Last Name'),
    ('learner_previous_last_name', 'Learner Previous Last Name'),
    ('learner_current_occupation', 'Learner Current Occupation'),
    ('years_in_occupation', 'Years in Occupation'),
    ('employer', 'Employer'),
    ('highest_secondary_education', 'Highest Secondary Education'),
    ('secondary_school_name', 'School Name (Secondary)'),
    ('secondary_year_completed', 'Year Completed (Secondary)'),
    ('percentage_maths', 'Percentage - Maths'),
    ('percentage_first_language', 'Percentage - 1st Language'),
    ('percentage_second_language', 'Percentage - 2nd Language'),
    ('highest_tertiary_education', 'Highest Tertiary Education'),
    ('tertiary_school_name', 'School Name (Tertiary)'),
    ('tertiary_year_completed', 'Year Completed (Tertiary)'),
    ('address_line1', 'Address Line 1'),
    ('address_line2', 'Address Line 2'),
    ('city', 'City'),
    ('state_province', 'State / Province'),
    ('phone_number', 'Learner Phone Number'),
    ('alt_contact_number', 'Alternative Contact Number'),
    ('email_address', 'Learner Email Address'),
    ('provider_etqa_id', 'Provider ETQA ID'),
    ('provider_code', 'Provider Code'),
    ('programme_title', 'Learning Programme / Course / Qualification Title'),
    ('qualification_code', 'Qualification Code'),
    ('nqf_level', 'NQF Level'),
    ('sponsor', 'Sponsor'),
    ('duration_start_date', 'Duration - Start Date'),
    ('duration_end_date', 'Duration - End Date'),
    ('consent_to_process', 'Consent to Process'),
    ('postal_code', 'Postal / Zip Code'),
]

PLACEHOLDER_CHOICES = [
    ('{{learner}}', '{{learner}}'),
    ('{{national_id}}', '{{national_id}}'),
    ('{{alternative_id}}', '{{alternative_id}}'),
    ('{{alternative_id_type}}', '{{alternative_id_type}}'),
    ('{{equity_code}}', '{{equity_code}}'),
    ('{{nationality_code}}', '{{nationality_code}}'),
    ('{{gender_code}}', '{{gender_code}}'),
    ('{{citizen_resident_status_code}}', '{{citizen_resident_status_code}}'),
    ('{{home_language_code}}', '{{home_language_code}}'),
    ('{{province_code}}', '{{province_code}}'),
    ('{{disability_status_code}}', '{{disability_status_code}}'),
    ('{{socio_economic_status_code}}', '{{socio_economic_status_code}}'),
    ('{{learner_title}}', '{{learner_title}}'),
    ('{{learner_birth_date}}', '{{learner_birth_date}}'),
    ('{{learner_first_name}}', '{{learner_first_name}}'),
    ('{{learner_middle_name}}', '{{learner_middle_name}}'),
    ('{{learner_last_name}}', '{{learner_last_name}}'),
    ('{{learner_previous_last_name}}', '{{learner_previous_last_name}}'),
    ('{{learner_current_occupation}}', '{{learner_current_occupation}}'),
    ('{{years_in_occupation}}', '{{years_in_occupation}}'),
    ('{{employer}}', '{{employer}}'),
    ('{{highest_secondary_education}}', '{{highest_secondary_education}}'),
    ('{{secondary_school_name}}', '{{secondary_school_name}}'),
    ('{{secondary_year_completed}}', '{{secondary_year_completed}}'),
    ('{{percentage_maths}}', '{{percentage_maths}}'),
    ('{{percentage_first_language}}', '{{percentage_first_language}}'),
    ('{{percentage_second_language}}', '{{percentage_second_language}}'),
    ('{{highest_tertiary_education}}', '{{highest_tertiary_education}}'),
    ('{{tertiary_school_name}}', '{{tertiary_school_name}}'),
    ('{{tertiary_year_completed}}', '{{tertiary_year_completed}}'),
    ('{{address_line1}}', '{{address_line1}}'),
    ('{{address_line2}}', '{{address_line2}}'),
    ('{{city}}', '{{city}}'),
    ('{{state_province}}', '{{state_province}}'),
    ('{{phone_number}}', '{{phone_number}}'),
    ('{{alt_contact_number}}', '{{alt_contact_number}}'),
    ('{{email_address}}', '{{email_address}}'),
    ('{{provider_etqa_id}}', '{{provider_etqa_id}}'),
    ('{{provider_code}}', '{{provider_code}}'),
    ('{{programme_title}}', '{{programme_title}}'),
    ('{{qualification_code}}', '{{qualification_code}}'),
    ('{{nqf_level}}', '{{nqf_level}}'),
    ('{{sponsor}}', '{{sponsor}}'),
    ('{{duration_start_date}}', '{{duration_start_date}}'),
    ('{{duration_end_date}}', '{{duration_end_date}}'),
    ('{{consent_to_process}}', '{{consent_to_process}}'),
    ('{{postal_code}}', '{{postal_code}}'),
    # Gender placeholders for crosses
    ('{{gender_male}}', '{{gender_male}}'),
    ('{{gender_female}}', '{{gender_female}}'),
    # Below 35 years placeholders
    ('{{below_35_yes}}', '{{below_35_yes}}'),
    ('{{below_35_no}}', '{{below_35_no}}'),
    # Equity placeholders
    ('{{equity_african}}', '{{equity_african}}'),
    ('{{equity_coloured}}', '{{equity_coloured}}'),
    ('{{equity_indian}}', '{{equity_indian}}'),
    ('{{equity_white}}', '{{equity_white}}'),
    # Disability placeholders
    ('{{disability_sight}}', '{{disability_sight}}'),
    ('{{disability_hearing}}', '{{disability_hearing}}'),
    ('{{disability_communication}}', '{{disability_communication}}'),
    ('{{disability_physical}}', '{{disability_physical}}'),
    ('{{disability_intellectual}}', '{{disability_intellectual}}'),
    ('{{disability_emotional}}', '{{disability_emotional}}'),
    ('{{disability_multiple}}', '{{disability_multiple}}'),
    ('{{disability_unspecified}}', '{{disability_unspecified}}'),
    ('{{disability_none}}', '{{disability_none}}'),
    # Citizen status placeholders
    ('{{citizen_sa}}', '{{citizen_sa}}'),
    ('{{citizen_dual}}', '{{citizen_dual}}'),
    ('{{citizen_other}}', '{{citizen_other}}'),
    ('{{citizen_permanent}}', '{{citizen_permanent}}'),
    ('{{citizen_unknown}}', '{{citizen_unknown}}'),
    # Nationality placeholders
    ('{{nationality_afrikaans}}', '{{nationality_afrikaans}}'),
    ('{{nationality_english}}', '{{nationality_english}}'),
    ('{{nationality_ndebele}}', '{{nationality_ndebele}}'),
    ('{{nationality_sepedi}}', '{{nationality_sepedi}}'),
    ('{{nationality_sesotho}}', '{{nationality_sesotho}}'),
    ('{{nationality_setswana}}', '{{nationality_setswana}}'),
    ('{{nationality_siswati}}', '{{nationality_siswati}}'),
    ('{{nationality_tshivenda}}', '{{nationality_tshivenda}}'),
    ('{{nationality_isixhosa}}', '{{nationality_isixhosa}}'),
    ('{{nationality_xitsonga}}', '{{nationality_xitsonga}}'),
    ('{{nationality_isizulu}}', '{{nationality_isizulu}}'),
    ('{{nationality_sasl}}', '{{nationality_sasl}}'),
    ('{{nationality_other}}', '{{nationality_other}}'),
    ('{{nationality_unknown}}', '{{nationality_unknown}}'),
    # Home language placeholders (same as nationality)
    ('{{home_language_afrikaans}}', '{{home_language_afrikaans}}'),
    ('{{home_language_english}}', '{{home_language_english}}'),
    ('{{home_language_ndebele}}', '{{home_language_ndebele}}'),
    ('{{home_language_sepedi}}', '{{home_language_sepedi}}'),
    ('{{home_language_sesotho}}', '{{home_language_sesotho}}'),
    ('{{home_language_setswana}}', '{{home_language_setswana}}'),
    ('{{home_language_siswati}}', '{{home_language_siswati}}'),
    ('{{home_language_tshivenda}}', '{{home_language_tshivenda}}'),
    ('{{home_language_isixhosa}}', '{{home_language_isixhosa}}'),
    ('{{home_language_xitsonga}}', '{{home_language_xitsonga}}'),
    ('{{home_language_isizulu}}', '{{home_language_isizulu}}'),
    ('{{home_language_sasl}}', '{{home_language_sasl}}'),
    ('{{home_language_other}}', '{{home_language_other}}'),
    ('{{home_language_unknown}}', '{{home_language_unknown}}'),
    # Province placeholders
    ('{{province_western_cape}}', '{{province_western_cape}}'),
    ('{{province_eastern_cape}}', '{{province_eastern_cape}}'),
    ('{{province_northern_cape}}', '{{province_northern_cape}}'),
    ('{{province_free_state}}', '{{province_free_state}}'),
    ('{{province_kwazulu_natal}}', '{{province_kwazulu_natal}}'),
    ('{{province_north_west}}', '{{province_north_west}}'),
    ('{{province_gauteng_jhb}}', '{{province_gauteng_jhb}}'),
    ('{{province_gauteng_pta}}', '{{province_gauteng_pta}}'),
    ('{{province_mpumalanga}}', '{{province_mpumalanga}}'),
    ('{{province_limpopo}}', '{{province_limpopo}}'),
    ('{{province_outside_sa}}', '{{province_outside_sa}}'),
    ('{{province_national}}', '{{province_national}}'),
    # Socio-economic status placeholders
    ('{{socio_employed}}', '{{socio_employed}}'),
    ('{{socio_unemployed_seeking}}', '{{socio_unemployed_seeking}}'),
    ('{{socio_not_working_not_looking}}', '{{socio_not_working_not_looking}}'),
    ('{{socio_homemaker}}', '{{socio_homemaker}}'),
    ('{{socio_student}}', '{{socio_student}}'),
    ('{{socio_pensioner}}', '{{socio_pensioner}}'),
    ('{{socio_disabled}}', '{{socio_disabled}}'),
    ('{{socio_no_wish_to_work}}', '{{socio_no_wish_to_work}}'),
    ('{{socio_not_working_nec}}', '{{socio_not_working_nec}}'),
    ('{{socio_aged_under_15}}', '{{socio_aged_under_15}}'),
    ('{{socio_institution}}', '{{socio_institution}}'),
    ('{{socio_unspecified}}', '{{socio_unspecified}}'),
    # Alternative ID type placeholders
    ('{{alt_id_saqa}}', '{{alt_id_saqa}}'),
    ('{{alt_id_passport}}', '{{alt_id_passport}}'),
    ('{{alt_id_driver}}', '{{alt_id_driver}}'),
    ('{{alt_id_temp_id}}', '{{alt_id_temp_id}}'),
    ('{{alt_id_none}}', '{{alt_id_none}}'),
    ('{{alt_id_unknown}}', '{{alt_id_unknown}}'),
    ('{{alt_id_student}}', '{{alt_id_student}}'),
    ('{{alt_id_work_permit}}', '{{alt_id_work_permit}}'),
    ('{{alt_id_employee}}', '{{alt_id_employee}}'),
    ('{{alt_id_birth_cert}}', '{{alt_id_birth_cert}}'),
    ('{{alt_id_hsrc}}', '{{alt_id_hsrc}}'),
    ('{{alt_id_etqa}}', '{{alt_id_etqa}}'),
    ('{{alt_id_refugee}}', '{{alt_id_refugee}}'),
    # Highest tertiary education placeholders
    ('{{tertiary_national_certificate}}', '{{tertiary_national_certificate}}'),
    ('{{tertiary_national_diploma}}', '{{tertiary_national_diploma}}'),
    ('{{tertiary_first_degree}}', '{{tertiary_first_degree}}'),
    ('{{tertiary_post_doctoral}}', '{{tertiary_post_doctoral}}'),
    ('{{tertiary_doctoral}}', '{{tertiary_doctoral}}'),
    ('{{tertiary_professional}}', '{{tertiary_professional}}'),
    ('{{tertiary_honours}}', '{{tertiary_honours}}'),
    ('{{tertiary_higher_diploma}}', '{{tertiary_higher_diploma}}'),
    ('{{tertiary_masters_diploma}}', '{{tertiary_masters_diploma}}'),
    ('{{tertiary_national_higher}}', '{{tertiary_national_higher}}'),
    ('{{tertiary_further_diploma}}', '{{tertiary_further_diploma}}'),
    ('{{tertiary_post_graduate}}', '{{tertiary_post_graduate}}'),
    ('{{tertiary_senior_certificate}}', '{{tertiary_senior_certificate}}'),
    ('{{tertiary_qual_nat_sen_cert}}', '{{tertiary_qual_nat_sen_cert}}'),
    ('{{tertiary_apprenticeship}}', '{{tertiary_apprenticeship}}'),
    ('{{tertiary_post_grad_b_degree}}', '{{tertiary_post_grad_b_degree}}'),
    ('{{tertiary_post_diploma_diploma}}', '{{tertiary_post_diploma_diploma}}'),
    ('{{tertiary_post_basic_diploma}}', '{{tertiary_post_basic_diploma}}'),
]

class LIFTemplateFieldMapForm(forms.ModelForm):
    placeholder = forms.ChoiceField(
        choices=PLACEHOLDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    lif_field = forms.ChoiceField(
        choices=LIF_FIELD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = LIFTemplateFieldMap
        fields = ['placeholder', 'lif_field']

class LIFTemplateUploadForm(forms.ModelForm):
    class Meta:
        model = LIFTemplate
        fields = ['name', 'template_file', 'description']