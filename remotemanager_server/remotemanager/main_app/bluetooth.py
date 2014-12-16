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


def get_rfcomm_status(remotedevice):
	dev = str(remotedevice.remotedevice_dev)
	rfcomm_interfaces = subprocess.check_output('/usr/bin/rfcomm').strip().split('\n')
	for rfcomm_interface in rfcomm_interfaces:
		if ':' in rfcomm_interface:
			rfcomm_dev, rfcomm_output = rfcomm_interface.strip().split(':', 1)
			if ' ' in rfcomm_output:
				rfcomm_mac, rfcomm_output = rfcomm_output.strip().split(' ', 1)
				if ' ' in rfcomm_output:
					rfcomm_output, rfcomm_state = rfcomm_output.strip().rsplit(' ', 1)
					if dev.endswith(rfcomm_dev):
						return (rfcomm_mac.upper(), rfcomm_state)

	return (None, None)

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
