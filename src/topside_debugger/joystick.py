import pygame
import time
import sys

pygame.init()

joystick_connected = False
while not joystick_connected:
	try:
		joystick = pygame.joystick.Joystick(0)
		print "Initialized joystick %s" % joystick.get_name()
		joystick_connected = True
	except pygame.error:
		print "Make sure a joystick is plugged in."
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			sys.exit("\nProgram closed by user.")

joystick.init()

def remap(value, left_min, left_max, right_min, right_max):
	# Figure out how 'wide' each range is
	left_span = left_max - left_min
	right_span = right_max - right_min

	# Convert the left range into a 0-1 range (float)
	value_scaled = (float(value - left_min) / float(left_span))

	# Convert the 0-1 range into a value in the right range.
	value_converted =  int(round(right_min + (value_scaled * right_span)))
	return value_converted

def compute_deflection(value, left_min=-1, left_max=1, right_min=0, 
		right_max=250, dead_zone=20, flatten=False):

		# Improves the sensitivity for small deflections but still allows 
		# you to access the whole range of movement with large deflections.
		# https://www.desmos.com/calculator/q68fesfgg7
		if (flatten):
			if (value > 0):
				value = pow(value, 2)
			else:
				value = -pow(value, 2)

		# Convert the 0-1 range into a value in the right range.
		value_converted =  remap(value, left_min, left_max, right_min, 
			right_max)

		center = (right_max / 2)
		absolute_deflection = abs(value_converted - center)
		deflection = value_converted - center
		
		print "Center + Deflection = %d + %d = %d" % (center, deflection, 
			(center + deflection))

		# Deadzone
		if (absolute_deflection <= dead_zone):
			return center

		if deflection >= 0:	
			return remap(center+deflection, center+dead_zone, 
				right_max, center, right_max)
		else:
			val = remap(center-deflection, center+dead_zone, 
				right_max, center, right_max)
			return right_max - val

try:
	while True:
		# Poll joystick.
		pygame.event.pump()
		for i in range(0, 4):
			axis = compute_deflection(joystick.get_axis(i))
			print axis
		time.sleep(0.25)
except KeyboardInterrupt:
	joystick.quit()