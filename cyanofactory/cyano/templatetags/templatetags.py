'''
Whole-cell template tags

Author: Jonathan Karr, jkarr@stanford.edu
Affiliation: Covert Lab, Department of Bioengineering, Stanford University
Last updated: 2012-07-17

Copyright (c) 2013 Gabriel Kind <gkind@hs-mittweida.de>
Hochschule Mittweida, University of Applied Sciences

Released under the MIT license
'''

from itertools import groupby
from math import ceil
import datetime
import os
import re

from django import template
from django.core.urlresolvers import reverse
from django.template import TemplateSyntaxError

numeric_test = re.compile("^\d+$")
register = template.Library()

''' From http://stackoverflow.com/questions/844746/performing-a-getattr-style-lookup-in-a-django-template '''
@register.filter
def getattribute(value, arg):
	'''Gets an attribute of an object dynamically from a string name'''

	if hasattr(value, arg):
		return getattr(value, arg)
	elif hasattr(value, 'has_key') and value.has_key(arg):
		return value[arg]
	elif numeric_test.match(arg) and len(value) > int(arg):
		return value[int(arg)]
	else:
		return None

''' From http://snipplr.com/view/47532/ '''
@register.filter
def cammelCaseToSpaces(value):	
	s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', value)
	return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
	
@register.filter
def cammelCaseToUnderscores(value):	
	s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', value)
	return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
	
@register.filter
def append(li, item):
	return li.append(item)

@register.filter
def firsthalf(thelist):
	try:
		thelist = list(thelist)
	except (ValueError, TypeError):
		return [thelist]
	half = int(ceil(float(len(thelist)) / 2))
	return thelist[0:half]
	
@register.filter
def lasthalf(thelist):
	try:
		thelist = list(thelist)
	except (ValueError, TypeError):
		return [thelist]
	half = int(ceil(float(len(thelist)) / 2))
	return thelist[half:]

''' From http://djangosnippets.org/snippets/6/: '''
'''
Template tags for working with lists.

You'll use these in templates thusly::

	{% load listutil %}
	{% for sublist in mylist|parition:"3" %}
		{% for item in mylist %}
			do something with {{ item }}
		{% endfor %}
	{% endfor %}
'''
@register.filter
def partition(thelist, n):
	'''
	Break a list into ``n`` pieces. The last list may be larger than the rest if
	the list doesn't break cleanly. That is::

		>>> l = range(10)

		>>> partition(l, 2)
		[[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

		>>> partition(l, 3)
		[[0, 1, 2], [3, 4, 5], [6, 7, 8, 9]]

		>>> partition(l, 4)
		[[0, 1], [2, 3], [4, 5], [6, 7, 8, 9]]

		>>> partition(l, 5)
		[[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

	'''
	try:
		n = int(n)
		thelist = list(thelist)
	except (ValueError, TypeError):
		return [thelist]
	p = len(thelist) / n
	return [thelist[p*i:p*(i+1)] for i in range(n - 1)] + [thelist[p*(i+1):]]

@register.filter
def partition_horizontal(thelist, n):
	'''
	Break a list into ``n`` peices, but "horizontally." That is, 
	``partition_horizontal(range(10), 3)`` gives::
	
		[[1, 2, 3],
		 [4, 5, 6],
		 [7, 8, 9],
		 [10]]
		
	Clear as mud?
	'''
	try:
		n = int(n)
		thelist = list(thelist)
	except (ValueError, TypeError):
		return [thelist]
	newlists = [list() for i in range(n)]
	for i, val in enumerate(thelist):
		newlists[i%n].append(val)
	return newlists
	
'''From http://djangosnippets.org/snippets/2511/ '''
class DynamicRegroupNode(template.Node):
	def __init__(self, target, parser, expression, var_name):
		self.target = target
		self.expression = template.Variable(expression)
		self.var_name = var_name
		self.parser = parser

	def render(self, context):
		obj_list = self.target.resolve(context, True)
		if obj_list == None:
			# target variable wasn't found in context; fail silently.
			context[self.var_name] = []
			return ''
		# List of dictionaries in the format:
		# {'grouper': 'key', 'list': [list of contents]}.

		'''
		Try to resolve the filter expression from the template context.
		If the variable doesn't exist, accept the value that passed to the
		template tag and convert it to a string
		'''
		try:
			exp = self.expression.resolve(context)
		except template.VariableDoesNotExist:
			exp = unicode(self.expression)

		filter_exp = self.parser.compile_filter(exp)

		context[self.var_name] = [
			{'grouper': key, 'list': list(val)}
			for key, val in
			groupby(obj_list, lambda v, f=filter_exp.resolve: f(v, True))
		]

		return ''
	
@register.tag
def dynamic_regroup(parser, token):
	firstbits = token.contents.split(None, 3)
	if len(firstbits) != 4:
		raise TemplateSyntaxError("'regroup' tag takes five arguments")
	target = parser.compile_filter(firstbits[1])
	if firstbits[2] != 'by':
		raise TemplateSyntaxError("second argument to 'regroup' tag must be 'by'")
	lastbits_reversed = firstbits[3][::-1].split(None, 2)
	if lastbits_reversed[1][::-1] != 'as':
		raise TemplateSyntaxError("next-to-last argument to 'regroup' tag must"
								  " be 'as'")

	'''
	Django expects the value of `expression` to be an attribute available on
	your objects. The value you pass to the template tag gets converted into a
	FilterExpression object from the literal.
	
	Sometimes we need the attribute to group on to be dynamic. So, instead
	of converting the value to a FilterExpression here, we're going to pass the
	value as-is and convert it in the Node.
	'''
	expression = lastbits_reversed[2][::-1]
	var_name = lastbits_reversed[0][::-1]

	'''
	We also need to hand the parser to the node in order to convert the value
	for `expression` to a FilterExpression.
	'''
	return DynamicRegroupNode(target, parser, expression, var_name)

class MakeUrlNode(template.Node):
	def __init__(self, queryargs, newarg, newval):
		self.queryargs = template.Variable(queryargs)
		self.newarg = template.Variable(newarg)
		self.newval = template.Variable(newval)
	def render(self, context):
		arr = []		
		newarg = self.newarg.resolve(context)
		newval = self.newval.resolve(context)
		queryargs = {}
		for key, val in self.queryargs.resolve(context).items():
			queryargs[key] = val
		queryargs[newarg] = [newval, ]
		for key, vals in queryargs.items():
			for val in vals:
				if hasattr(val, 'id'):
					val = val.id
				if val != '':
					arr.append(key + '=' + val)
		return '&'.join(arr)

@register.tag
def makeurl(parser, token):
	queryargs, newarg, newval = token.split_contents()[1:]
	return MakeUrlNode(queryargs, newarg, newval)
	
@register.simple_tag
def reverseurl(*args, **kwargs):
	view = ''.join(args)
	if kwargs.has_key('pk'):
		return reverse(view, args=(kwargs['pk'], ))
	return reverse(view)

@register.simple_tag
def stringreplace(s, old, new):
	return s.replace(old, new)

@register.filter
def is_concrete_entry(model_verbose_name_plural, app_name):	
	from cyano.helpers import getModelByVerboseNamePlural
	return not getModelByVerboseNamePlural(model_verbose_name_plural) is None
	
@register.simple_tag
def get_choice_verbose_name(app_name, model_type, field_name, choice_name):
	from django.db.models import get_model
	
	choices = get_model(app_name, model_type)._meta.get_field(field_name).choices
	
	choice_names = [x[0] for x in choices]
	if choice_name in choice_names:
		return choices[choice_names.index(choice_name)][1]
	return choice_name
	
@register.filter
def get_cross_reference(source, xid):
	from cyano.models import CROSS_REFERENCE_SOURCE_URLS
	return CROSS_REFERENCE_SOURCE_URLS[source] % xid
	
@register.filter
def get_genetic_code_name(code):
	from cyano.models import CHOICES_GENETIC_CODE
	code = '%s' % code
	
	codes = [x[0] for x in CHOICES_GENETIC_CODE]
	if code in codes:
		return CHOICES_GENETIC_CODE[codes.index(code)][1]
	return 'Unknown'
	
@register.filter
def multiply(val1, val2):
	return val1 * val2;
	
@register.filter
def get_template_last_updated(templateFile):
	import settings
	return datetime.datetime.fromtimestamp(os.path.getmtime(settings.TEMPLATES[0]['DIRS'][0] + '/' + templateFile))

@register.filter	
def set_time_zone(datetime):		
	return datetime.astimezone(tz=None)