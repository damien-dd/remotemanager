import sys
import time
import datetime
import subprocess


def main():
	logfile = None
	if len(sys.argv) > 1:
		logfile = sys.argv[1]
		print 'log file: %s' % logfile

	reboot = False
	
	while not reboot:
		time.sleep(60)
		rfcomm_output = subprocess.check_output('/usr/bin/rfcomm').strip()
		
		if rfcomm_output.count('rfcomm') > 200 and not 'connected' in rfcomm_output:
			reboot = True

	if logfile is not None:
		try:
			f = open(logfile, 'a')
			f.write('%s reboot, rfcomm_output=%s\n' % (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), repr(rfcomm_output)))
			f.close()
		except Exception:
			print 'Cannot write into %s log file' % logfile

	print 'is going to reboot in 10sec.'
	time.sleep(10)
	subprocess.check_output(['/sbin/reboot'])
		

if __name__ == "__main__":
	main()
