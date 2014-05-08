import sys
import time
import datetime
import subprocess

def get_rfcomm_status():
	rfcomm_status = []
	rfcomm_interfaces = subprocess.check_output('/usr/bin/rfcomm').strip().split('\n')
	for rfcomm_interface in rfcomm_interfaces:
		if ':' in rfcomm_interface:
			rfcomm_dev, rfcomm_output = rfcomm_interface.strip().split(':', 1)
			if ' ' in rfcomm_output:
				rfcomm_mac, rfcomm_output = rfcomm_output.strip().split(' ', 1)
				rfcomm_status.append((rfcomm_mac.upper(), rfcomm_output))
	return rfcomm_status


def main():
	logfile = None
	if len(sys.argv) > 1:
		logfile = sys.argv[1]
		print 'log file: %s' % logfile

	reboot = False
	while not reboot:
		time.sleep(60)
		rfcomm_status = get_rfcomm_status()
		print rfcomm_status
		for rfcomm_mac, rfcomm_state in rfcomm_status:
			if 'closed' in rfcomm_state and 'tty-attached' in rfcomm_state:
				reboot = True

	if logfile is not None:
		try:
			f = open(logfile, 'a')
			f.write('%s reboot, rfcomm_status=%s\n' % (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), repr(rfcomm_status)))
			f.close()
		except Exception:
			print 'Cannot write into %s log file' % logfile

	print 'is going to reboot in 10sec.'
	time.sleep(10)
	subprocess.check_output(['/sbin/reboot'])
		

if __name__ == "__main__":
	main()
