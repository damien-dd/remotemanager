from __future__ import absolute_import

from celery import task
import time

from main_app.models import DataField, Serie, RemoteDevice
from main_app.device_handler import DeviceHandler

@task()
def add(x, y):
	return x+y

@task()
def update_device_series(deviceId):
	result = {}
	
	if type(deviceId) == type(int()):
		device = RemoteDevice.objects.get(id=deviceId)
	elif type(deviceId) == type(str()):
		device = RemoteDevice.objects.get(remotedevice_name=deviceId)
	
	device_handler = DeviceHandler(device)
	for serie in Serie.objects.filter(serie_remotedevice=device):
		result['Serie%d' % serie.id] = serie.update(10, device_handler, keep_device_open=True)
	device_handler.close()
	return result

@task()
def update_serie(serieId):
	if type(serieId) == type(int()):
		serie = Serie.objects.get(id=serieId)
	elif type(serieId) == type(str()):
		serie = Serie.objects.get(serie_name=serieId)

	return serie.update(10)

@task()
def test_task_db(date_str):
	return DataField.objects.filter(datafield_serie_id__exact=1, datafield_timestamp__contains=date_str).values_list('id','datafield_timestamp',  'datafield_nb_points')
