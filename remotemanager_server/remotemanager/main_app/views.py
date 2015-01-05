from django.http import HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import simplejson
from django.db import connection
from django.utils import timezone
import os
import subprocess
import serial
import datetime
import calendar
import re
import pytz
import time
from datetime import date, timedelta
import uptime


from main_app.models import RemoteDevice, Serie, DataField, TimelineChart, SeriePlot
from main_app import bluetooth
from main_app import realtime_cmd
from main_app.program_loader import handle_uploaded_file
from main_app.forms import ProgramLoaderForm, DataHistoryForm
from main_app import tasks

task_test=None

def logout_view(request):
	logout(request)
	return redirect('/')


def dev_choices(request): 
	dev_list = []
	ChoiceUSB = ("on-false", "on-true")

	mode = request.GET.get('mode')
	if str(mode).lower() == 'usb':
		ftdi_list = []
		arduino_list = []
		syst_dev_list = os.listdir('/dev')
		for dev in syst_dev_list:
			if dev.startswith('ftdi-'):
				ftdi_list.append('/dev/'+dev)
			elif dev.startswith('arduino-'):
				arduino_list.append('/dev/'+dev)
		choices = arduino_list + ftdi_list
	else:
		choices = ()

	[dev_list.append((each, each)) for each in choices]
	json = simplejson.dumps(dev_list)
	return HttpResponse(json, mimetype='application/javascript')


@login_required
def index(request):
	remotedevices = RemoteDevice.objects.all().order_by('remotedevice_name')
	return render_to_response('home.html', {'remotedevices': remotedevices, 'system_uptime': calendar.timegm(time.gmtime()), 'uptime': (timezone.now()-timedelta(seconds=uptime.uptime()))}, context_instance=RequestContext(request))

@login_required
def bluetooth_status(request):
	return HttpResponse(repr(bluetooth.get_status()))

@login_required
def rtcmd(request):
	return render_to_response('realtime_cmd.html', context_instance=RequestContext(request))

@login_required
@user_passes_test(lambda u: u.is_staff)
def program_loader(request):
	if request.method == 'POST':
		form = ProgramLoaderForm(request.POST, request.FILES)
		if form.is_valid():
			output = handle_uploaded_file(request.FILES['file'], form.cleaned_data['device'])
			return render_to_response('loader_output.html', {'output': output}, context_instance=RequestContext(request))
	else:
		form = ProgramLoaderForm()

	return render_to_response('loader_form.html', {'form': form}, context_instance=RequestContext(request))

@login_required
@user_passes_test(lambda u: u.is_staff)
def get_vbat(request):
	
	voltages = realtime_cmd.get_vbat()
	voltagesElements = voltages[:-1]
	voltageTotal = voltages[-1]
	if type(voltages) is list:
		return render_to_response('realtime_cmd_vbat_chart.html', {'voltagesElements': voltagesElements, 'voltageTotal': voltageTotal}, context_instance=RequestContext(request))
	else:
		return HttpResponse(repr(voltages))


@login_required
@user_passes_test(lambda u: u.is_staff)
def get_temp(request):
	
	error = None
	temperatures = realtime_cmd.get_temp()
	if type(temperatures) is type(str()):
		error = temperatures

	return render_to_response('realtime_cmd_temp_chart.html', {'temperatures': temperatures, 'error': error}, context_instance=RequestContext(request))

@login_required
def timeline_charts(request):
	charts = TimelineChart.objects.all()

	return render_to_response('timeline_charts.html', {'charts': charts}, context_instance=RequestContext(request))


@login_required
def get_serie(request, serie_id, timestep, timezone, from_date, to_date):
	serie = Serie.objects.get(id=serie_id)

	if timestep.startswith('minute'):
		year=2000+int(timestep[6:8])
		month=int(timestep[8:10])
		day=int(timestep[10:12])
		hour=timestep[12:14]

		data = serie.get_raw_data(datetime.date(year, month, day), hour=hour)
		return HttpResponse(simplejson.dumps(data), mimetype='application/json')
	else:
		total_minutes = {
			'hour':  '60',
			'day':   '1440',
			'month': '''1440*extract('days' from (date_trunc('month', datafield_timestamp at time zone \'GMT\' at time zone \'%s\' at time zone \'GMT\')+interval '1 month - 1 day'))''' % timezone,
			'year':  '''1440*extract('days' from (date_trunc('year', datafield_timestamp at time zone \'GMT\' at time zone \'%s\' at time zone \'GMT\')+interval '1 year - 1 day'))''' % timezone,
			}
		fromDate=calendar.timegm(time.strptime(from_date, "%Y%m%d"))
	        toDate=calendar.timegm(time.strptime(to_date, "%Y%m%d"))+24*60*60

		cursor = connection.cursor()
		query =\
			' select'\
			'   extract(epoch from date_trunc(\'%(timestep)s\','\
			'      datafield_timestamp at time zone \'GMT\' at time zone \'%(timezone)s\' at time zone \'GMT\'))::bigint*1000 as timestamp,'\
			'   %(serie_type)s((datafield_value-%(serie_offset)f)*%(serie_multiplier)f),'\
			'   MAX(%(total_minutes)s)-SUM(datafield_nb_points)'\
			' from main_app_datafield'\
			' where datafield_nb_points>0 and datafield_serie_id=%(serie_id)d'\
			' group by timestamp order by timestamp' % {\
				'timestep': timestep,
				'serie_type': str(serie.serie_type),
				'serie_offset': serie.serie_values_offset,
				'serie_multiplier': serie.serie_values_multiplier,
				'total_minutes': total_minutes[timestep],
				'serie_id': int(serie_id),
				'timezone': timezone}
		#raise Exception(query)
		cursor.execute(query)
		data=cursor.fetchall()
	
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@login_required
def timeline_chart(request, timelinechart_id):
	if request.method == 'POST':
		form = DataHistoryForm(request.POST, request.FILES)
		if form.is_valid():
			serieplots = SeriePlot.objects.filter(serieplot_timelinechart__id=int(timelinechart_id)).order_by('serieplot_rank')
			return render_to_response('timeline_chart_plot.html', {'serieplots': serieplots, 'timestep': form.cleaned_data['timestep'], 'timezone': form.data['timezone'], 'from_date': date(2014,01,01), 'to_date': date(2014,01,01)}, context_instance=RequestContext(request))
	else:
		form = DataHistoryForm()

	return render_to_response('timeline_chart_form.html', {'form': form}, context_instance=RequestContext(request))

@login_required
@user_passes_test(lambda u: u.is_staff)
def update_serie(request, serie_id):
	serie = Serie.objects.get(id=serie_id)

	return HttpResponse(repr(serie.update(3)))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def test(request):
	global task_test
	if task_test is None:
		task_test = tasks.test_task_db.delay('2013-08-13')
		output='new task started'
		output += repr(task_test.ready())
		time.sleep(2)
		output += repr(task_test.ready())
		output += repr(task_test.get())
	else:
		output = repr(task_test.ready())
		
	return HttpResponse(output)
