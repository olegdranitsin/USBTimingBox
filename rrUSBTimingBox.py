import serial
import time
import string
import os
import math
import inspect
from time       import sleep
from datetime   import datetime                 #only used for command line and RRFileParser()


SERIAL_PORT = 'COM3'            #for Windows systems
#SERIAL_PORT = '/dev/ttyUSB0'   #for Unix systems
SERIAL_BAUDRATE = 19200

SUPPRESS_CONFSET_PRINT = True
SUPPRESS_CONFGET_PRINT = True


class rrUSB(object):
     
    def __init__(self, sPort = SERIAL_PORT):
    # DESCRIPTION: Opens serial port for connection to USB Timing Box. Resets variables.
        
        self.conn             = serial.Serial()
        self.conn.port        = sPort
        self.conn.baudrate    = SERIAL_BAUDRATE
        self.conn.bytesize    = serial.EIGHTBITS     #number of bits per bytes
        self.conn.parity      = serial.PARITY_NONE   #set parity check: no parity
        self.conn.stopbits    = serial.STOPBITS_ONE  #number of stop bits
        #self.conn.timeout    = None                 #block read
        self.conn.timeout     = 1                    #non-block read
        #self.conn.timeout    = 2                    #timeout block read
        self.conn.xonxoff     = False                #disable software flow control
        self.conn.rtscts      = False                #disable hardware (RTS/CTS) flow control
        self.conn.dsrdtr      = False                #disable hardware (DSR/DTR) flow control
        self.conn.writeTimeout = 1                   #timeout for write
        self.conn.open()

        # Switch to ASCII protocol
        self.conn.flushInput()
        self.conn.setDTR(False)
        self.WriteSerial('ASCII\n')	             #Put USB-Box into ASCii Mode
        sleep(0.2)
        self.conn.flushInput()

        # Store static system information.
        self.deviceID           = self.__deviceID__
        self.firmwareVersion    = self.__firmwareVersion__
        self.hardwareVersion    = self.__hardwareVersion__
        self.boxType            = self.__boxType__
        self.systemInfo         = "A-" + str(self.deviceID) + ", " + str(self.boxType) + ", FW" + str(self.firmwareVersion) + ", HW" + str(self.hardwareVersion)
        print "race|result Active System"
        print self.systemInfo
        print ""
        
        # Initalise variables.
        self.__warnings__   = ""
        self.startID        = 00000000               #has to Increment --- save to tmp file to automaticaly 
        self.passings       = []
        self.beacons        = {}
        self.beaconErrors   = ""
        self.beaconWarnings = ""

        # Store Time References
        self.lastEpochRef, self.lastTickRef  = self.epochReferenceTime

        print self.warnings
        #Ready to go!
    # end __init__


##                                                  ##
## HELPER COMMANDS FOR SERIAL CONNECTION            ##
##                                                  ##
    
    def close(self):
        self.conn.close()
 
    def WriteSerial(self, data):
        try:
            self.conn.write(data)
        except serial.SerialException as e:
            self.close()
            print "ERROR: Unable to speak with USB Timing Box. Serial Connection closed."
            pass
        
    def ReadSerial(self):
        return self.conn.readline().replace("\n", "")

    def cmdLine(self, cmd):
        self.WriteSerial(cmd)
        sleep(0.2)
        outLine = self.conn.readall().split("\n")
        for line in outLine:
            print "rrUSB ->  " + line
        print ""
        self.conn.flushInput()

##                                                  ##
## CONFSET, CONFGET, and INFOGET COMMANDS           ##
##                                                  ##
    
    def ConfSet(self, param, val):
        # DESCRIPTION: Translates commands to parameter/value pairs
        param               = format(param  , '02x')
        val                 = format(val    , '02x')
        cmd                 = 'CONFSET;' + param + ';' + val + '\n'
        self.WriteSerial(cmd)
        ret                 = self.ReadSerial()
        err                 = ret.split(';')[1]
        if not SUPPRESS_CONFSET_PRINT: print ret
        if err == '00':
            if not SUPPRESS_CONFSET_PRINT: print self.ReadSerial()
        else:
            print 'Error: ' + param + ';' + val + ';' + err
        sleep(0.2)
        self.conn.flushInput()

    def ConfGet(self, param):
        # DESCRIPTION: Translates commands to parameter/value pairs
        param               = format(param  , '02x')
        cmd                 = 'CONFGET;' + param + '\n'
        self.WriteSerial(cmd)
        ret                 = self.ReadSerial()
        err                 = ret.split(';')[1]
        if not SUPPRESS_CONFGET_PRINT: print ret
        if err == '00':
            ret = self.ReadSerial()
            #print ret
        else:
            print 'Error: ' + param + ';' + err
        sleep(0.2)
        self.conn.flushInput()
        return ret.split(';')[1]

    def InfoGet(self, param):
        # DESCRIPTION: Translates commands to parameter/value pairs
        param               = format(param  , '02x')
        cmd                 = 'INFOGET;' + param + '\n'
        self.WriteSerial(cmd)
        ret                 = self.ReadSerial()
        err                 = ret.split(';')[1]
        if not SUPPRESS_CONFGET_PRINT: print ret
        if err == '00':
            ret = self.ReadSerial()
            if not SUPPRESS_CONFGET_PRINT: print self.ReadSerial()
        else:
            print 'Error: ' + param + ';' + err
        sleep(0.2)
        self.conn.flushInput()
        return ret.split(';')[1]
        
##                                                  ##
## ALPHA COMMANDS FOR GETTING/SETTING PARAMETERS    ##
##                                                  ##

    # PushPreWarn
    @property
    def pushPreWarn(self):
        return bool(int(self.ConfGet(1)))

    @pushPreWarn.setter
    def pushPreWarn(self, value):
        self.ConfSet(1, value)
    #END PushPreWarn

    # BlinkOnRepeat
    @property
    def blinkOnRepeat(self):
        return bool(int(self.ConfGet(2)))

    @blinkOnRepeat.setter
    def blinkOnRepeat(self, value):
        self.ConfSet(2, value)
    #END PushPreWarn

    # BeepOut
    @property
    def beepOut(self):
        return bool(int(self.ConfGet(3)))

    @blinkOnRepeat.setter
    def beepOut(self, value):
        self.ConfSet(3, value)
    #END BeepOut
        
    # AUTO-POWER OFF
    @property
    def autoPowerOff(self):
        return bool(int(self.ConfGet(4)))

    @autoPowerOff.setter
    def autoPowerOff(self, value):
        self.ConfSet(4, value)
    #END AUTO-POWER OFF

    # TIMING OR SCAN MODE
    @property
    def timingMode(self):
        return bool(int(self.ConfGet(5))-5)

    @timingMode.setter
    def timingMode(self, value):
        if value==0 or value==1 or value==True or value==False: value=int(value)+5
        if value==5 or value == 6:
            self.ConfSet(5, value)
        else:
            raise ValueError('timingMode must be Boolean')
            
    #END AUTO-POWER OFF

    # CHANNEL
    @property
    def channel(self):
        return int(self.ConfGet(6))+1

    @channel.setter
    def channel(self, value):
        self.ConfSet(6, value-1)
    #END CHANNEL

    # LOOP ID
    @property
    def loopId(self):
        return int(self.ConfGet(7))+1

    @loopId.setter
    def loopId(self, value):
        self.ConfSet(7, value-1)
    # END LOOP ID

    # LOOP POWER
    @property
    def loopPower(self):
        return int(self.ConfGet(8),16)

    @loopPower.setter
    def loopPower(self, value):
        self.ConfSet(8, min(max(value,0),100))
    # END LOOP POWER

    # UseDTR
    @property
    def useDTR(self):
        return bool(int(self.ConfGet(10)))

    @useDTR.setter
    def useDTR(self, value):
        self.ConfSet(10, value)
    # END UseDTR

##                                                  ##
## ALPHA COMMANDS FOR GETTING INFO                  ##
##                                                  ##
    @property
    def __deviceID__(self):
        return int(self.InfoGet(1), 16)

    @property
    def __firmwareVersion__(self):
        return int(self.InfoGet(2),16)/10.0

    @property
    def __hardwareVersion__(self):
        return int(self.InfoGet(3),16)/10.0

    @property
    def __boxType__(self):
        rcv = self.InfoGet(4)
        if rcv=='0a': return 'AEx'
        if rcv=='1e': return 'AMB'
        if rcv=='28': return 'USB'

    @property
    def batteryVoltage(self):
        return int(self.InfoGet(5),16)

    # INFOGET;06 reserved

    @property
    def batteryState(self):
        rcv = self.InfoGet(7)
        if rcv == '00': return 'Fault'
        if rcv == '01': return 'Charging'
        if rcv == '02': return 'Reduced Charging'
        if rcv == '03': return 'Discharging'

    @property
    def batteryPercent(self):
        return int(self.InfoGet(8),16)

    @property
    def internalTemp(self):
        return int(self.InfoGet(9),16)

    @property
    def supplyVoltage(self):
        return int(self.InfoGet(10),16)/10.0

    @property
    def loopStatus(self):
        rcv = self.InfoGet(11)
        if rcv == '00': return 'OK'
        if rcv == '01': return 'FAULT'
        if rcv == '02': return 'Loop Limit'
        if rcv == '03': return 'Overvoltage Error'

## END ALPHA COMMANDS                               ##

##                                                  ##
## BEACONS FROM OTHER LOOPBOXES                     ##
##                                                  ##

    class NewBeacon(dict):
    # Dictionary for storing beacon values
        def __init__(self):
            self.beaconString      = ''
            self.device            = ''
            self.loopStatus        = ''
            self.mode              = ''
            self.loopData          = ''
            self.loopPower         = ''
            self.channel           = ''
            self.loopId            = ''
            self.powerStatus       = ''
            self.powerRead         = ''
            self.beaconIndex       = ''
            self.ticks             = ''
            self.channelNoisePeak  = ''
            self.channelNoiseAvg   = ''
            self.chipLQI           = ''
            self.chipRSSI          = ''
            self.beaconLQI         = ''
            self.beaconRSSI        = ''
        def clear(self):
            self.__init__()
        def __str__(self):
            return self.beaconString
        def __repr__(self):
            return "<rrUSB Beacon ("+self.device+"/"+hex(self.ticks)+")>"
        
    def UpdateBeacons(self):
        self.conn.flushInput()
        self.WriteSerial("BEACONGET\n")
        self.beaconErrors   = ""
        self.beaconWarnings = ""
        sleep(0.1)
        if self.ReadSerial().split(';')[1] == '00':
            self.beaconCount = int(self.ReadSerial(), 16)
            for j in range(0, self.beaconCount):
                beaconString = self.ReadSerial()
                beaconInfo = beaconString.split(';')
                deviceID = str(int(beaconInfo[0],16))
                thisBeacon                   = self.NewBeacon()
                thisBeacon.beaconString      = beaconString
                thisBeacon.device            = deviceID
                thisBeacon.loopStatus        = int(beaconInfo[1])
                thisBeacon.mode              = int(beaconInfo[2], 16)
                thisBeacon.loopData          = int(beaconInfo[3], 16)
                thisBeacon.loopPower         = int(beaconInfo[4], 16)
                thisBeacon.channel           = int(beaconInfo[5], 16) + 1
                thisBeacon.loopId            = int(beaconInfo[6], 16) + 1
                thisBeacon.powerStatus       = int(beaconInfo[7], 16)
                thisBeacon.powerRead         = int(beaconInfo[8], 16)
                thisBeacon.beaconIndex       = int(beaconInfo[9], 16)
                thisBeacon.ticks             = int(beaconInfo[10], 16)
                thisBeacon.channelNoisePeak  = int(beaconInfo[11], int(16))
                thisBeacon.channelNoiseAvg   = int(beaconInfo[12], 16)
                thisBeacon.chipLQI           = int(beaconInfo[13], 16)
                thisBeacon.chipRSSI          = int(beaconInfo[14], 16)
                thisBeacon.beaconLQI         = int(beaconInfo[15], 16)
                thisBeacon.beaconRSSI        = int(beaconInfo[16], 16)

                self.beacons[deviceID] = thisBeacon

                if thisBeacon.loopStatus > 0:       self.beaconErrors      += (deviceID + ": LOOP ERROR (" + beaconInfo[1] + ")\n")
                if thisBeacon.powerStatus==0:       self.beaconWarnings    += (deviceID + ": ON BATTERY POWER\n")
                if thisBeacon.channelNoiseAvg > 7:  self.beaconWarnings    += (deviceID + ": HIGH CHANNEL NOISE\n")
                
        self.conn.flushInput()

##                                                  ##
## PASSING PARSER AND RETRIEVAL                     ##
##                                                  ##

    class NewPassing(dict):
    # Dictionary for storing beacon values
        def __init__(self):
            self.passingString      = ''
            self.transponder        = ''
            self.wakeupCount        = ''
            self.ticks              = ''
            self.timeSinceEpoch     = ''
            self.detectionCount     = ''
            self.rssi               = ''
            self.batteryVoltage     = ''
            self.temperature        = ''
            self.loopOnly           = ''
            self.loopId             = ''
            self.channelId          = ''
            self.status             = ''
            self.internalData       = ''
        def clear(self):
            self.__init__()
        def __str__(self):
            return self.passingString
        def __repr__(self):
            return "<rrUSB Passing ("+self.transponder+"/"+hex(self.ticks)+")>"

    def ParsePassing(self, rcv, epochRef, timeStampRef):
        data = rcv.split(';')
        singlePassing = self.NewPassing()
        singlePassing.passingString      = rcv
        singlePassing.transponder        = data[0]
        singlePassing.wakeupCount        = int(data[1]   ,16)
        singlePassing.ticks              = int(data[2]   ,16)
        singlePassing.detectionCount     = int(data[3]   ,16)
        singlePassing.rssi               = int(data[4]   ,16)
        singlePassing.batteryVoltage     = int(data[5]   ,16)
        singlePassing.temperature        = int(data[6]   ,16)
        singlePassing.loopOnly           = bool(int(data[7]))
        singlePassing.loopId             = int(data[8]) + 1
        singlePassing.channelId          = int(data[9]) + 1
        singlePassing.status             = data[10]
        singlePassing.internalData       = data[11]

        singlePassing.timeSinceEpoch     = self.CalculateTime(epochRef, timeStampRef, singlePassing.ticks)
        return singlePassing
    #end parsePassing

    def GetNewPassings(self, epochRef = None, timeStampRef = None, minId = None):
        # Cannot make default arguments to be self.*, so making default to be None then defining if still None when called.
        if epochRef == None:        epochRef = self.lastEpochRef
        if timeStampRef == None:    timeStampRef = self.lastTickRef
        if minId == None:           minId = self.startID
        # Getting on with the rest of the function.
        passings = []
        self.conn.flushInput()
        self.WriteSerial('PASSINGGET;' + format(minId, '08x') + '\n')
        sleep(0.1)
        ret = self.ReadSerial().split(';')
        if ret[1] == '00':
            count = int(self.ReadSerial().split(';')[1], 16)
            self.startID = self.startID + count
            for c in range(0, count):
                rcv = self.ReadSerial()
                passings.append(self.ParsePassing(rcv, epochRef, timeStampRef))
        else:
            sleep(0.01)

        self.conn.flushInput()
        return passings

    #end GetPassings

    def ReadOutBufferToFile(self):

        def RRFileLineParser(singlePassing, num):
            passingTime = datetime.fromtimestamp(singlePassing.timeSinceEpoch)
            return str(num) + ";" + singlePassing.transponder + ";" + passingTime.strftime("%Y-%m-%d")+ ";" + passingTime.strftime("%H:%M:%S.%f")[:12] + ";;" + str(singlePassing.detectionCount) + ";" + str(singlePassing.rssi) + ";;1;" + str(singlePassing.channelId) + ";" + str(singlePassing.loopId) + ";" + str(int(singlePassing.loopOnly)) + ";" + str(singlePassing.wakeupCount) + ";" + str(singlePassing.batteryVoltage) + ";" + str(singlePassing.temperature) + ";" + str(singlePassing.internalData) + ";" + "\n\r"      

        passingsAvailable   = True
        passings            = []
        numPassings         = 0
        print "Retrieving passings"
        while passingsAvailable:
            newPassings     = self.GetNewPassings(minId = numPassings)
            passings        += newPassings
            numPassings     += len(newPassings)
            if len(newPassings)==0: passingsAvailable = False

        print str(numPassings) + " available"
        result              = ""
        for i in range(0,numPassings):
            result += RRFileLineParser(passings[i], i+1)
            
        #Opening File an put input in
        cwd = os.getcwd()
        filename_suffix='.txt'
        filename_index=0
        filename_base='passings_'
        filename=cwd+'/'+filename_base+str(filename_index).zfill(2)+filename_suffix
        while (os.path.isfile(filename) ):
                filename_index += 1
                filename=cwd+'/'+filename_base+str(filename_index).zfill(2)+filename_suffix
        #Opening File an put input in
        fd = open(filename,'w')
        fd.write(result)
        fd.close();
        print "Passing file available here: " + filename
    #end ReadOutBufferToFile

##                                                  ##
## TIME FUNCTIONS                                   ##
##                                                  ##
    @property
    def currentTicks(self):
        self.WriteSerial("TIMESTAMPGET\n")
        sleep(0.5)
        if self.ReadSerial().split(';')[1] == '00':
            self.timestamp = int(self.ReadSerial(), 16)
            self.conn.flushInput()
            return self.timestamp
        else:
            print "rrUSB.timeStamp unavailable";
            return 0
        
    @property
    def epochReferenceTime(self):
        self.WriteSerial("EPOCHREFGET\n")
        sleep(0.5)
        if self.ReadSerial().split(';')[1] == '00':
            self.ret            = self.ReadSerial().split(';')
            self.epochRef       = int(self.ret[0],  16)
            self.timeStampRef   = int(self.ret[1],  16)
            self.conn.flushInput()
            return self.epochRef, self.timeStampRef
        else:
            print "rrUSB.epochRef unavailable";
            return 0, 0
        
    def SetEpochRefToNow(self):
        # DESCRIPTION: Sets the Epoch Refrence of system to current time of PC.
        setTime                 = time.time() + 1
        setTimeHex              = format( int(setTime) , '08x')
        self.WriteSerial("EPOCHREFSET;" + setTimeHex + "\n")
        # Wait until next second has elapsed, then set time.
        while time.time() != setTime:
            #while current time is not the time we want to set
            sleep(0.0001)
            #do nothing
        #end while
        self.conn.setDTR(True)      # time is set at rising edge
        print "DTR Line toggled"
        sleep(0.3)
        self.conn.setDTR(False)     # Return DTR to false so system does not reset.
        sleep(0.5)                  # Sleep times need to be 0.25 < s < 0.50 
        self.ret = self.ReadSerial()
        print self.ret
        if self.ret.split(';')[1] == '00':
            self.ret            = self.ReadSerial().split(';')
            self.epochRef       = int(self.ret[0],  16)
            self.timeStampRef   = int(self.ret[1],  16)
            self.conn.flushInput()
            return self.epochRef, self.timeStampRef
        else:
            print "Unable to set Epoch reference";
            self.conn.flushInput()
    
    def AdjustEpochRefBy1Day(self):		#Adjusts Reference Ticks by one Day including all past passings
        self.WriteSerial("EPOCHREFADJ1D\n")
        sleep(0.5)
        if self.ReadSerial().split(';')[1] == '00':
            self.ret            = self.ReadSerial().split(';')
            self.epochRef       = int(self.ret[0],  16)
            self.timeStampRef   = int(self.ret[1],  16)
            self.conn.flushInput()
            return self.epochRef, self.timeStampRef
        else:
            print "@refTime: Adj EPOCH not available"

    def CreateTimeReference(self):		#Sets the reference times
        self.epochRef, self.timeStampRef    = self.epochReferenceTime
        self.ticks                          = self.currentTicks
        if self.epochRef == 0               : self.epochRef, self.timeStampRef = self.SetEpochRefToNow()
        if self.ticks >= 44236800           : self.epochRef, self.timeStampRef = self.AdjustEpochRefBy1Day()
        self.lastEpochRef = self.epochRef
        self.lastTickRef = self.timeStampRef
        return self.epochRef, self.timeStampRef
        
    def CalculateTime(self, epochRef, timeStampRef, passingTicks):
        self.epochPassingTime = epochRef + ((passingTicks - timeStampRef) / 256.0)
        return self.epochPassingTime

##                                                  ##
## DEVICE WARNINGS                                  ##
##                                                  ##

    def CheckForWarnings(self):
        self.__warnings__   =   ''
        epochRef, timeStampRef = self.epochReferenceTime
        if epochRef == 0    : self.__warnings__   += "- Epoch reference not set\n"
        if self.loopId <> 1 : self.__warnings__   += "- Loop ID is not 1. Device will not act as base for LoopBoxes\n"
        if self.useDTR == 0 : self.__warnings__   += "- DTR is not being used. Timing accuracy might be affected\n"
        return self.__warnings__
        
    
    @property
    def warnings(self):
        if self.__warnings__=='': self.CheckForWarnings()
        return self.__warnings__

##                                                  ##
## COMMAND LINE INTERFACE                           ##
##                                                  ##

    ## RUN COMMAND LINE
    def RunCommandLine(self):
        print "###"
        print "### Type serial commands as described in SDK Document. '\\n' not required."
        print "### Type function in rrUSBTimingBox method preceeded by @"
        print "### Type EXIT to close command line"
        print "### Type HELP to list available commands"
        print "### Type DUMP to dump all passings to race|result File"
        print "###"
        print ""

        print "rrUSB <-  ASCII"
        print "rrUSB ->  ASCII;00"
        print "rrUSB ->  "
        print ""

        def printHelp():
            print ""
            print "# PYTHON COMMANDS"
            print "# Consult the code for definition and use of each of commands below. Commands should be preceeded by '@'."
            print "# Example: @GetNewPassings()"
            print " AdjustEpochRefBy1Day\n CalculateTime\n CheckForWarnings\n ConfGet\n ConfSet\n CreateTimeReference\n GetNewPassings\n InfoGet\n NewBeacon\n NewPassing\n ParsePassing\n ReadOutBufferToFile\n ReadSerial\n RunCommandLine\n SetEpochRefToNow\n UpdateBeacons\n WriteSerial\n autoPowerOff\n batteryPercent\n batteryState\n batteryVoltage\n beaconErrors\n beaconWarnings\n beacons\n beepOut\n blinkOnRepeat\n boxType\n channel\n close\n cmdLine\n conn { = serial.Serial() }\n currentTicks\n deviceID\n firmwareVersion\n hardwareVersion\n internalTemp\n lastEpochRef\n lastTickRef\n loopId\n loopPower\n loopStatus\n pushPreWarn\n startID\n supplyVoltage\n systemInfo\n timeStampRef\n timingMode\n useDTR\n warnings"

            print ""
            print "# SERIAL COMMANDS"
            print "# Commands always start with the command name, in uppercase, followed by their arguments, seperated by ';'. All numbers should be written as hex numbers, without any prefixes (like 0x), lowercase letters, and always with leading zeros where required." 
            print " BEACONGET"
            print " CONFGET"
            print " CONFSET"
            print " EPOCHREFADJ1D"
            print " EPOCHREFGET"
            print " EPOCHREFSET"
            print " INFOGET"
            print " PASSINGGET"
            print " TIMESTAMPGET"
            print ""
                
            

        while True:
            print "rrUSB <- ",
            inLine = raw_input()
            if inLine[0] == "@":
                print eval("box." + inLine[1:])
            elif inLine == "HELP":
                printHelp()
            elif inLine == "DUMP":
                self.ReadOutBufferToFile()
            elif inLine == "EXIT":
                break
            else:
                if inLine[-2:]!= '\n': inLine += '\n'
                self.cmdLine(inLine)
    #end RunCommandLine


if __name__ == '__main__':
    print "###"
    print "### race|result USB Timing Box"
    print "### Command Line interface for ASCII Protocol FWv2.4+"
    print "###"
    print "###"
    print "### Serial Port? (Type 'COMx' for Windows, '/dev/ttyUSBx' or similar for Unix)"
    print ""
    sPort = raw_input(">   ")
    print ""
    
    box = rrUSB(sPort)
    box.RunCommandLine()
    box.close()
