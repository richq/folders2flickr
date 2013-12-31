"""configuration: Read the global or relative uploadr.ini file."""
import os
from ConfigParser import ConfigParser

class ConfigDict:
    """Singleton style/static initialisation wrapper thing"""
    def __init__(self):
        self.configdict = ConfigParser()
        for filename in (os.path.expanduser('~/.uploadr.ini'), 'uploadr.ini'):
            if os.path.exists(filename):
                print 'using uploadr.ini file "%s"' % os.path.abspath(filename)
                self.configdict.read(filename)
                break

    def get(self, configparam):
        """get the value from the ini file's default section."""
        return self.configdict.defaults()[configparam]

configdict = ConfigDict()
