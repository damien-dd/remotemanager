import os
import time
import subprocess
import re
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


def get_backupfiles_list():
	fileslist = []
	filenameslist = os.listdir(DBBACKUP_DIR)
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
	return render_template('main.html')

@app.route('/sleep/<timeout>')
def sleep(timeout):
	time.sleep(int(timeout))
	return render_template('main.html')

@app.route('/dbbackup/')
def dbbackup():
	return render_template('dbbackup_list.html', fileslist=get_backupfiles_list())

@app.route('/dbbackup/create/', methods=['GET', 'POST'])
def dbbackup_action():
	if request.method == 'POST':
		p = subprocess.Popen('python /srv/remotemanager/manage.py dbbackup --compress'.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		returncode = p.wait()
		if returncode == 0:
			filename = p.stdout.read().split('Backup tempfile created: ', 1)[-1].split(' ', 1)[0]
			return render_template('dbbackup_success.html', filename=filename)
		else:
			error_msg = '%s\n%s' % (p.stdout.read(), p.stderr.read())
			return render_template('dbbackup_failed.html', error_msg=error_msg)
		
	else:
		return render_template('dbbackup_confirm.html')

@app.route('/dbrestore/')
def dbrestore():
	return render_template('dbrestore_list.html', fileslist=get_backupfiles_list())

@app.route('/dbrestore/<filename>/', methods=['GET', 'POST'])
def dbrestore_action(filename):
	if request.method == 'POST':
		filepath = os.path.join(DBBACKUP_DIR, filename)
		# This operation can takes few minutes, the uwsgi_read_timeout parameter in
		# the nginx.conf file might need to be adjusted to a longer timeout (default is 60s)
		p = subprocess.Popen(['python', '/srv/remotemanager/manage.py', 'dbrestore', '-f', filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		returncode = p.wait()
		if returncode == 0:
			return render_template('dbrestore_success.html', filename=filename)
		else:
			error_msg = '%s\n%s' % (p.stdout.read(), p.stderr.read())
			return render_template('dbrestore_failed.html', error_msg=error_msg)
	else:
		return render_template('dbrestore_confirm.html', filename=filename)


@app.route('/dbrestore/upload/', methods=['GET', 'POST'])
def upload_file():
# The client_max_body_size parameter in the nginx.conf file needs to be set if
# we want to accept file larger than 1M which is the default value for client_max_body_size
	if request.method == 'POST':
	        f = request.files['file']
		if f:
			filename = secure_filename(f.filename)
			if re.match(RE_DBBACKUP_FILENAME, filename) is None:
				return render_template('uploadbackup_failed.html', filename=filename, error_msg='Nom de fichier de sauvegarde invalide!')
			filepath = '/data/dbbackup/%s' % filename
			if not os.path.isfile(filepath):
				f.save(filepath)
				return render_template('uploadbackup_success.html', filename=filename)
			else:
				return render_template('uploadbackup_failed.html', filename=filename, error_msg='Une sauvegarde du meme nom existe deja!')
		else:
			return render_template('uploadbackup_form.html')
	else:
		return render_template('uploadbackup_form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug = True)
