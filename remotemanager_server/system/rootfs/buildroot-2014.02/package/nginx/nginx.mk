################################################################################
#
# nginx
#
################################################################################

NGINX_VERSION_MAJOR = 1.4
NGINX_VERSION = $(NGINX_VERSION_MAJOR).7
NGINX_SOURCE = nginx-$(NGINX_VERSION).tar.gz
NGINX_SITE = http://nginx.org/download
NGINX_LICENSE = BSD-3c
NGINX_LICENSE_FILES = COPYING
NGINX_DEPENDENCIES = pcre
NGINX_CONF_OPT = \
	--prefix=/usr/local/nginx \
	--pid-path=/var/run/nginx.pid \
	--conf-path=/etc/nginx/nginx.conf \
	--error-log-path=/var/log/nginx-error.log \
	--http-log-path=/var/log/nginx-access.log \
	--http-client-body-temp-path=/var/tmp/nginx/client/ \
	--http-proxy-temp-path=/var/tmp/nginx/proxy/ \
	--http-fastcgi-temp-path=/var/tmp/nginx/fcgi/ \
	--http-uwsgi-temp-path=/var/tmp/nginx/uwsgi/ \
	--http-scgi-temp-path=/var/tmp/nginx/scgi/ \
	--crossbuild=Linux:arm \
	--with-cc-opt="$(CFLAGS)" \
	--with-ld-opt="$(LDFLAGS)" \
	--with-endian=little \
	--with-int=4 \
	--with-long=4 \
	--with-long-long=8 \
	--with-ptr-size=4 \
	--with-sig-atomic-t=4 \
	--with-size-t=4 \
	--with-off-t=4 \
	--with-time-t=4 \
	--with-sys-nerr=132

ifeq ($(BR2_PACKAGE_NGINX_OPENSSL),y)
NGINX_DEPENDENCIES += openssl
NGINX_CONF_OPT += --with-http_ssl_module
endif

ifeq ($(BR2_PACKAGE_NGINX_ZLIB),y)
NGINX_DEPENDENCIES += zlib
else
NGINX_CONF_OPT += --without-http_gzip_module
endif

define NGINX_INSTALL_INIT_SYSTEMD
	[ -f $(TARGET_DIR)/etc/systemd/system/nginx.service ] || \
		$(INSTALL) -D -m 644 package/nginx/nginx.service \
			$(TARGET_DIR)/etc/systemd/system/nginx.service

	mkdir -p $(TARGET_DIR)/etc/systemd/system/multi-user.target.wants

	ln -fs ../nginx.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/nginx.service
endef

$(eval $(autotools-package))
