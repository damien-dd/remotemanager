#!/bin/sh

echo 'Remount rootfs in read/write mode...'
/bin/mount -o remount,rw /
if [ $? -ne 0 ]; then
	echo 'Error: Cannot remount the rootfs in read/write mode'
	exit 1
fi

echo 'Copy file...'
/bin/cp $@
cp_ret=$?
if [ $cp_ret -ne 0 ]; then
	echo 'Error: Cannot copy file'
fi

echo 'Remount rootfs in read-only mode...'
/bin/mount -o remount,ro /
if [ $? -ne 0 ]; then
	echo 'Error: Cannot remount the rootfs in read-only mode'
	exit 1
fi

exit $cp_ret
