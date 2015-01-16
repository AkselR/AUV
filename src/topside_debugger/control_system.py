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

	# ------------------------------ CONSTANTS ------------------------------ #

	# Signal the start of a packet.
	START = 255
	#Signal the end of a packet.
	STOP = 251
	# Number of joystick axes.
	NUMBER_OF_AXES = 4
	# Where to put the button pressed value
	BUTTON_INDEX = 5
	# The index of where the first joystick axis is to be put.
	PILOT_AXIS_START = 1
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

	# ------------------------------ FUNCTIONS ------------------------------ #

	def __init__(self):
		self.init_logging()

		self.rov_data = [
		self.START, # start byte
		125, 		# roll
		125, 		# pitch
		125, 		# yaw
		125, 		# throttle
		0,	 		# button
		125, 		# hat
		125, 		# manipulator
		125, 		# manipulator
		0, 	 		# manipulator
		0, 	 		# manipulator
		self.STOP 	# stop byte
		]

		self.initialize_joystick()
		self.connet_to_rov()

	def init_logging(self):
		cfg = configs.parse_config_section("Logging")
		logging_enabled = cfg['enabled']
		logging_level = cfg['level']
		log_to_file = cfg['log_to_file']
		log_to_console = cfg['log_to_console']

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

		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(level)
		log_formatter = logging.Formatter("[%(levelname)s]: %(message)s")

		if log_to_file == "True":
			# Truncate existing log.
			with open('rov.log', 'w'):
				pass
			file_handler = logging.FileHandler("rov.log")
			file_handler.setFormatter(log_formatter)
			self.logger.addHandler(file_handler)
		if log_to_console == "True":
			console_handler = logging.StreamHandler()
			console_handler.setFormatter(log_formatter)
			self.logger.addHandler(console_handler)

		if logging_enabled == "False":
			logging.disable(logging.CRITICAL)

		self.logger.info("\n---------- Logging started %s, %s ----------\n", 
			time.strftime("%d.%m.%y"), time.strftime("%H:%M:%S"))

	def connet_to_rov(self):

		# Read configs.
		cfg = configs.parse_config_section("Communication")
		port = cfg['port']
		baud_rate = int(cfg['baud_rate'])
		self.logger.debug("Com port = %s", port)
		self.logger.debug("Baud rate = %d", baud_rate)

		# Check if comport is connected. If not, wait one second and perform
		# another check. This check goes on continuously until the vehicle is 
		# connected.
		self.logger.info("Looking for port %s", port)
		com_port_connected = False
		while not com_port_connected:
			try:
				# Open Serial Connection to the FT232R.
				# timeout=None makes Serial.read() a blocking function.
				self.rov = serial.Serial(port=port, baudrate=baud_rate, 
					timeout=None, writeTimeout=None)
				com_port_connected = True
			except OSError:
				self.logger.error("Could not find the requested com port." + \
				" Make sure that %s is connected.", self.PORT)
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					sys.exit("\nProgram closed by user.")

	def initialize_joystick(self):

		# Read configs.
		cfg = configs.parse_config_section("Joystick")
		self.gain = float(cfg['gain'])

		if cfg['flatten'] == "False":
			self.flatten = False
		else:
			self.flatten = True

		self.increase_gain_button = int(
			cfg['increase_gain_button'])
		self.decrease_gain_button = int(
			cfg['decrease_gain_button'])

		self.toggle_flatten_button = int(
			cfg['toggle_flatten_button'])
		
		self.dead_zone = int(cfg['dead_zone'])
		self.logger.debug("Joystick dead zone = %d", self.dead_zone)
		self.logger.debug("Flatten joystick deflection = %r", self.flatten)
		self.logger.debug("Increase gain button = %d", 
			self.increase_gain_button)
		self.logger.debug("Decrease gain button = %d", 
			self.decrease_gain_button)

		# Initialize a joystick object.
		pygame.init()

		# Check if joystick is connected. If not, wait one second and perform
		# another check. This check goes on continuously until a joystick is 
		# connected.
		self.logger.info("Looking for a joystick...")
		joystick_connected = False
		while not joystick_connected:
			try:
				self.joystick = pygame.joystick.Joystick(0)
			except pygame.error:
				self.logger.error("Make sure a joystick is plugged in.")
				try:
					time.sleep(1)
				except KeyboardInterrupt:
					sys.exit("\nProgram closed by user.")

		self.joystick.init()
		self.logger.info("Initialized Joystick : %s", self.joystick.get_name())

	# The joystick produces values in the range -1 to 1. We want to values
	# to go from 0 to 250. This function can convert from/to any range.
	# You can also provide the function with a dead zone to compensate for 
	# inaccuracies in the values provided by the joystick.
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
		# Put the four joystick axes in the data array that will be sent to the 
		# ROV.

		# Roll and pitch are the first two axes on the joystick.
		for a in range(0, 2):
			self.rov_data[a+1] = self.compute_deflection(
				self.joystick.get_axis(a), 
				flatten=self.flatten) * self.gain

		# Throttle is the second axis on the joystick.
		throttle = self.compute_deflection(self.joystick.get_axis(2), 
			flatten=self.flatten)

		# Yaw is the third axis on the joystick. The deflection should not
		# be affected by gain settings because we always need maximum power
		# in the vertical direction.
		yaw = self.compute_deflection(self.joystick.get_axis(3),
			flatten=self.flatten) * self.gain

		# The vehicle is very sensitive on this axis, therefore we halve
		# the deflection to improve handling.
		self.rov_data[3] = yaw / 2

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

		if self.rov_data[self.BUTTON_INDEX] == self.increase_gain_button:
			self.set_gain(self.gain + 0.1)
		elif self.rov_data[self.BUTTON_INDEX] == self.decrease_gain_button:
			self.set_gain(self.gain - 0.1)
		elif self.rov_data[self.BUTTON_INDEX] == self.toggle_flatten_button:
			if not self.flatten:
				self.flatten = True
			else:
				self.flatten = False

	def set_gain(self, gain):
		if gain > 1 and gain <= 0:
			return

		self.gain = gain

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

	def log_currenct_state(self):
		self.logger.info("Gain: %d", self.gain)
		self.logger.info("Flatten: %r", self.flatten)

	def run(self):
		try:
			running = True
		   	while running:
		   		self.log_currenct_state()

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

# ------------------------------ MAIN ----------------------------------- #

def main():
	rov = ROV()
	rov.run()

if __name__ == "__main__": main()
