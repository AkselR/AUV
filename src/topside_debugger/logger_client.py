#!/usr/bin/python

import logging, logging.handlers

rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.DEBUG)
socketHandler = logging.handlers.SocketHandler('localhost',
                    logging.handlers.DEFAULT_TCP_LOGGING_PORT)
# don't bother with a formatter, since a socket handler sends the event as
# an unformatted pickle
rootLogger.addHandler(socketHandler)

# Now, we can log to the root logger, or any other logger. First the root...
logging.info("AUV initialization completed")

# Now, define a couple of other loggers which might represent areas in your
# application:

sensors = logging.getLogger("auv.sensors")
vision = logging.getLogger("auv.vision")

sensors.debug("Wrote mtSendBBUser (14 bytes) to sonar.")
sensors.info("Sonar configured to channel 2 (675 kHz).")
vision.warning("Encountered low light environment.")
vision.critical("Lost connection with camera 2!")