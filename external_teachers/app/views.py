# -*- coding: utf-8 -*-
#App views

# Http response
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import json

# Models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from app.models import ExternalTeacher, Semester, ProfessionalCategory

# Internationalization
from django.utils.translation import ugettext_lazy as _

# Utils
from datetime import datetime
import csv
import os
from django.core import serializers

# Custom modules
from . import constants
from . import utils
from . import forms
from . import name_service

import fenixedu

config = fenixedu.FenixEduConfiguration.fromConfigFile()
fenixAPI = fenixedu.FenixEduClient(config)

##################
# Public views
##################

# Entry point
def index(request):
	url = fenixAPI.get_authentication_url()
	code = request.GET.get('code', None)

	if code is not None and not request.user.is_authenticated():
		utils.authenticate_by_fenixedu_code(request, fenixAPI, code)

	context = {'auth_url' : url, 'is_department_member' : 'is_department_member' in request.session,
			'is_scientific_council_member' : 'is_scientific_council_member' in request.session}

	return render(request, 'app/index.html', context)

# Get the name with a given ist id
def name(request):
        import f
	name = f.from_ist_id(request.GET['username']).partyName.encode("iso-8859-1")

	return HttpResponse(name)

def about(request):
	about = fenixAPI.get_about()
	context = {'about' : about['institutionName']}
	return render(request, 'app/about.html', context)

def user_logout(request):
	logout(request)
	return index(request)

##################
# Private views
##################

# Get the name with a given ist id
@login_required
def name(request):
	name = name_service.get_name_by_istid(request)
	return HttpResponse(name)

@login_required
def sc_opened(request):
	external_teachers = utils.get_external_teachers_list(request, is_closed = False,
																									filter_by_dep = False)
	saved = False
	template = 'app/sc_opened.html'

	if request.method == 'POST':
		return utils.process_action(request, template, external_teachers, 'sc_opened')

	context = utils.get_context_for_list(external_teachers, 'sc_opened')

	context['saved'] = False
	context['pro_categories'] = ProfessionalCategory.objects.all()
	return render(request, template, context)

@login_required
def sc_closed(request):
	template = 'app/sc_closed.html'
	external_teachers = utils.get_external_teachers_list(request, is_closed = True,
																									filter_by_dep = False)

	if request.method == 'POST':
		return utils.process_action(request, template, external_teachers, 'sc_closed')

	context = utils.get_context_for_list(external_teachers, 'sc_closed')
	return render(request, template, context)

@login_required
def dep_opened(request):
	external_teachers = utils.get_external_teachers_list(request, is_closed = False,
																									filter_by_dep = True)
	template = 'app/dep_opened.html'

	if request.method == 'POST':
		return utils.process_action(request, template, external_teachers, 'dep_opened')

	context = utils.get_context_for_list(external_teachers, 'dep_opened')
	context['can_edit'] = True
	return render(request, template, context)

@login_required
def dep_closed(request):
	template = 'app/dep_closed.html'
	external_teachers = utils.get_external_teachers_list(request, is_closed = True,
																									filter_by_dep = True)

	if request.method == 'POST':
		return utils.process_action(request, template, external_teachers, 'dep_closed')

	context = utils.get_context_for_list(external_teachers, 'dep_closed')
	return render(request, template, context)

@login_required
def dep_prop_new(request):
	if request.method == 'POST':
		form = forms.ExternalTeacherForm(request.POST, request=request)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect('/professoresexternos/dep_opened/')
	else:
		form = forms.ExternalTeacherForm(request=request)

	context = {'form' : form}
	return render(request, 'app/external_teacher_form.html', context)

@login_required
def edit(request, pk):
	template = 'app/dep_opened.html'
	external_teacher = ExternalTeacher.objects.get(id=pk)

	# Its not supposed to try to edit a closed one
	if external_teacher.is_closed:
		return render(request, template, {'error' : 'ERROR: This proposal is closed'})

	if request.method == 'POST':
		form = forms.ExternalTeacherForm(request.POST, request=request, instance=external_teacher)
		if form.is_valid():
			form.save()
			return HttpResponseRedirect('/professoresexternos/dep_opened/')
	else:
		form = forms.ExternalTeacherForm(request=request, instance=external_teacher)

	context = {'form' : form}
	return render(request, 'app/external_teacher_form.html', context)

@login_required
def change_park(request, pk):
	value = request.GET.get("value")
	external_teacher = ExternalTeacher.objects.get(id=pk)

	if value == 'true':
		external_teacher.park = True
		response = _('Yes')
	else:
		external_teacher.park = False
		response = _('No')

	external_teacher.save()

	return HttpResponse(response)

@login_required
def change_card(request, pk):
	value = request.GET.get("value")
	external_teacher = ExternalTeacher.objects.get(id=pk)

	if value == 'true':
		external_teacher.card = True
		response = _('Yes')
	else:
		external_teacher.card = False
		response = _('No')

	external_teacher.save()

	return HttpResponse(response)

@login_required
def change_professional_category(request, pk):
	value = int(request.GET.get("value"))
	external_teacher = ExternalTeacher.objects.get(id=pk)

	if value < 0:
		category = None
	else:
		category = ProfessionalCategory.objects.get(id=value)
	
	external_teacher.professional_category = category

	external_teacher.save()

	return HttpResponse(utils.get_pro_category_dict(external_teacher))

@login_required
def get_external_teacher(request, pk):
	external_teacher = ExternalTeacher.objects.get(id=pk)
	if external_teacher.close_date:
		close_date = external_teacher.close_date.strftime("%d/%m/%Y %H:%M")
	else:
		close_date = ''
	if external_teacher.closed_by:
		closed_by = utils.get_user_display(external_teacher.closed_by)
	else:
		closed_by = ''
	response = {'id' : external_teacher.id,
				'ist_id' : external_teacher.ist_id,
				'name' : external_teacher.name,
				'semester' : {
					'id' : external_teacher.semester.id,
					'display' : external_teacher.semester.get_display()
				},
				'is_closed' : external_teacher.is_closed,
				'close_date' : close_date,
				'closed_by': closed_by,
				'professional_category' : utils.get_pro_category_dict(external_teacher),
				'typology' : utils.get_typology_dict(external_teacher),
				'hours_per_week' : '%.2f' % external_teacher.hours_per_week,
				'park' : external_teacher.park,
				'card' : external_teacher.card,
				'department' : external_teacher.department,
				'degree' : external_teacher.degree,
				'course' : external_teacher.course,
				'course_manager' : external_teacher.course_manager,
				'costs_center' : external_teacher.costs_center,
				'notes' : external_teacher.notes,
			}

	return HttpResponse(json.dumps(response), content_type="application/json")
