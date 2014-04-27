#!/bin/sh

# This script monitor the state of the eth0 link
# and configure the interface with ifup/ifdown when
# the link goes up/down

currentState="down"
previousState="down"
transitionUp=false
transitionDown=false

/sbin/ifconfig eth0 up

disable_interface() {
	/bin/echo "shutdown eth0 interface"
	/sbin/ifdown eth0
	exit 0
}

trap disable_interface SIGTERM

while true
do
	currentState=`cat /sys/class/net/eth0/operstate`

	if [ $currentState == "up" ]
	then
		if [ $previousState != "up" ]
		then
			/bin/echo 'eth0 interface went up'
			/sbin/ifup eth0
		fi
	else
		if [ $previousState == "up" ]
		then
			/bin/echo 'eth0 interface went down'
			/sbin/ifdown eth0
			/sbin/ifconfig eth0 up
		fi
	fi

	previousState=$currentState
	/bin/sleep 1
done
