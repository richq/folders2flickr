"""configuration: Read the global or relative uploadr.ini file."""
import os
from ConfigParser import ConfigParser

__copyright__ = "(C) 2014 Richard Quirk. GNU GPL v2 or later."

class ConfigDict:
    """Singleton style/static initialisation wrapper thing"""
    def __init__(self):
        self.configdict = ConfigParser()
        foundini = False
        paths = (os.path.abspath('uploadr.ini'), os.path.expanduser('~/.uploadr.ini'))
        for filename in paths:
            if os.path.exists(filename):
                print 'using uploadr.ini file "%s"' % os.path.abspath(filename)
                self.configdict.read(filename)
                foundini = True
                break
        if not foundini:
            raise IOError('Missing configuration file: ' + ' '.join(paths))


    def get(self, configparam, default=None):
        """get the value from the ini file's default section."""
        defaults = self.configdict.defaults()
        if configparam in defaults:
            return defaults[configparam]
        if default:
            return default
        raise KeyError(configparam)

configdict = ConfigDict()
