################################################################################
#
# remotemanager
#
################################################################################

REMOTEMANAGER_VERSION = 0.1
REMOTEMANAGER_SITE = $(TOPDIR)/../../../remotemanager
REMOTEMANAGER_SITE_METHOD = local

REMOTEMANAGER_DEPENDENCIES = python python-pip host-python-pip host-python host-remotemanager nginx
HOST_REMOTEMANAGER_DEPENDENCIES = host-python-pip host-python

REMOTEMANAGER_DESTDIR = /srv/remotemanager


define REMOTEMANAGER_EXTRACT_CMDS
        cp -r * $(@D)
endef

define REMOTEMANAGER_CONFIGURE_CMDS
	echo "nothing to configure"
endef

define REMOTEMANAGER_BUILD_CMDS
	echo "nothing to build"
endef


ifeq ($(BR2_PACKAGE_REMOTEMANAGER_ETHERNET_INTERFACE),y)
define REMOTEMANAGER_ETHERNET_INTERFACE_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 744 package/remotemanager/eth0-configure.sh \
		$(TARGET_DIR)/home/eth0-configure.sh
endef
endif


define REMOTEMANAGER_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)$(REMOTEMANAGER_DESTDIR)
	cp -r $(@D)/* $(TARGET_DIR)$(REMOTEMANAGER_DESTDIR)
	$(INSTALL) -D -m 755 $(@D)/manage.py \
		$(TARGET_DIR)$(REMOTEMANAGER_DESTDIR)/manage.py

	$(INSTALL) -D -m 755 $(@D)/recovery_interface/scripts/initdb.sh \
		$(TARGET_DIR)$(REMOTEMANAGER_DESTDIR)/recovery_interface/scripts/initdb.sh
	
	$(INSTALL) -D -m 644 package/remotemanager/django-settings-collectstatic-host-to-target.py \
		$(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/django-settings-collectstatic-host-to-target.py

	$(HOST_DIR)/usr/bin/python \
		$(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/django-settings-collectstatic-host-to-target.py \
		$(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/remotemanager/settings.py \
		$(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/remotemanager/settings_cross_compile.py \
		$(HOST_DIR) $(TARGET_DIR)
	$(HOST_DIR)/usr/bin/python $(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/manage.py collectstatic --settings=remotemanager.settings_cross_compile --noinput

	$(REMOTEMANAGER_ETHERNET_INTERFACE_INSTALL_TARGET_CMDS)
endef

define HOST_REMOTEMANAGER_INSTALL_CMDS
	mkdir -p $(HOST_DIR)$(REMOTEMANAGER_DESTDIR)
	cp -r $(@D)/* $(HOST_DIR)$(REMOTEMANAGER_DESTDIR)
	$(INSTALL) -D -m 755 $(@D)/manage.py \
		$(HOST_DIR)$(REMOTEMANAGER_DESTDIR)/manage.py
endef

ifeq ($(BR2_PACKAGE_REMOTEMANAGER_ETHERNET_INTERFACE),y)
define REMOTEMANAGER_ETHERNET_INTERFACE_INSTALL_INIT_SYSTEMD
	[ -f $(TARGET_DIR)/etc/systemd/system/network.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/network.service \
			$(TARGET_DIR)/etc/systemd/system/network.service

	ln -fs ../network.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/network.service
endef
endif

define REMOTEMANAGER_INSTALL_INIT_SYSTEMD

	[ -f $(TARGET_DIR)/etc/celery.conf ] || \
		$(INSTALL) -D -m 644 package/remotemanager/celery.conf \
			$(TARGET_DIR)/etc/celery.conf

	[ -f $(TARGET_DIR)/etc/systemd/system/celery.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/celery.service \
			$(TARGET_DIR)/etc/systemd/system/celery.service

	[ -f $(TARGET_DIR)/etc/systemd/system/celerybeat.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/celerybeat.service \
			$(TARGET_DIR)/etc/systemd/system/celerybeat.service

	[ -f $(TARGET_DIR)/etc/systemd/system/celerycam.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/celerycam.service \
			$(TARGET_DIR)/etc/systemd/system/celerycam.service

	[ -f $(TARGET_DIR)/etc/systemd/system/emperor.uwsgi.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/emperor.uwsgi.service \
			$(TARGET_DIR)/etc/systemd/system/emperor.uwsgi.service

	[ -f $(TARGET_DIR)/etc/systemd/system/mount-data-partition.service ] || \
		$(INSTALL) -D -m 644 package/remotemanager/mount-data-partition.service \
			$(TARGET_DIR)/etc/systemd/system/mount-data-partition.service

	ln -fs /tmp/ssh_host_key $(TARGET_DIR)/etc/ssh_host_key
	ln -fs /tmp/ssh_host_key.pub $(TARGET_DIR)/etc/ssh_host_key.pub

	ln -fs /tmp/ssh_host_rsa_key $(TARGET_DIR)/etc/ssh_host_rsa_key
	ln -fs /tmp/ssh_host_rsa_key.pub $(TARGET_DIR)/etc/ssh_host_rsa_key.pub

	ln -fs /data/ssh_host_dsa_key $(TARGET_DIR)/etc/ssh_host_dsa_key
	ln -fs /data/ssh_host_dsa_key.pub $(TARGET_DIR)/etc/ssh_host_dsa_key.pub

	ln -fs /data/ssh_host_ecdsa_key $(TARGET_DIR)/etc/ssh_host_ecdsa_key
	ln -fs /data/ssh_host_ecdsa_key.pub $(TARGET_DIR)/etc/ssh_host_ecdsa_key.pub

	ln -fs /data/ssh_host_ed25519_key $(TARGET_DIR)/etc/ssh_host_ed25519_key
	ln -fs /data/ssh_host_ed25519_key.pub $(TARGET_DIR)/etc/ssh_host_ed25519_key.pub


	mkdir -p $(TARGET_DIR)/etc/systemd/system/multi-user.target.wants

	ln -fs ../celery.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/celery.service

	ln -fs ../celerybeat.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/celerybeat.service

	ln -fs ../celerycam.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/celerycam.service

	ln -fs ../emperor.uwsgi.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/emperor.uwsgi.service

	ln -fs ../mount-data-partition.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/mount-data-partition.service

	mkdir -p $(TARGET_DIR)/etc/uwsgi/vassals

	[ -f $(TARGET_DIR)/etc/uwsgi/emperor.ini ] || \
		$(INSTALL) -D -m 644 package/remotemanager/emperor.ini \
			$(TARGET_DIR)/etc/uwsgi/emperor.ini

	ln -fs $(REMOTEMANAGER_DESTDIR)/uwsgi.ini \
		$(TARGET_DIR)/etc/uwsgi/vassals/remotemanager.ini

	ln -fs $(REMOTEMANAGER_DESTDIR)/recovery_interface/uwsgi.ini \
		$(TARGET_DIR)/etc/uwsgi/vassals/recovery.ini

	rm -f $(TARGET_DIR)/etc/nginx/nginx.conf

	$(INSTALL) -D -m 644 package/remotemanager/nginx.conf \
		$(TARGET_DIR)/etc/nginx/nginx.conf

	$(REMOTEMANAGER_ETHERNET_INTERFACE_INSTALL_INIT_SYSTEMD)

endef

$(eval $(generic-package))
$(eval $(host-generic-package))
