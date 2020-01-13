##################
# Forms
##################

# Form widgets
from django.forms import ModelForm, Textarea, Select, TextInput

# Internationalization
from django.utils.translation import ugettext_lazy as _

#Models
from app.models import ExternalTeacher, Semester, Typology

class ExternalTeacherForm(ModelForm):

    def __init__(self, *args, **kwargs):
        arg = kwargs.pop('request', None)
        super(ExternalTeacherForm, self).__init__(*args, **kwargs)
        session = arg.session
        deps = session['departments']
        dep_choices = [(d['acronym'], d['acronym']) for d in deps]
        self.fields['department'].widget = Select(choices=dep_choices)

        typologies = Typology.objects.all()
        typology_choices = [(0, _('select_typology'))] + [(t.id, t.name) for t in typologies]
        self.fields['typology'].widget = Select(choices=typology_choices)


        # Labels internationalization
        self.fields['ist_id'].label = _('IST ID')
        self.fields['name'].label = _('name')
        self.fields['semester'].label = _('semester')
        self.fields['hours_per_week'].label = _('hours_per_week')
        self.fields['department'].label = _('department')
        self.fields['typology'].label = _('typology')
        self.fields['degree'].label = _('degree')
        self.fields['course'].label = _('course')
        self.fields['course_manager'].label = _('course_manager')
        self.fields['costs_center'].label = _('costs_center')
        self.fields['notes'].label = _('notes')

        instance = kwargs.pop('instance', None)
        if instance:
            semester_initial = instance.id
        else:
            semester_initial = Semester.get_or_create_current().id

        semester_choices = [(s.id, s.get_display()) for s in Semester.get_current_and_future()]
        
        self.fields['semester'].initial = semester_initial
        self.fields['semester'].widget = Select(choices=semester_choices)

    class Meta:
        model = ExternalTeacher
        fields = ['ist_id', 'name', 'semester', 'hours_per_week',
            'department', 'typology', 'degree', 'course',
            'course_manager', 'costs_center', 'notes']
        widgets = {'notes' : Textarea(), 'name' : TextInput(attrs={'readonly' : 'true'})}
