#!/usr/bin/env python
import time

# GPIO control
import pigpio

# Import main radio class
from resources.piradio import PiRadio

# Import our modes
from modes.bluetooth import ModeBluetooth
from modes.settings import ModeSettings
from modes.squeezeplayer import ModeSqueezeplayer
from modes.internetradio import ModeRadio
from modes.airplay import ModeAirplay

# Get pigpio up and running
pi = pigpio.pi()

# Create an instance of the PiRadio and confirm which modes we want to run
# NB the order of the modes here is how they will appear on the display
radio = PiRadio(pi, [ModeSqueezeplayer(),
                     ModeRadio(),
                     ModeBluetooth(),
                     ModeAirplay(),
                     ModeSettings()])

# Go!
radio.start()

# Keep the script alive
while True:
    try:
        time.sleep(1)

    # Yes, this is bad practice but let's catch everything that goes wrong
    except:
        try:
            radio.exit()
        except TypeError:
            pass

        raise
