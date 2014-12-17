import serial
import re

from main_app import bluetooth
from main_app.models import RemoteDevice
from main_app.device_handler import DeviceHandler


TEMPERATURES_POS = {
	'Tin': (285, 430),
	'Tout': (285, 240),
	'S1': (240, 25),
	'S2': (534, 400),
	'S3': (534, 140),
	'Circulator': (227, 415)
}

def get_vbat():

	device = RemoteDevice.objects.get(remotedevice_name='BatteryVoltageMonitor')
	device_handler = DeviceHandler(device)

	
	device_handler.send_command('READ_ALL')
	
	res = device_handler.read_response((3+2)*13, timeout=3)
	device_handler.close()

	if res == '':
		return 'No response from remote device'

	if re.match('^([0-9]{3}\r\n){13}$', res) is None:
		return 'Invalid response from remote device: %s' % repr(res)

	res = res.strip().split('\r\n')
	
	voltagesList = []
	for voltage in res[:-1]:
		voltagesList.append(float(voltage)/100)

	voltagesList.append(float(res[-1])/10)

	return voltagesList


def get_temp():

	device = RemoteDevice.objects.get(remotedevice_name='DataLoggerTemperature')
	device_handler = DeviceHandler(device)

	device_handler.send_command('READ_ALL')
	
	res = device_handler.read_response(1000, timeout=3)
	
	device_handler.close()

	if res == '':
		return 'No response from remote device'

	temperatures = []
	for temperature in res.strip().split('\r\n'):
		name, value = temperature.rsplit(':', 1)
		name = name.strip()
		value = value.strip()

		if name in TEMPERATURES_POS:
			temperatures.append((name, value, TEMPERATURES_POS[name][0], TEMPERATURES_POS[name][1]))

	return temperatures
