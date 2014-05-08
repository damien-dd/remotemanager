#!/bin/sh

echo 'Stop PostgrSQL services...'
/usr/bin/systemctl stop postgresql-init.service
/usr/bin/systemctl stop postgresql.service
if [ $? -ne 0 ]; then
	echo 'Error: Cannot stop postgresql.service'
	exit 1
fi

if [ $# -eq 1 ] && [ $1 == "-reformat" ]; then
	echo 'Umount /data partition...'
	! mountpoint -q /data || /bin/umount /data
	if [ $? -ne 0 ]; then
		echo 'Error: Cannot umount the data partition'
		exit 1
	fi

	/usr/sbin/mkfs.ext4 /dev/mmcblk0p3
	if [ $? -ne 0 ]; then
		echo 'Error: Cannot format the data partition'
		exit 1
	fi

	/bin/mount /data
	if [ $? -ne 0 ]; then
		echo 'Error: Cannot mount the data partition'
		exit 1
	fi

	/bin/mkdir /data/dbbackup
	if [ $? -ne 0 ]; then
		echo 'Error: Cannot create /data/dbbackup directory'
		exit 1
	fi

	/bin/chown www-data:www-data /data/dbbackup
	if [ $? -ne 0 ]; then
		echo 'Error: Cannot set ownership on /data/dbbackup directory'
		exit 1
	fi
else
	echo 'Delete the all pgsql directory...'
	/bin/rm -rf /data/pgsql
fi

echo 'Restart PostgreSQL services...'
/usr/bin/systemctl start postgresql.service
/bin/sleep 1
if [ $? -ne 0 ]; then
	echo 'Error: Cannot start postgresql.service'
	exit 1
fi

echo 'Create remotemanager database user...'
/usr/bin/createuser --username=postgres remotemanager
if [ $? -ne 0 ]; then
	echo 'Error: Cannot create the remotemanager database user'
	exit 1
fi

echo 'Create remotemanagerdb database...'
/usr/bin/createdb --username=postgres --owner=remotemanager remotemanagerdb
if [ $? -ne 0 ]; then
	echo 'Error: Cannot create the remotemanagerdb database'
	exit 1
fi

/usr/bin/python /srv/remotemanager/manage.py syncdb --noinput
if [ $? -ne 0 ]; then
	echo 'Error: syncdb command failed'
	exit 1
fi

/usr/bin/python /srv/remotemanager/manage.py migrate djcelery
if [ $? -ne 0 ]; then
	echo 'Error: migrate djcelery command failed'
	exit 1
fi

/usr/bin/django-admin.py createsuperuser --pythonpath=/srv/remotemanager --settings=remotemanager.settings --username=root --noinput --email=root@example.com
if [ $? -ne 0 ]; then
	echo 'Error: Cannot create django root superuser'
	exit 1
fi
