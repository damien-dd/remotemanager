# RemoteManager

RemoteManager aims to control one or multiple slave devices having a serial interface from internet via a web interface.


A Linux embedded platform running a Django based web service acts as a base station. The RootFS specically made for this system is build using the Buildroot compilation tool. Supported platforms are:
- BeagleBone Black
- Raspberry Pi 2

Slaves devices (typicaly Arduino but not exclusively) are connected to the base station via Bluetooth (Serial port profile) or USB (Virtual serial port).




In this current implementation, the system is dedicated for energy monitoring for a specific installation (with photovoltaic and water heating solar panels).

However it can be easily configured to monitor any kind of value measurable from a slave device.

Fell free to modify and adapt it to your own needs!



# Compilation instructions (for Linux Debian based distributions)

$ cd remotemanager/remotemanager_server/system/rootfs/buildroot-2014.02/

$ cp configs/remotemanager_bbb_defconfig .config  # for BeagleBone Black

$ cp configs/remotemanager_rpi2_defconfig .config  # for Raspberry Pi 2

$ make

Note: The compilation does not work on 64bits systems (you can use a 32bits virtual machine if you have a 64bits system)

# Installation instructions

TO DO
