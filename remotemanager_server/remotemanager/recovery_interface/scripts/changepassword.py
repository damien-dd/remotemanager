import os
import sys
import inspect

sys.path.append(os.path.join(os.path.abspath(__file__).rsplit('/', 1)[0], '../..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'remotemanager.settings')

from django.contrib.auth.models import User


def changepassword(username, new_password):
	user = User.objects.get(username=username)
	user.set_password(new_password)
	user.save()

if __name__ == "__main__":
	if len(sys.argv) == 3:
		changepassword(sys.argv[1], sys.argv[2])
		print 'Password for the %r user has been changed' % sys.argv[1]
		sys.exit(0)
	else:
		print 'Usage: python changepassword.py <username> <new_password>'
		sys.exit(1)
