#!/usr/bin/python

import serial
import time
import sys
import configs
import logging
import pid

class AUV(object):

    # ------------------------------ CONSTANTS ------------------------------ #

    # Signal the start of a packet.
    START = 255
    #Signal the end of a packet.
    STOP = 251
    MIN_DEFLECTION = 0
    # Maximum deflection according to custom protocol.
    MAX_DEFLECTION = 250
    CENTER = 125

    # ------------------------------ FUNCTIONS ------------------------------ #

    def __init__(self):
        self.init_logging()

        self.auv_data = [
        self.START, # start byte
        125,        # roll
        125,        # pitch
        125,        # yaw
        125,        # throttle
        0,          # button
        125,        # hat
        125,        # manipulator
        125,        # manipulator
        0,          # manipulator
        0,          # manipulator
        self.STOP   # stop byte
    ]
        
        self.connect_to_imu()
        self.init_pid()
        self.connet_to_auv()

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
            with open('auv.log', 'w'):
                pass
            file_handler = logging.FileHandler("auv.log")
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

    def init_pid(self):
        cfg = configs.parse_config_section("PID")
        p = int(cfg['P'])
        i = int(cfg['I'])
        d = int(cfg['D'])

        self.pid = pid.PID(p, i, d)
        self.pid.setPoint(1.3)

    def connet_to_auv(self):

        # Read configs.
        cfg = configs.parse_config_section("Communication")
        port = cfg['auv_port']
        baud_rate = int(cfg['auv_baud_rate'])
        self.logger.debug("AUV com port = %s", port)
        self.logger.debug("AUV baud rate = %d", baud_rate)

        # Check if comport is connected. If not, wait one second and perform
        # another check. This check goes on continuously until the vehicle is 
        # connected.
        self.logger.info("Looking for port %s", port)
        self.auv = self.connect_to_serial_port(port, baud_rate)

    def connet_to_imu(self):

        # Read configs.
        cfg = configs.parse_config_section("Communication")
        port = cfg['imu_port']
        baud_rate = int(cfg['imu_baud_rate'])
        self.logger.debug("IMU com port = %s", port)
        self.logger.debug("IMU baud rate = %d", baud_rate)

        # Check if comport is connected. If not, wait one second and perform
        # another check. This check goes on continuously until the vehicle is 
        # connected.
        self.logger.info("Looking for port %s", port)
        self.imu = self.connect_to_serial_port(port, baud_rate)

    def connect_to_serial_port(self, port, baud_rate):
        com_port_connected = False
        while not com_port_connected:
            try:
                # Open Serial Connection to the AUV.
                # timeout=None makes Serial.read() a blocking function.
                ser = serial.Serial(port=port, baudrate=baud_rate, 
                    timeout=None, writeTimeout=None)
                com_port_connected = True
            except (OSError, serial.serialutil.SerialException):
                self.logger.debug("Could not find the requested com port." + \
                " Make sure that %s is connected.", port)
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    sys.exit("\nProgram closed by user.")
        return ser

    def remap(self, value, left_min, left_max, right_min, right_max):
        # Figure out how 'wide' each range is
        left_span = left_max - left_min
        right_span = right_max - right_min

        # Convert the left range into a 0-1 range (float)
        value_scaled = (float(value - left_min) / float(left_span))

        # Convert the 0-1 range into a value in the right range.
        value_converted =  round(right_min + (value_scaled * right_span))
        return int(value_converted)

    def prepare_auv_data(self):
        self.auv_data[1] = self.CENTER
        self.auv_data[2] = self.CENTER
        self.auv_data[3] = self.CENTER
        self.auv_data[4] = self.pid.update(self.depth)

    # Convert byte to int.
    def bytes_to_int(self, str):
        return int(str.encode('hex'), 16)

    def read_imu_state(self):
        imu_state = self.imu.readline()
        self.heading, self.depth = imu_state.split(",")

    def read_auv_state(self):
        # Wait for AUV to send stop byte.
        indata = self.bytes_to_int(self.auv.read())
        while(indata != self.STOP):
            self.logger.debug("Input from AUV: %d", indata)
            indata = self.bytes_to_int(self.auv.read())

    def run(self):
        try:
            running = True
            while running:
                self.read_auv_state()
                self.read_imu_state()
                self.prepare_auv_data()

                # Print the message for debugging purposes.
                self.logger.debug("Transmitting data to AUV")
                self.logger.debug(self.auv_data)
                # Write the data to the AUV.    
                self.auv.write(self.auv_data)

        except KeyboardInterrupt:
            self.auv.close()
            self.imu.close()

# ------------------------------ MAIN ----------------------------------- #

def main():
    auv = AUV()
    auv.run()

if __name__ == "__main__": main()
