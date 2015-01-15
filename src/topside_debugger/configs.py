#!/usr/bin/python

import ConfigParser

def parse_config_section(section):
	
	Config = ConfigParser.ConfigParser()
	Config.read("rov_config.cfg")
	
	cfg = {}
	options = Config.options(section)
	for option in options:
		try:
			cfg[option]	= Config.get(section, option)
		except:
			print("Could not read section %s" % option)
			cfg[option] = None

	return cfg