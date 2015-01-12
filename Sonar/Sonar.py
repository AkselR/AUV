import serial
import time
from collections import namedtuple
import binascii
import sys

HEADER = '\x40'
LF = '\x0A'
HEX_LENGHT = '\x30\x30\x30\x38'
BIN_LENGTH = '\x08\x00'
TX_NDE = '\xFF'
RX_NDE = '\x02'
NO_BYTE = '\x03'
SEQ = '\x80'
NDE = '\x02'

MT_ALIVE_LENGTH = 22

MT_SEND_VERSION_ID = '\x17'
MT_VERSION_DATA_ID = '\x01'
MT_VERSION_DATA_LENGTH = 25

MT_SEND_BB_USER_ID = '\x18'
MT_BB_USER_DATA_ID = '\x06'
MT_BB_USER_DATA_LENGTH = 264

MT_SEND_DATA = '\x19'

REPLY_COMMAND_ID_IDX = 10

command = namedtuple("command", 
    "header hex_length bin_length tx_nde rx_nde no_byte command seq nde lf")

send_data = namedtuple("send_data", 
    "header hex_length bin_length tx_nde rx_nde no_byte command seq nde current_time lf")

# Serial communication baud rate. Must be the same as the ROVs baud rate.
BAUD_RATE = 115200

# Com port
COM_PORT = "COM5"

# Open Serial Connection to the sonar
# timeout=None makes Serial.read() a blocking function.
sonar = serial.Serial(port=COM_PORT, baudrate=BAUD_RATE, timeout=None, writeTimeout=None)

def send_command(cmd):
    # mtSendData is 18 bytes long, all the other commands are 14 bytes long.
    c = None
    if cmd is not MT_SEND_DATA:
        c = command(header=HEADER, 
            hex_length=HEX_LENGHT, bin_length=BIN_LENGTH, tx_nde=TX_NDE, rx_nde=RX_NDE, 
            no_byte=NO_BYTE, command=cmd, seq=SEQ, nde=NDE, lf=LF)
    else:
        c = send_data(header=HEADER, 
                hex_length=HEX_LENGHT, bin_length=BIN_LENGTH, tx_nde=TX_NDE, rx_nde=RX_NDE, 
                no_byte=NO_BYTE, command=cmd, seq=SEQ, nde=NDE, current_time=0, lf=LF)
        
    for b in c:
        sonar.write(b)
        
def read_message(length, command_id):
    message = []
    
    while len(message) != length and message[REPLY_COMMAND_ID_IDX] != command_id:
        message = []
        
        indata = sonar.read()
        while(indata != HEADER):
            indata = sonar.read()
    
        message.append(bytes_to_hex(indata))
    
        indata = sonar.read()
        while(indata != LF):
            message.append(bytes_to_hex(indata))
            indata = sonar.read()
    
        message.append(bytes_to_hex(indata))
    
    return message

def alive():
    indata = binascii.hexlify(bytearray(sonar.read(22)))
    for idx, b in enumerate(indata):
        sys.stdout.write(b)
        if (idx-1) % 2 == 0:
            print ", ",
    print "\n\n"

def send_version():
    send_command(MT_SEND_VERSION_ID)

def version_data():
    indata = sonar.read()

    while(indata != HEADER):
        indata = sonar.read()

    version = []
    version.append(binascii.hexlify(bytearray(indata)))

    indata = sonar.read()
    while(indata != LF):
        version.append(binascii.hexlify(bytearray(indata)))
        indata = sonar.read()

    version.append(binascii.hexlify(bytearray(indata)))

    if (len(version) == MT_VERSION_DATA_LENGTH):
        for idx, b in enumerate(version):
            sys.stdout.write(b)
            if ((idx-1) % 2)/2 == 0 and idx < len(version)-1:
                print ", ",
        print "\n\n"

def send_BBUser():
    send_command(MT_SEND_BB_USER_ID)

def BBUser_data():
    # NOT IMPLEMENTED
    print "NOT IMPLEMENTED"

def head_command():
    # NOT IMPLEMENTED
    print "NOT IMPLEMENTED"

def send_data():
    send_command(MT_SEND_DATA)

def head_data():
    # NOT IMPLEMENTED
    print "NOT IMPLEMENTED"
    
def bytes_to_hex(byte):
    #return byte.encode('hex', 16)
    return binascii.hexlify(bytearray(byte))

def sonar_read(numberOfBytes):
    inData = bytes_to_hex(sonar.read())
    return inData

try:
    while True:
        send_version()
        version_data()
        time.sleep(0.2)
except KeyboardInterrupt:
    sonar.close()
