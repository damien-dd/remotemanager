################################################################################
#
# avrdude
#
################################################################################

AVRDUDE_VERSION = 6.1
AVRDUDE_SOURCE = avrdude-$(AVRDUDE_VERSION).tar.gz
AVRDUDE_SITE = http://download.savannah.gnu.org/releases/avrdude
AVRDUDE_LICENSE = GPLv2+
AVRDUDR_LICENSE_FILES = COPYING
# Sources coming from git, without generated configure and Makefile.in
# files.
#AVRDUDE_AUTORECONF = YES
AVRDUDE_DEPENDENCIES = libelf libusb libusb-compat ncurses \
	host-flex host-bison

ifeq ($(BR2_PACKAGE_LIBFTDI),y)
AVRDUDE_DEPENDENCIES += libftdi
endif

# if /etc/avrdude.conf exists, the installation process creates a
# backup file, which we do not want in the context of Buildroot.
define AVRDUDE_REMOVE_BACKUP_FILE
	$(RM) -f $(TARGET_DIR)/etc/avrdude.conf.bak
endef

AVRDUDE_POST_INSTALL_TARGET_HOOKS += AVRDUDE_REMOVE_BACKUP_FILE

$(eval $(autotools-package))
