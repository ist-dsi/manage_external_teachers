##################
# Utils
##################

from app.models import ExternalTeacher, Semester, ProfessionalCategory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

import csv

# Internationalization
from django.utils.translation import ugettext_lazy as _

from . import constants

import fenixedu

config = fenixedu.FenixEduConfiguration.fromConfigFile()
fenixAPI = fenixedu.FenixEduClient(config)

def get_department(request, acronym):
  departments = request.session['departments']
  for dep in departments:
    if dep['acronym'] == acronym:
      return dep

  return None

def process_action(request, template, external_teachers, view):
  saved = False

  if request.POST['action'] == 'close':
    ids = request.POST.getlist('external_teachers')
    ids_park = request.POST.getlist('park')
    ids_card = request.POST.getlist('card')
    if ids:
      # Close proposals
      for et_id in ids:
        e_teacher = ExternalTeacher.objects.get(id = et_id)
        # Check if authorization to use the park was given
        if et_id in ids_park:
          e_teacher.park = True
        # Check if authorization to use the card was given
        if et_id in ids_card:
          e_teacher.card = True
        # Change professional category
        pro_category = request.POST.getlist('professional_category' + et_id)
        e_teacher.professional_category = ProfessionalCategory.objects.get(id = pro_category[0])
        e_teacher.close(request.user)
        e_teacher.save()
      saved = True
      context = get_context_for_list(external_teachers, view)
      context['saved'] = saved
      return render(request, 'app/sc_opened.html', context)

  elif request.POST['action'] == 'export':
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="proposals_for_fenix_import.csv"'
    writer = csv.writer(response, delimiter=',')

    ids = request.POST.getlist('external_teachers')

    if ids:
      # Write the headers
      writer.writerow([_('TheUser').encode(constants.ENCODING),
        _('Category code').encode(constants.ENCODING),
        _('Department acronym').encode(constants.ENCODING),
        _('Hours').encode(constants.ENCODING),
        _('Engaged').encode(constants.ENCODING)])

      engaged = _('False')

      for et_id in ids:
        e_teacher = ExternalTeacher.objects.get(id = et_id)
        department = get_department(request, e_teacher.department)
        writer.writerow([
          e_teacher.ist_id,
          e_teacher.professional_category.slug.encode(constants.ENCODING),
          department['acronym'].encode(constants.ENCODING),
          e_teacher.hours_per_week,
          engaged.encode(constants.ENCODING)])

      return response

  elif request.POST['action'] == 'export_all_fields':
      # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="proposals.csv"'
    writer = csv.writer(response, delimiter=';')

    ids = request.POST.getlist('external_teachers')

    if ids:
      # Write the headers
      writer.writerow([_('Id').encode(constants.ENCODING),
        _('Professional category').encode(constants.ENCODING),
        _('Hours per week').encode(constants.ENCODING),
        _('Park').encode(constants.ENCODING),
        _('Card').encode(constants.ENCODING),
        _('Department').encode(constants.ENCODING),
        _('Name').encode(constants.ENCODING),
        _('Degree').encode(constants.ENCODING),
        _('Course').encode(constants.ENCODING),
        _('Course manager').encode(constants.ENCODING),
        _('Costs Center').encode(constants.ENCODING),
        _('Notes').encode(constants.ENCODING)])
      for et_id in ids:
        e_teacher = ExternalTeacher.objects.get(id = et_id)
        if e_teacher.park:
          park = _('True')
        else:
          park = _('False')

        if e_teacher.card:
          card = _('True')
        else:
          card = _('False')
        writer.writerow([
          e_teacher.ist_id,
          e_teacher.professional_category.name.encode(constants.ENCODING),
          e_teacher.hours_per_week,
          park.encode(constants.ENCODING),
          card.encode(constants.ENCODING),
          e_teacher.department.encode(constants.ENCODING),
          e_teacher.name.encode(constants.ENCODING),
          e_teacher.degree.encode(constants.ENCODING),
          e_teacher.course.encode(constants.ENCODING),
          e_teacher.course_manager.encode(constants.ENCODING),
          e_teacher.costs_center.encode(constants.ENCODING),
          e_teacher.notes.encode(constants.ENCODING)
          ])


      return response

  elif request.POST['action'] == 'delete':
    ids = request.POST.getlist('external_teachers')
    if ids:
      # Delete proposals
      for et_id in ids:
        e_teacher = ExternalTeacher.objects.get(id = et_id)
        e_teacher.delete()

  context = get_context_for_list(external_teachers, view)
  context['saved'] = saved
  return render(request, template, context)

import json

def open_json_file(filename):
  json_data = open(filename)
  data = json.load(json_data)
  return data

def get_departments(username, data):
  department_members = data['departmentMembers']

  for member in department_members:
    if username == member["username"]:
      return member["departments"]

  return None

def is_scientific_council_member(username, data):
  scientific_council_members = data["scientificCouncilMembers"]

  for member in scientific_council_members:
    if username == member["username"]:
      return True

  return False

def is_admin(username, data):
  admins = data['admins']

  for member in admins:
    if username == member['username']:
      return True

  return False

def get_all_departments(data):
  department_members = data['departmentMembers']
  departments = []

  for member in department_members:
    for dep in member['departments']:
      if dep not in departments:
        departments.append(dep)
  return departments

def get_user_dep_acronyms(request):
  acronyms = []
  for dep in request.session["departments"]:
    acronyms.append(dep['acronym'])
  return acronyms

# Get the context to return to the views that show a list of external teachers
def get_context_for_list(external_teachers, view):
  context = constants.POSSIBLE_ACTIONS[view]
  context['external_teachers'] = external_teachers
  context['current_semester'] = Semester.get_or_create_current()
  context['semesters'] = Semester.objects.all()
  return context

def get_external_teachers_list(request, is_closed, filter_by_dep):
  semester_param = request.GET.get('semester')

  if filter_by_dep:
    external_teachers = ExternalTeacher.objects.filter(is_closed = is_closed,
                        department__in = request.session['dep_acronyms'])
  else:
    external_teachers = ExternalTeacher.objects.filter(is_closed = is_closed)

  if semester_param:
    semester = int(semester_param)

    if semester > 0:
      external_teachers = external_teachers.filter(semester = semester)

  return external_teachers

def authenticate_by_fenixedu_code(request, client, code):
  json_data = open_json_file(constants.JSON_FILE)

  user = authenticate(request=request, client=client, code=code)

  if user is not None:
    username = user.username
    if is_admin(username, json_data) or is_scientific_council_member(username, json_data):
      departments = get_all_departments(json_data)
    else:
      departments = get_departments(user.username, json_data)

    can_login = False

    if is_admin(username, json_data):
      request.session['departments'] = departments
      request.session['is_department_member'] = True
      request.session['dep_acronyms'] = get_user_dep_acronyms(request)
      request.session['is_scientific_council_member'] = True
      can_login = True

    # Check if it's a department member
    elif departments is not None:
      request.session['departments'] = departments
      request.session['is_department_member'] = True
      request.session['dep_acronyms'] = get_user_dep_acronyms(request)
      can_login = True

    # Check if it's a scientific council member
    if is_scientific_council_member(username, json_data):
      request.session['is_scientific_council_member'] = True
      can_login = True

    if user.is_active and can_login:
      login(request, user)

def get_user_display(user):
  return user.get_full_name() + ' (' + user.username + ')'

def get_pro_category_dict(teacher):
  if teacher.professional_category:
    category = teacher.professional_category
    return {'id': category.id, 'slug': category.slug, 'name': category.name}
  else:
    return {}

def get_typology_dict(teacher):
  if teacher.typology:
    typology = teacher.typology
    return {'id': typology.id, 'name': typology.name}
  else:
    return {}
