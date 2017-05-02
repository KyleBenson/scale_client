import urllib2
import time


def wait_for_internet():
    """Returns when Internet access (to google.com) is established."""
    has_network = False
    while has_network != True:
        try:
            response = urllib2.urlopen('http://www.google.com', timeout=2)
            has_network = True
        except urllib2.URLError:
            time.sleep(5)
            continue
