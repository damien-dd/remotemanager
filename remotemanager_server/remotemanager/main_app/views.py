from django.http import HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import simplejson
from django.db import connection
import subprocess
import serial
import datetime
import re
import pytz
import time
from datetime import date


from main_app.models import BluetoothRemoteDevice, RemoteDevice, Serie, DataField, TimelineChart, SeriePlot
from main_app import bluetooth
from main_app import realtime_cmd
from main_app.program_loader import handle_uploaded_file
from main_app.forms import ProgramLoaderForm, DataHistoryForm
from main_app import tasks

task_test=None

def logout_view(request):
	logout(request)
	return redirect('/')

@login_required
def index(request):
	return render(request, 'base.html')

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
def get_serie(request, serie_id, timestep):
	serie = Serie.objects.get(id=serie_id)

	if timestep.startswith('minute'):
		year=2000+int(timestep[6:8])
		month=int(timestep[8:10])
		day=int(timestep[10:12])
		hour=timestep[12:14]

		data = serie.get_raw_data(datetime.date(year, month, day), hour=hour)
		return HttpResponse(simplejson.dumps(data), mimetype='application/json')
	else:
		groupby = {
			'hour':  '%%Y-%%m-%%d %%H:00',
			'day':   '%%Y-%%m-%%d 00:00',
			'month': '%%Y-%%m-01 00:00',
			'year':  '%%Y-01-01 00:00',
			}

		total_minutes = {
			'hour':  '60',
			'day':   '1440',
			'month': '''1440*cast(julianday(date(datafield_timestamp, 'start of month', '+1 month'))-julianday(datafield_timestamp, 'start of month') as integer)''',
			'year':  '''1440*cast(julianday(date(datafield_timestamp, 'start of year', '+1 year'))-julianday(datafield_timestamp, 'start of year') as integer)''',
			}
		cursor = connection.cursor()
		query = 'select strftime(\'%%%%s\', strftime(\'%s\', datafield_timestamp))*1000, %s((datafield_value-%f)*%f), %s-SUM(datafield_nb_points) from main_app_datafield where datafield_nb_points>0 and datafield_serie_id=%d group by strftime(\'%s\', datafield_timestamp)' % (groupby[timestep], str(serie.serie_type), serie.serie_values_offset, serie.serie_values_multiplier, total_minutes[timestep], int(serie_id), groupby[timestep])
		cursor.execute(query)
		data=cursor.fetchall()
	
	return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@login_required
def timeline_chart(request, timelinechart_id):
	if request.method == 'POST':
		form = DataHistoryForm(request.POST, request.FILES)
		if form.is_valid():
			serieplots = SeriePlot.objects.filter(serieplot_timelinechart__id=int(timelinechart_id)).order_by('serieplot_rank')
			return render_to_response('timeline_chart_plot.html', {'title': 'Production/Consommation electrique', 'serieplots': serieplots, 'timestep': form.cleaned_data['timestep']}, context_instance=RequestContext(request))
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
