# USB Timing Box SDK

This repository provides documentation and examples for the race|result USB Timing Box. It includes a document describing communication, and implimention of a Python class for connecting with the race|result USB Timing Box.

Developers should require their users to update their USB Timing Boxes through the TagKeyboardReader Tool (https://www.raceresult.com/download/TagReaderKeyboard_2.5.0.zip).

example.py gives a quick example of connecting and processing passings using the ASCII Communication Protocol available with Active Firmware v2.4 and later.

rrUSBTimingBox.py is a Python implimentation of the Communication Protocol document available here: https://www.raceresult.com/v11/en/support/developers.php

rrUSBTimingBox.exe is a Command Line tool for speaking with the USB Timing Box. All functions in rrUSBTimingBox.py are available in this tool.
