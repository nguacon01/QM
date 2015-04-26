#!/usr/bin/env python
# encoding: utf-8
"""

"""
import sys
import os
import unittest
from ConfigParser import SafeConfigParser
import re

class defaultConfigParser(SafeConfigParser):
    """
    this is a subclass of ConfigParser.SafeConfigParser, providing default value for values
    will never raise an error on missing values
    """
    def get(self, section, option, default = None, raw = 0, vars = None):
        """read a value from the configuration, with a default value"""
        if self.has_option(section, option):
            vv = SafeConfigParser.get(self, section, option, raw = raw, vars = vars) # returns the string after "option = "
            vl = re.split('\s*#',vv)        # this removes trailing comments
            return vl[0]
        else:
            print "Using default value for {} : {}".format(option,default) # send message if option not in configfile
            return default
    def getword(self, section, option, default = None, raw = 0, vars = None):
        "read a value from the configuration, with a default value - takes the first word of the string"
        vv = self.get(section, option, default = str(default), raw = raw, vars = vars)
        v = vv.split()[0]
        return v
    def getint(self, section, option, default = 0, raw = 0, vars = None):
        """
        """
        v = self.getword(section, option, default = str(default), raw = raw, vars = vars).lower()
        val = int(v)
        return val
    def getfloat(self, section, option, default=0.0, raw=0, vars=None):
        """read a float value from the configuration, with a default value"""
        return float(self.getword(section, option, default=str(default), raw=raw, vars=vars))
    def getboolean(self, section, option, default="OFF", raw=0, vars=None):
        """read a boolean value from the configuration, with a default value"""
        v = self.getword(section, option, default=str(default), raw=raw, vars=vars)
        if v.lower() not in self._boolean_states:
            raise ValueError, 'Not a boolean: %s' % v
        return self._boolean_states[v.lower()]


if __name__ == '__main__':
    unittest.main()