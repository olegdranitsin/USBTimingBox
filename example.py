from rrUSBTimingBox import rrUSB
from time           import sleep
from datetime       import datetime

SERIAL_PORT = 'COM3'            #for Windows systems
#SERIAL_PORT = '/dev/ttyUSB0'   #for Unix systems

def DBinsert(passings):
    ## Writes passing time and entire passing line to database
    printNewLine = len(passings)>0
    for n in range(0, len(passings)):
        print datetime.fromtimestamp(passings[n].timeSinceEpoch).isoformat(' ') + " : " + passings[n].passingString,
        if printNewLine: print ""
    ## do something here to place passings into database
    ##
#end DBinsert

class NewApp(object):
    def __init__(self):
        self.epochRef      = ''
        self.timeStampRef  = ''

myApp                   = NewApp()  # Initalise application
myDevice                = rrUSB(SERIAL_PORT)   # Connection to USB Timing Box

# Initalise variables
myDevice.timingMode     = True      #
myDevice.useDTR         = True      # These three are already defaults on system startup
myDevice.autoPowerOff   = False     #

myDevice.loopId         = 5         #
myDevice.channel        = 4         # Set these only with user interaction
myDevice.loopPower      = 45        #

#myApp.epochRef, myApp.timeStampRef = myDevice.CreateTimeReference()
                                    # Optional as rrUSB().CreateTimeReference() is called
                                    # when initialised, and result stored as *.lastEpochRef, *.lastTickRef

# Run application
while True:
    #passings = myDevice.GetNewPassings(myApp.epochRef, myApp.timeStampRef)
                                    # Optional as rrUSB().CreateTimeReference() is called
                                    # when initialised, and result stored as *.lastEpochRef, *.lastTickRef
    passings = myDevice.GetNewPassings()
    if passings:
        DBinsert(passings)
    sleep(1)
