import serial
import time

from django.utils import timezone

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
			self.device.remotedevice_last_connection_status = 'OK'
		except Exception:
			self.device.remotedevice_last_connection_status = 'OPEN_ERR'
			self.close()
			self.device.save()
			raise RemoteDeviceOpenError('Unable to connect to the device')

		self.device.save()

		if request_status:
			self.request_status()
			

	def request_status(self):
		self.send_command('STATUS')
		status = self.read_response(length=3, timeout=2)
		self.device.remotedevice_last_status_request = timezone.now()
		self.device.remotedevice_last_status = status
		self.device.save()


	def send_command(self, command):
		try:
			self.serial.write(command+'\r')
		except Exception:
			self.close()
			raise RemoteDeviceWriteError('Unable to send command to the device')

	def read_response(self, length=MAX_RESPONSE_SIZE, timeout=1):
		eleapsed_time=0
		response = ''
		while eleapsed_time < timeout and len(response) < length:
			try:
				response += self.serial.read(length - len(response))
			except Exception:
				self.close()
				raise RemoteDeviceReadError('Unable to read response from the device')
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
