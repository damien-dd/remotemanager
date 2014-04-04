################################################################################
#
# redis
#
################################################################################

REDIS_VERSION = 2.6.17
REDIS_SITE = http://download.redis.io/releases
REDIS_LICENSE = BSD-3c (core); MIT and BSD family licenses (Bundled components)
REDIS_LICENSE_FILES = COPYING

# Redis doesn't support DESTDIR (yet, see
# https://github.com/antirez/redis/pull/609).  We set PREFIX
# instead.
REDIS_BUILDOPTS = $(TARGET_CONFIGURE_OPTS) \
    PREFIX=$(TARGET_DIR)/usr MALLOC=libc \

define REDIS_BUILD_CMDS
        $(TARGET_MAKE_ENV) $(MAKE) $(REDIS_BUILDOPTS) -C $(@D)
endef

define REDIS_INSTALL_TARGET_CMDS
        $(TARGET_MAKE_ENV) $(MAKE) $(REDIS_BUILDOPTS) -C $(@D) \
	    LDCONFIG=true install

	[ -f $(TARGET_DIR)/etc/redis.conf.default ] || \
		$(INSTALL) -D -m 644 $(@D)/redis.conf \
			$(TARGET_DIR)/etc/redis.conf.default

	[ -f $(TARGET_DIR)/etc/redis.conf ] || \
		ln -fs redis.conf.default \
			$(TARGET_DIR)/etc/redis.conf
endef

define REDIS_INSTALL_INIT_SYSTEMD
	[ -f $(TARGET_DIR)/etc/systemd/system/redis.service ] || \
		$(INSTALL) -D -m 644 package/redis/redis.service \
			$(TARGET_DIR)/etc/systemd/system/redis.service

	mkdir -p $(TARGET_DIR)/etc/systemd/system/multi-user.target.wants

	ln -fs ../redis.service \
		$(TARGET_DIR)/etc/systemd/system/multi-user.target.wants/redis.service
endef

$(eval $(generic-package))
