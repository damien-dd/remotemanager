import serial
import time

READING_TIMEOUT = 0.1
MAX_RESPONSE_SIZE = 5000

class DeviceHandler:

	def __init__(self, device):
		self.device = device
		self.device.enable()
		time.sleep(0.5)
		
		try:
			self.serial = serial.Serial(str(device.remotedevice_dev), 115200, timeout=READING_TIMEOUT)
		except Exception:
			self.close()
			raise Exception('Unable to connect to the device')

	def send_command(self, command):
		try:
			self.serial.write(command+'\r')
		except Exception:
			self.close()
			raise Exception('Unable to send command to the device')

	def read_response(self, length=MAX_RESPONSE_SIZE, timeout=1):
		eleapsed_time=0
		response = ''
		while eleapsed_time < timeout and len(response) < length:
			try:
				response += self.serial.read(length - len(response))
			except Exception:
				self.close()
				raise Exception('Unable to read response from the device')
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