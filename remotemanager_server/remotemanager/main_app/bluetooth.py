import re
import subprocess



def get_status():
	try:
		output = subprocess.check_output(['/usr/sbin/hciconfig','hci0'], stderr=subprocess.STDOUT)
		if 'DOWN' in output:
			return 'down'
		elif 'UP RUNNING' in output:
			return 'up'
		else:
			return None
	except subprocess.CalledProcessError:
		return None

def get_free_rfcomm():
	rfcomm_interfaces_taken = []
	rfcomm_interfaces = subprocess.check_output('/usr/bin/rfcomm').strip().split('\n')
	for rfcomm_interface in rfcomm_interfaces:
		if re.match('^rfcomm\d+:', rfcomm_interface):
			rfcomm_interfaces_taken.append(int(rfcomm_interface.split(':',1)[0][6:]))

	for n in range(256):
		if n not in rfcomm_interfaces_taken:
			return '/dev/rfcomm%d' % n

	return None


def get_rfcomm_status(remotedevice):
	dev = str(remotedevice.remotedevice_dev)
	mac = str(remotedevice.remotedevice_serial).upper()
	rfcomm_interfaces = subprocess.check_output('/usr/bin/rfcomm').strip().split('\n')
	for rfcomm_interface in rfcomm_interfaces:
		if mac in rfcomm_interface and 'connected' in rfcomm_interface:
			return (mac, 'connected')

	return (mac, None)

def bind_device(remotedevice):

	if remotedevice.remotedevice_mode != 'BT':
		return None

	dev = str(remotedevice.remotedevice_dev)
	mac = str(remotedevice.remotedevice_serial)

	try:
		subprocess.check_output(['sudo', '/usr/bin/rfcomm', 'release', dev], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError:
		pass

	try:
		output=subprocess.check_output(['sudo', '/usr/bin/rfcomm', 'bind', dev, mac, '1'], stderr=subprocess.STDOUT)
		if output == '':
			return True
		else:
			return False
	except subprocess.CalledProcessError:
		return False


def enable(enable=True):
	try:
		subprocess.check_output(['sudo','/usr/sbin/hciconfig','hci0', 'up' if enable else 'down'], stderr=subprocess.STDOUT)
		return True
	except subprocess.CalledProcessError:
		return False
