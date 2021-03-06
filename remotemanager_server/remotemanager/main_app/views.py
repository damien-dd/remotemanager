from django.http import HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import simplejson
from django.db import connection
from django.utils import timezone
from django.utils.encoding import force_text
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.views import login
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
from main_app.forms import ProgramLoaderForm, DataHistoryForm, CustomAuthenticationForm
from main_app import tasks

task_test=None

@csrf_protect
@never_cache
def login_view(request):
	return login(request, authentication_form=CustomAuthenticationForm, template_name='login.html')


def logout_view(request):
	logout(request)
	return redirect('/')

@login_required
@user_passes_test(lambda u: u.is_staff)
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
@user_passes_test(lambda u: u.is_staff)
def rtcmd_readall(request, deviceID):
	remotedevice = RemoteDevice.objects.get(id=int(deviceID))
	values = realtime_cmd.read_all(int(deviceID))
	
	if type(values) is list:
		return render_to_response('realtime_cmd_readall.html', {'remotedevice': remotedevice, 'values': values}, context_instance=RequestContext(request))
	else:
		error_type = type(values).__name__
		error_msg = force_text(values)
		error = (error_type, error_msg)
		return render_to_response('realtime_cmd_readall.html', {'remotedevice': remotedevice, 'error': error}, context_instance=RequestContext(request))


@login_required
def index(request):
	remotedevices = RemoteDevice.objects.all().order_by('remotedevice_name')
	return render_to_response('home.html', {'remotedevices': remotedevices, 'system_uptime': calendar.timegm(time.gmtime()), 'uptime': (timezone.now()-timedelta(seconds=uptime.uptime()))}, context_instance=RequestContext(request))

@login_required
def bluetooth_status(request):
	return HttpResponse(repr(bluetooth.get_status()))

@login_required
def rtcmd(request):
	remotedevices = RemoteDevice.objects.all().order_by('remotedevice_name')
	return render_to_response('realtime_cmd.html', {'remotedevices': remotedevices}, context_instance=RequestContext(request))

@login_required
@user_passes_test(lambda u: u.is_superuser)
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
	if type(voltages) is list:
		voltagesElements = voltages[:-1]
		voltageTotal = voltages[-1]
		return render_to_response('realtime_cmd_vbat_chart.html', {'voltagesElements': voltagesElements, 'voltageTotal': voltageTotal}, context_instance=RequestContext(request))
	else:
		error_type = type(voltages).__name__
		error_msg = force_text(voltages)
		error = (error_type, error_msg)
		return render_to_response('realtime_cmd_vbat_chart.html', {'error': error}, context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_staff)
def get_temp(request):
	
	temperatures = realtime_cmd.get_temp()
	if type(temperatures) is list:
		return render_to_response('realtime_cmd_temp_chart.html', {'temperatures': temperatures}, context_instance=RequestContext(request))
	else:
		error_type = type(temperatures).__name__
		error_msg = force_text(temperatures)
		error = (error_type, error_msg)
		return render_to_response('realtime_cmd_temp_chart.html', {'error': error}, context_instance=RequestContext(request))

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
		fromDate=time.strftime("%Y-%m-%d", time.strptime(from_date, "%Y%m%d"))
	        toDate=time.strftime("%Y-%m-%d", time.strptime(to_date, "%Y%m%d"))

		cursor = connection.cursor()
		query =\
			' select'\
			'   extract(epoch from date_trunc(\'%(timestep)s\','\
			'      datafield_timestamp at time zone \'GMT\' at time zone \'%(timezone)s\' at time zone \'GMT\'))::bigint*1000 as timestamp,'\
			'   %(serie_type)s((datafield_value-%(serie_offset)f)*%(serie_multiplier)f),'\
			'   MAX(%(total_minutes)s)-SUM(datafield_nb_points)'\
			' from main_app_datafield'\
			' where datafield_nb_points>0 and datafield_serie_id=%(serie_id)d'\
			'   and datafield_timestamp at time zone \'GMT\' at time zone \'%(timezone)s\' at time zone \'GMT\' >= \'%(from_date)s\''\
			'   and datafield_timestamp at time zone \'GMT\' at time zone \'%(timezone)s\' at time zone \'GMT\' <= \'%(to_date)s\''\
			' group by timestamp order by timestamp' % {\
				'timestep': timestep,
				'serie_type': str(serie.serie_type),
				'serie_offset': serie.serie_values_offset,
				'serie_multiplier': serie.serie_values_multiplier,
				'total_minutes': total_minutes[timestep],
				'serie_id': int(serie_id),
				'timezone': timezone,
				'from_date': fromDate,
				'to_date':toDate}
		#raise Exception(query)
		cursor.execute(query)
		data=cursor.fetchall()
	
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@login_required
def timeline_chart(request, timelinechart_id):
	if request.method == 'POST':
		form = DataHistoryForm(request.POST, request.FILES)
		if form.is_valid():
			timestep = form.cleaned_data['timestep']
			timezone = form.cleaned_data['timezone']
			limit_to = form.cleaned_data['limit_to']
			if limit_to == 0:
				limit_to = ''
			else:
				limit_to = 'limit %d' % limit_to
			cursor = connection.cursor()
			if timestep == 'hour':
				timestep_bis = 'day'
			else:
				timestep_bis = timestep
			
			query =\
				' select'\
				'  date_trunc(\'day\', min(timestamp)) as from_date,'\
				'  date_trunc(\'day\', max(timestamp))+\'1 %(timestep_bis)s\'::INTERVAL as to_date'\
				'  from ('\
				'    select'\
				'     date_trunc(\'%(timestep)s\', datafield_timestamp at time zone \'GMT\' at time zone \'%(timezone)s\' at time zone \'GMT\') as timestamp'\
				'     from main_app_datafield'\
				'     where datafield_nb_points>0 and datafield_serie_id in (%(serieIDs)s)'\
				'     group by timestamp order by timestamp desc %(limit_to)s) as foo' % {\
					'timestep': timestep,
					'timestep_bis': timestep_bis,
					'serieIDs': ','.join(list(str(i) for i in TimelineChart.objects.get(id=int(timelinechart_id)).timelinechart_series.values_list('id', flat=True))),
					'timezone': timezone,
					'limit_to': limit_to}
			cursor.execute(query)
			from_date, to_date = cursor.fetchone()
			if from_date is None:
				from_date = date(1970,01,01)
			if to_date is None:
				to_date = date(9999,12,31)

			serieplots = SeriePlot.objects.filter(serieplot_timelinechart__id=int(timelinechart_id)).order_by('serieplot_rank')
			return render_to_response('timeline_chart_plot.html', {'serieplots': serieplots, 'timestep': timestep, 'timezone': timezone, 'from_date': from_date, 'to_date': to_date, 'query': query}, context_instance=RequestContext(request))
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
