import re

andy = "inet addr:169.254.8.240  Bcast:169.254.255.255  Mask:255.255.0.0"

m = re.search("addr:(.+?) ", andy)
if m:
	found = m.group(1)
	print found

print 'Nothing found'
