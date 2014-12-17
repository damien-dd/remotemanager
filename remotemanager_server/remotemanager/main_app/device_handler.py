import serial
import time
import re
import datetime
import calendar

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

READING_TIMEOUT = 0.1
MAX_RESPONSE_SIZE = 5000


class RemoteDeviceConnectionError(Exception):
    pass

class BluetoothHostError(RemoteDeviceConnectionError):
    pass

class RemoteDeviceCurrentlyInUseError(RemoteDeviceConnectionError):
    pass

class RemoteDeviceOpenError(RemoteDeviceConnectionError):
    pass



class RemoteDeviceCommunicationError(Exception):
    pass

class RemoteDeviceReadError(RemoteDeviceCommunicationError):
    pass

class RemoteDeviceWriteError(RemoteDeviceCommunicationError):
    pass


class DeviceHandler:

	def __init__(self, device, request_status=True):
		self.device = device
		self.device.enable()
		time.sleep(0.5)
				
		try:
			self.serial = serial.Serial(str(device.remotedevice_dev), 115200, timeout=READING_TIMEOUT)
			self.serial.flushInput()
			self.device.remotedevice_last_connection_status = 'OK'
		except Exception:
			self.device.remotedevice_last_connection_status = 'OPEN_ERR'
			self.close()
			self.device.save()
			raise RemoteDeviceOpenError(_('Unable to connect to the device'))

		self.device.save()

		if request_status:
			self.request_status()
			

	def request_status(self):
		self.send_command('STATUS')
		status = self.read_response(length=3, timeout=2)
		self.device.remotedevice_last_status_request = timezone.now()
		self.device.remotedevice_last_status = status
		self.send_command('GET_TIME')
		datetime_str = self.read_response(length=19, end_with='\r\n', timeout=3).strip()
		if re.match('^\d{1,2}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}$', datetime_str):
			date_str, time_str = datetime_str.split(' ')
			day_str, month_str, year_str = date_str.split('/')
			hours_str, minutes_str, seconds_str = time_str.split(':')
			try:
				remotedevice_clock = datetime.datetime(2000+int(year_str), int(month_str), int(day_str), int(hours_str), int(minutes_str), int(seconds_str))
				time_offset = calendar.timegm(remotedevice_clock.timetuple()) - calendar.timegm(time.gmtime())
				if time_offset > -2147483648 and time_offset < 2147483647:
					self.device.remotedevice_last_time_offset = time_offset
				else:
					raise ValueError('Clock offset out of range')
			except ValueError:
				self.device.remotedevice_last_time_offset = None
		else:
			self.device.remotedevice_last_time_offset = None
		self.device.save()


	def send_command(self, command):
		try:
			self.serial.write(command+'\r')
		except Exception:
			self.close()
			raise RemoteDeviceWriteError(_('Unable to send command to the device'))

	def read_response(self, length=MAX_RESPONSE_SIZE, end_with=None, timeout=1):
		eleapsed_time=0
		response = ''
		while eleapsed_time < timeout and len(response) < length and (end_with is None or not end_with in response):
			try:
				response += self.serial.read(length - len(response))
			except Exception:
				self.close()
				raise RemoteDeviceReadError(_('Unable to read response from the device'))
			eleapsed_time += READING_TIMEOUT
		return response

	def close(self):
		try:
			self.serial.close()
		except Exception:
			pass

		try:
			self.device.enable(False)
		except Exception:
			pass
