import subprocess

from main_app.models import RemoteDevice
from main_app import bluetooth

MAX_PROGRAM_SIZE = 32256

def handle_uploaded_file(f, device):
	file_path = '/tmp/%s' % f.name
	with open(file_path, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
	
	program_size = verify_program_size(file_path)
	if program_size < 0:
		return 'Invalid program file'
	elif program_size == 0:
		return 'Cannot determine program size'
	elif program_size > MAX_PROGRAM_SIZE:
		return 'Program size: %d bytes out of max %d' % (program_size, MAX_PROGRAM_SIZE)

	return load_program(device, file_path)


def verify_program_size(program_path):
	try:
		output = subprocess.check_output(['/home/root/avr-size', program_path], stderr=subprocess.STDOUT).strip().split('\n')[-1].replace(' ', '').split('\t')
		try:
			return (int(output[1])+int(output[2]))
		except Exception:
			return 0
		
	except subprocess.CalledProcessError:
		return -1


def load_program(device, program_path):
	dev = str(device.remotedevice_dev)

	if not bluetooth.enable():
		return 'Cannot enable bluetooth'
	if not bluetooth.bind_device(device):
		return 'Cannot bind bluetooth device'
	
	
	try:
		output = subprocess.check_output(['sudo', '/home/root/avrdude-5.11.1/avrdude','-F','-p', 'atmega328p', '-c', 'arduino', '-b', '115200', '-P', dev, '-U', 'flash:w:%s' % program_path], stderr=subprocess.STDOUT)
		output = output.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
	except subprocess.CalledProcessError:
		output = '\'/home/root/avrdude-5.11.1/avrdude -F -p atmega328p -c arduino -b 115200 -P /dev/rfcomm2 -U flash:w:/home/root/Blink.cpp.hex\' command failed'

	bluetooth.enable(False)

	return output
