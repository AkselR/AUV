#!/usr/bin/python

import serial
import logging
import sys
import time

class Arduino(object):

    def __init__(self):
        self.port = "/dev/tty.usbserial-A403MP4D"
        self.init_logging()
        self.connet_to_arduino()
        self.open_logfile()

    def open_logfile(self):
        self.logfile = open("power_consumption.dat", "w")

    def init_logging(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter("[%(levelname)s]: %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

    def connet_to_arduino(self):
            self.logger.info("Looking for port %s", self.port)
            com_port_connected = False
            while not com_port_connected:
                try:
                    # timeout=None makes Serial.read() a blocking function.
                    self.arduino = serial.Serial(port=self.port, baudrate=115200, 
                        timeout=None, writeTimeout=None)
                    com_port_connected = True
                except (OSError, serial.serialutil.SerialException):
                    self.logger.debug("Could not find the requested com port." + \
                    " Make sure that %s is connected.", self.port)
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        sys.exit("\nProgram closed by user.")
                        self.logfile.close()

    def read(self):
        self.logger.info("Beggining to read from arduino...")
        try:
            running = True
            while running:

                indata = self.arduino.readline()
                try:
                    voltage = float(indata)
                except ValueError:
                    self.logger.debug("Not a float %s", indata)
                    continue
                self.logger.info("Read %s", voltage)
                self.logfile.write(str(voltage) + ", ")

        except KeyboardInterrupt:
            self.logger.info("Application closed by user.")
            self.logfile.close()

def main():
    arduino = Arduino()
    arduino.read()

if __name__ == "__main__": main()
