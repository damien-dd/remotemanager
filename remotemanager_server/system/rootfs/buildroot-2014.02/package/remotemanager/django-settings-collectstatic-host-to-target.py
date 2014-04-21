import os
import sys
import imp


if __name__ == '__main__':
	assert(len(sys.argv) == 5)

	settings_orig = sys.argv[1]
	settings_host = sys.argv[2]
	prefix_host = sys.argv[3]
	prefix_target = sys.argv[4]

	settings = imp.load_source('*', settings_orig)
	
	f = open(settings_host, 'w')
	for constant in settings.__dict__:
		if not constant.isupper():
			continue

		if constant == 'STATIC_ROOT':
			settings.__dict__[constant] = os.path.join(prefix_target, settings.__dict__[constant][1:])
		elif constant == 'STATICFILES_DIRS':
			path_list = []
			for path in settings.__dict__[constant]:
				path_list.append(os.path.join(prefix_host, path[1:]))
			settings.__dict__[constant] = tuple(path_list)
			
		f.write('%s = %r\n' % (constant, settings.__dict__[constant]))
	f.close()