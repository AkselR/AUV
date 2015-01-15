#!/usr/bin/python

##############################################################################
# @file    ControlSystem.py
# @author  Stian Sandve, UiS Subsea
# @version V1.0.0
# @date    18-Dec-2014
# @brief   This provides a platform-independent console application for 
# 			controlling Njord (ROV developed by UiS Subsea) by a USB joystick.
#			To run this on a Mac, you may have to execute the following command:
# 			$ arch -i386 python ControlSystem.py
###############################################################################
# Copyright (c) 2014, UiS Subsea
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of UiS Subsea nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################

import serial
import pygame
import time
import sys
import configs
import logging

class ROV(object):

	# -------------------------------- CONSTANTS -------------------------------- #

	# Signal the start of a packet.
	START = 255
	#Signal the end of a packet.
	STOP = 251
	# Number of joystick axes.
	NUMBER_OF_AXES = 4
	# Where to put the button pressed value
	BUTTON_INDEX = 5
	# Where to put the hat switch position
	HAT_SWITCH_INDEX = 6
	# Minimum joystick deflection according to custom protocol.
	MIN_DEFLECTION = 0
	# Maximum joystick deflection according to custom protocol.
	MAX_DEFLECTION = 251
	# Minimum joystick deflection according to pygame.
	PYGAME_MIN_DEFLECTION = -1
	# Maximum joystick deflection according to pygame.
	PYGAME_MAX_DEFLECTION = 1

	# -------------------------------- FUNCTIONS -------------------------------- #

	def __init__(self):
		self.init_logging()

		# start byte, roll, pitch, yaw, throttle, button, hat, manip, manip, 
		# manip, manip, manip, stop byte
		self.rov_data = [self.START, 125, 125, 125, 125, 0, 125, 125, 125, 0, 0, self.STOP]
		self.initialize_joystick()
		self.connet_to_rov()

	def init_logging(self):
		logging_enabled = configs.parse_config_section("Logging")['enabled']
		logging_level = configs.parse_config_section("Logging")['level']
		log_to_file = configs.parse_config_section("Logging")['log_to_file']

		if logging_level.lower() == "critical":
			level = logging.CRITICAL
		elif logging_level.lower() == "info":
			level = logging.INFO
		elif logging_level.lower() == "warning":
			level = logging.WARNING
		elif logging_level.lower() == "error":
			level = logging.ERROR
		else:
			level = logging.DEBUG

		if log_to_file == "False":
			logging.basicConfig(format='%(levelname)s: %(message)s', level=level)
		else:
			logging.basicConfig(filename='rov.log', format='%(levelname)s: %(message)s', level=level)

		if logging_enabled == "False":
			logging.disable(logging.CRITICAL)

		self.logger = logging.getLogger("ROV")
		self.logger.info("\n---------- Logging started %s, %s ----------\n", 
			time.strftime("%d.%m.%y"), time.strftime("%H:%M:%S"))

	def connet_to_rov(self):

		# Read configs.
		cfg = configs.parse_config_section("Communication")
		port = cfg['port']
		baud_rate = int(cfg['baud_rate'])
		self.logger.debug("Com port = %s", port)
		self.logger.debug("Baud rate = %d", baud_rate)

		# Check if comport is connected. If not, wait one second and do another check.
		# This check goes on continuously until the vehicle is connected.
		com_port_connected = False
		while not com_port_connected:
			try:
				# Open Serial Connection to the FT232R.
				# timeout=None makes Serial.read() a blocking function.
				self.rov = serial.Serial(port=port, baudrate=baud_rate, 
					timeout=None, writeTimeout=None)
				com_port_connected = True
			except OSError:
				self.logger.warning("Could not find the requested com port." + \
				" Make sure that %s is connected.", self.PORT)
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					sys.exit("\nProgram closed by user.")

	def initialize_joystick(self):

		# Read configs.
		cfg = configs.parse_config_section("Joystick")
		self.dead_zone = int(cfg['dead_zone'])
		self.flatten = bool(cfg['flatten'])
		self.logger.debug("Joystick dead zone = %d", self.dead_zone)
		self.logger.debug("Flatten joystick deflection = %r", self.flatten)

		# Initialize a joystick object.
		pygame.init()

		# Check if joystick is connected. If not, wait one second and do another check.
		# This check goes on continuously until a joystick is connected.
		joystick_connected = False
		while not joystick_connected:
			try:
				self.joystick = pygame.joystick.Joystick(0)
			except pygame.error:
				self.logger.warning("Make sure a joystick is plugged in.")
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					sys.exit("\nProgram closed by user.")

		self.joystick.init()
		self.logger.info("Initialized Joystick : %s", self.joystick.get_name())

	# The joystick produces values in the range -1 to 1. We want to values
	# to go from 0 to 250. This function can convert from/to any range.
	# You can also provide the function with a dead zone to compensate for inaccuracies
	# in the values provided by the joystick.
	def compute_deflection(self, value, left_min=-1, left_max=1, right_min=0, 
		right_max=251, dead_zone=5, flatten=False):

		# Improves the sensitivity for small deflections but still allows 
		# you to access the whole range of movement with large deflections.
		# https://www.desmos.com/calculator/q68fesfgg7
		if (flatten):
			if (value > 0):
				value = pow(value, 2)
			else:
				value = -pow(value, 2)

		# Figure out how 'wide' each range is
		left_span = left_max - left_min
		right_span = right_max - right_min

		# Convert the left range into a 0-1 range (float)
		value_scaled = float(value - left_min) / float(left_span)

		# Convert the 0-1 range into a value in the right range.
		value_converted =  int(right_min + (value_scaled * right_span))

		center = right_max / 2
		deflection = abs(value_converted - center)

		# Deadzone
		if (deflection <= dead_zone):
			value_converted = center

		return value_converted

	def prepare_joystick_data(self):
		# Put the four joystick axes in the data array that will be sent to the ROV.

		# Roll and pitch are the first two axes on the joystick.
		for a in range(0, 2):
			self.rov_data[a+1] = self.compute_deflection(self.joystick.get_axis(a), 
				flatten=self.flatten)

		# Throttle is the second axis on the joystick.
		throttle = self.compute_deflection(self.joystick.get_axis(2), 
			flatten=self.flatten)

		# Yaw is the third axis on the joystick.
		self.rov_data[3] = self.compute_deflection(self.joystick.get_axis(3),
			flatten=self.flatten)

		# We want to reverse the throttle axis to make it more intuitively
		# to fly the ROV.
		self.rov_data[4] = - (throttle - (self.MAX_DEFLECTION-1))

		self.rov_data[self.HAT_SWITCH_INDEX] = self.get_hat_switch_position()

		# Reset the button value set in previous call.
		self.rov_data[self.BUTTON_INDEX] = 0

		# Search for pressed buttons and stop when one is found.
		# Put the button number in the rov data array.
		for b in range(0, self.joystick.get_numbuttons()):
			if (self.joystick.get_button(b)) != 0:
				self.rov_data[self.BUTTON_INDEX] = b+1
				break

	def get_hat_switch_position(self):
		
		x, y = self.joystick.get_hat(0)

		if (x == 0 and y == 1): # Up
			return 1 << 3
		elif (x == 0 and y == -1): # Down
			return 1 << 2
		elif (x == -1 and y == 0): # Left
			return 1 << 1 
		elif (x == 1 and y == 0): # Right
			return 1 << 0
		else:
			return 0

	# Convert byte to int.
	def bytes_to_int(self, str):
		return int(str.encode('hex'), 16)

	def run(self):
		try:
			running = True
		   	while running:

		    	# Wait for ROV to send stop byte.
				indata = self.bytes_to_int(self.rov.read())
				while(indata != self.STOP):
					print indata
					indata = self.bytes_to_int(self.rov.read())

				# Poll joystick.
				pygame.event.pump()

				# Store joystick state in data in rov_data.
				self.prepare_joystick_data()

				# Print the message for debugging purposes.
				self.logger.debug("Transmitting data to ROV")
				self.logger.debug(self.rov_data)
				# Write the data to the ROV.	
				self.rov.write(self.rov_data)

		except KeyboardInterrupt:
		    self.joystick.quit()
		    self.rov.close()

# -------------------------------- MAIN ------------------------------------- #

def main():
	rov = ROV()
	rov.run()

if __name__ == "__main__": main()
