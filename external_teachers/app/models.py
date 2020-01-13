# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Textarea, Select
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
import json

import fenixedu

ENCODING = 'utf-8'
MONTH_START_CLASSES = 9
NUMBER_OF_SEMESTERS = 2

class Profile(models.Model):
	user = models.OneToOneField(User)
	name = models.CharField(max_length=200)

class Semester(models.Model):
	number = models.IntegerField()
	year_initial = models.IntegerField()
	year_final = models.IntegerField()

	@staticmethod
	def get_or_create_current():
		now = datetime.now()

		if now.month < MONTH_START_CLASSES:
			number = 2
			year_initial = now.year - 1
			year_final = now.year
		else:
			number = 1
			year_initial = now.year
			year_final = now.year + 1

		semester, created = Semester.objects.get_or_create(
			number = number,
			year_initial = year_initial,
			year_final = year_final)

		return semester

	@staticmethod
	def get_current_and_future():
		current = Semester.get_or_create_current()
		result = Semester.objects.filter(year_initial__gte=current.year_initial).exclude(
											number__lt=current.number,
											year_initial=current.year_initial)

		return result

	def __unicode__(self):
		return self.get_display()

	def get_display(self):
		return str(self.number) + " " + _("semester").encode().decode() + " " + str(self.year_initial) + "/" + str(self.year_final)

	def get_or_create_next(self):
		if self.number == NUMBER_OF_SEMESTERS:
			number = 1
			year_initial = self.year_initial + 1
			year_final = self.year_final + 1
		else:
			number = self.number + 1
			year_initial = self.year_initial
			year_final = self.year_final

		semester, created = Semester.objects.get_or_create(
			number = number,
			year_initial = year_initial,
			year_final = year_final)

		return semester

def get_or_create_current_semester():
	return Semester.get_or_create_current()

class ProfessionalCategory(models.Model):
	slug = models.CharField(max_length=200, unique=True)
	name = models.CharField(max_length=200)

class Typology(models.Model):
	name = models.CharField(max_length=200)

class ExternalTeacher(models.Model):
	ist_id = models.CharField(max_length=20)
	is_closed = models.BooleanField( default=False)
	closed_by = models.ForeignKey(User, null=True)
	close_date = models.DateTimeField('close date', null=True)
	professional_category_str = models.CharField(max_length=1, blank=True)
	professional_category = models.ForeignKey(ProfessionalCategory, null=True)
	typology = models.ForeignKey(Typology, null=True)
	hours_per_week = models.DecimalField(decimal_places=2, max_digits=5)
	park = models.BooleanField(default=False)
	card = models.BooleanField(default=False)
	department = models.CharField(max_length=200)
	name = models.CharField(max_length=200)
	degree = models.CharField(max_length=200)
	course = models.CharField(max_length=200)
	course_manager = models.CharField(max_length=200)
	costs_center = models.CharField(max_length=200, blank=True)
	notes = models.CharField(max_length=200, blank=True)
	semester = models.ForeignKey('Semester', default=1)

	def close(self, user):
		self.is_closed = True
		self.close_date = datetime.now()
		self.closed_by = user

	def get_display(self):
		return self.ist_id + ' ' + self.name + ' ' + self.course + self.professional_category.name

	def __unicode__(self):
		return self.get_display()

	def unique_error_message(self, model_class, unique_check):
		if model_class == type(self) and unique_check == ('semester', 'ist_id'):
			return _('error.same.semester')
		else:
			return super(ExternalTeacher, self).unique_error_message(model_class, unique_check)

#	class Meta:
#		unique_together = ('semester', 'ist_id',)
