################################################################################
#
# noip
#
################################################################################

NOIP_VERSION = 2.1.9
NOIP_SITE = http://www.no-ip.com/client/linux
NOIP_SOURCE = noip-duc-linux.tar.gz
NOIP_LICENSE = GPLv2+
NOIP_LICENSE_FILES = COPYING

define NOIP_BUILD_CMDS
	sed -i -e "s:\(#define CONFIG_FILENAME\).*:\1 \"/etc/no-ip2.conf\":" \
		$(@D)/noip2.c
	$(MAKE) -C $(@D) CC="$(TARGET_CC)" CFLAGS="$(TARGET_CFLAGS)" \
		PREFIX=/usr CONFDIR=/etc
endef

define NOIP_INSTALL_TARGET_CMDS
	$(INSTALL) -m 0755 -D $(@D)/noip2 $(TARGET_DIR)/usr/sbin/noip2
endef

define NOIP_INSTALL_INIT_SYSTEMD
	[ -f $(TARGET_DIR)/etc/systemd/system/noip.service ] || \
		$(INSTALL) -D -m 644 package/noip/noip.service \
			$(TARGET_DIR)/etc/systemd/system/noip.service

	mkdir -p $(TARGET_DIR)/etc/systemd/system/multi-user.target.wants

	ln -fs ../noip.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/noip.service
endef

$(eval $(generic-package))
