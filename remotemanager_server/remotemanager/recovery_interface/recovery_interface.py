import os
import time
import subprocess
import re
import uptime
from datetime import timedelta

from jinja2 import evalcontextfilter, Markup, escape
from flask import Flask, request, render_template, redirect
from werkzeug import secure_filename

app = Flask(__name__)

DBBACKUP_DIR = '/data/dbbackup'
RE_DBBACKUP_FILENAME = '^remotemanagerdb-\d{4}-\d{2}-\d{2}-\d{6}\.psql(\.gz)?$'

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
	result = ''
	for line in value.split('\n'):
		result += u'%s<br />' % escape(line)
	if eval_ctx.autoescape:
		result = Markup(result)
	return result


def get_uptime_str():
	uptime_delta = timedelta(seconds=uptime.uptime())
	uptime_str = '%s%s%s%s' % (\
		('%dj. ' % uptime_delta.days) if uptime_delta.days > 0 else '',
		('%dh. ' % (uptime_delta.seconds/(60*60))) if uptime_delta.seconds >= 60*60 else '',
		('%dmin. ' % (uptime_delta.seconds%(60*60)/60)) if uptime_delta.seconds >= 60 else '',
		'%dsec.' % (uptime_delta.seconds%60))
	return uptime_str

def get_backupfiles_list():
	fileslist = []
	try:
		filenameslist = os.listdir(DBBACKUP_DIR)
	except OSError:
		return None

	filenameslist.sort()
	for filename in filenameslist:
		filepath = os.path.join(DBBACKUP_DIR, filename)
		if os.path.isfile(filepath):
			filesize = os.path.getsize(filepath)
			filedate = time.strftime('%d-%m-%Y %H:%M:%S', time.gmtime(os.path.getmtime(filepath)))
			fileslist.append((filename, filesize, filedate))

	return fileslist


@app.route('/')
def index():
	return render_template('main.html', uptime=get_uptime_str())


@app.route('/dbinit/', methods=['GET', 'POST'])
def dbinit_action():
	if request.method == 'POST':
		post_data = dict(request.form)
		password = post_data['password'][0]
		if 'option' in post_data and post_data['option'][0] == 'reformat':
			reformat = True
		else:
			reformat = False
		
		if password != post_data['password_repeat'][0]:
			return render_template('dbinit_failed.html', uptime=get_uptime_str(), error_msg='Les mots de passes ne correspondent pas!')
		if str(password) == '':
			return render_template('dbinit_failed.html', uptime=get_uptime_str(), error_msg='Vous devez saisir un mot de passe!')
		try:
			cmd = ['sudo', 'scripts/initdb.sh']
			if reformat:
				cmd.append('-reformat')
			subprocess.check_output(cmd)
			subprocess.check_output(['python', 'scripts/changepassword.py', 'root', str(password)])
		except subprocess.CalledProcessError, err:
			error_msg = '%s script failed: %s' % (err.cmd, err.output)
			return render_template('dbinit_failed.html', uptime=get_uptime_str(), error_msg=error_msg)
		return render_template('dbinit_success.html', uptime=get_uptime_str())		
	else:
		return render_template('dbinit_confirm.html', uptime=get_uptime_str())


@app.route('/dbbackup/')
def dbbackup():
	return render_template('dbbackup_list.html', uptime=get_uptime_str(), fileslist=get_backupfiles_list())

@app.route('/dbbackup/create/', methods=['GET', 'POST'])
def dbbackup_action():
	if request.method == 'POST':
		p = subprocess.Popen('python /srv/remotemanager/manage.py dbbackup --compress'.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		returncode = p.wait()
		if returncode == 0:
			filename = p.stdout.read().split('Backup tempfile created: ', 1)[-1].split(' ', 1)[0]
			return render_template('dbbackup_success.html', uptime=get_uptime_str(), filename=filename)
		else:
			error_msg = '%s\n%s' % (p.stdout.read(), p.stderr.read())
			return render_template('dbbackup_failed.html', uptime=get_uptime_str(), error_msg=error_msg)
		
	else:
		return render_template('dbbackup_confirm.html', uptime=get_uptime_str())

@app.route('/dbrestore/')
def dbrestore():
	return render_template('dbrestore_list.html', uptime=get_uptime_str(), fileslist=get_backupfiles_list())

@app.route('/dbrestore/<filename>/', methods=['GET', 'POST'])
def dbrestore_action(filename):
	if request.method == 'POST':
		filepath = os.path.join(DBBACKUP_DIR, filename)
		# This operation can takes few minutes, the uwsgi_read_timeout parameter in
		# the nginx.conf file might need to be adjusted to a longer timeout (default is 60s)
		p = subprocess.Popen(['python', '/srv/remotemanager/manage.py', 'dbrestore', '-f', filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		returncode = p.wait()
		if returncode == 0:
			return render_template('dbrestore_success.html', uptime=get_uptime_str(), filename=filename)
		else:
			error_msg = '%s\n%s' % (p.stdout.read(), p.stderr.read())
			return render_template('dbrestore_failed.html', uptime=get_uptime_str(), error_msg=error_msg)
	else:
		return render_template('dbrestore_confirm.html', uptime=get_uptime_str(), filename=filename)


@app.route('/dbrestore/upload/', methods=['GET', 'POST'])
def upload_file():
# The client_max_body_size parameter in the nginx.conf file needs to be set if
# we want to accept file larger than 1M which is the default value for client_max_body_size
	if request.method == 'POST':
	        f = request.files['file']
		if f:
			filename = secure_filename(f.filename)
			if re.match(RE_DBBACKUP_FILENAME, filename) is None:
				return render_template('uploadbackup_failed.html', uptime=get_uptime_str(), filename=filename, error_msg='Nom de fichier de sauvegarde invalide!')
			filepath = '/data/dbbackup/%s' % filename
			if not os.path.isfile(filepath):
				f.save(filepath)
				return render_template('uploadbackup_success.html', uptime=get_uptime_str(), filename=filename)
			else:
				return render_template('uploadbackup_failed.html', uptime=get_uptime_str(), filename=filename, error_msg='Une sauvegarde du meme nom existe deja!')
		else:
			return render_template('uploadbackup_form.html', uptime=get_uptime_str())
	else:
		return render_template('uploadbackup_form.html', uptime=get_uptime_str())

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug = True)
