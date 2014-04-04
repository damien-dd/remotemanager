
#############################################################
#
# python-pip
#
#############################################################

PYTHON_PIP_VERSION = 1.5.4
PYTHON_PIP_SOURCE = pip-$(PYTHON_PIP_VERSION).tar.gz
PYTHON_PIP_SITE = https://pypi.python.org/packages/source/p/pip
PYTHON_PIP_DEPENDENCIES = python python-setuptools host-python-setuptools host-python-pip
PYTHON_PIP_LICENSE = MIT

# README.rst refers to the file "LICENSE" but it's not included

define PYTHON_PIP_BUILD_CMDS
	(cd $(@D); \
	PYTHONPATH="$(TARGET_DIR)/usr/lib/python$(PYTHON_VERSION_MAJOR)/site-packages" \
	$(HOST_DIR)/usr/bin/python setup.py build --executable=/usr/bin/python)
endef

define HOST_PYTHON_PIP_INSTALL_CMDS
	(cd $(@D); PYTHONPATH=$(HOST_DIR)/usr/lib/python$(PYTHON_VERSION_MAJOR)/site-packages \
	$(HOST_DIR)/usr/bin/python setup.py install --prefix=$(HOST_DIR)/usr)
endef

PYTHON_PIP_MODULES_LIST=$(call qstrip, $(BR2_PACKAGE_PYTHON_PIP_MODULES_ADDITIONAL))

ifneq ($(PYTHON_PIP_MODULES_LIST),)
define PYTHON_PIP_INSTALL_MODULES
	# Explanation of environment variables
	# PIP_DOWNLOAD_CACHE: all downloads go into the buildroot download folder
	# PIP_TARGET: this is where the packages end up
	# PIP_BUILD: where the packages are built - a subdirectory of the pip folder
	($(TARGET_CONFIGURE_OPTS) \
	PIP_DOWNLOAD_CACHE=$(BR2_DL_DIR) \
	PIP_TARGET=$(TARGET_DIR)/usr/lib/python$(PYTHON_VERSION_MAJOR)/site-packages \
	PIP_BUILD=$(BUILD_DIR)/python-pip-$(PYTHON_PIP_VERSION)/packages \
	CC="$(TARGET_CC)"			\
	CFLAGS="$(TARGET_CFLAGS)" 	\
	LDSHARED="$(TARGET_CC) -shared" \
	LDFLAGS="$(TARGET_LDFLAGS)" 	\
	$(HOST_DIR)/usr/bin/pip install \
	$(PYTHON_PIP_MODULES_LIST));
endef
endif

define PYTHON_PIP_INSTALL_TARGET_CMDS
	$(PYTHON_PIP_INSTALL_MODULES)
endef

$(eval $(generic-package))
$(eval $(host-generic-package))
